"""
Librarian Agent - Phase II of the Architect workflow.
Uses Groq (for speed) to identify which technologies need documentation,
then crawls official docs and returns full scraped content with citations.
"""
import json
import logging
import re
from typing import Any

from app.models.state import AgentState
from app.models.schemas import Phase
from app.services.llm_service import llm_service
from app.services.crawler_service import crawler_service
from app.services.vector_service import vector_service

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# SYSTEM PROMPTS
# ------------------------------------------------------------------

TECH_IDENTIFIER_PROMPT = """You are a technology analyst. Given a project's tech stack,
identify the most important technologies that need documentation lookup.

Return ONLY a JSON array of technology names — no other text, no markdown.
Normalize names: use "FastAPI" not "fast api", "LangGraph" not "langgraph", etc.

Example output:
["FastAPI", "LangGraph", "Supabase", "Qdrant", "Next.js", "Tailwind CSS"]
"""

LIBRARIAN_SYNTHESIS_PROMPT = """You are the Librarian — an expert at synthesizing technical documentation.

You have been given scraped documentation for a project's tech stack.
Your job is to:
1. Present the most relevant documentation sections for this specific project
2. Format it like a Perplexity-style response: clear summaries with inline [n] citations
3. Highlight the most important concepts, APIs, and patterns the developer will need
4. Point out any integration concerns between technologies

Keep your response focused and practical — not a wall of raw text.
Every claim must have a citation from the provided documentation."""


# ------------------------------------------------------------------
# AGENT NODE
# ------------------------------------------------------------------

async def librarian_node(state: AgentState) -> dict[str, Any]:
    """
    LangGraph node for the Librarian agent.

    1. Uses Groq to identify technologies from the tech stack
    2. Crawls official documentation for each technology
    3. Stores embeddings in Qdrant
    4. Uses Groq to synthesize a cited response

    Returns:
        Partial state dict with updated fields
    """
    logger.info(f"[Librarian] Processing session {state['session_id']}")

    tech_stack = state.get("tech_stack", {})
    requirements = state.get("requirements", "")
    architecture = state.get("architecture", "")
    context = f"{requirements}\n{architecture}"

    if not tech_stack:
        logger.warning("[Librarian] No tech stack found in state")
        return {
            "error_message": "No tech stack available. Please complete the Planner phase first.",
            "current_phase": Phase.LIBRARIAN,
        }

    try:
        # Step 1: Identify technologies to look up
        identified_techs = await _identify_technologies(tech_stack)
        logger.info(f"[Librarian] Technologies identified: {identified_techs}")

        # Step 2: Crawl documentation for all technologies concurrently
        docs = await crawler_service.fetch_docs_for_tech_stack(tech_stack, context)
        logger.info(f"[Librarian] Fetched {len(docs)} documentation sections")

        # Step 3: Store docs in Qdrant for semantic search
        await _store_docs_in_vector_db(docs, state["session_id"])

        # Step 4: Synthesize a cited response using Groq
        synthesis = await _synthesize_documentation(docs, context, identified_techs)

        # Build the full assistant message
        response_message = _build_librarian_response(identified_techs, synthesis, docs)

        return {
            "messages": [
                {"role": "assistant", "content": response_message}
            ],
            "current_phase": Phase.MENTOR,
            "identified_technologies": identified_techs,
            "documentation_links": docs,
            "needs_clarification": False,
            "metadata": {
                **state.get("metadata", {}),
                "librarian_status": "complete",
                "docs_count": len(docs),
            },
        }

    except Exception as e:
        logger.error(f"[Librarian] Error: {e}")
        return {
            "error_message": str(e),
            "current_phase": Phase.LIBRARIAN,
            "messages": [
                {"role": "assistant", "content": f"Documentation fetch encountered an error: {e}"}
            ],
        }


# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------

async def _identify_technologies(tech_stack: dict) -> list[str]:
    """
    Use Groq to extract a clean, normalized list of technologies
    from the tech_stack dict.
    """
    stack_text = json.dumps(tech_stack, indent=2)
    prompt = f"""Tech stack from project spec:
{stack_text}

Return a JSON array of all technology names that need documentation lookup."""

    try:
        response = await llm_service.groq_generate(
            prompt=prompt,
            system_prompt=TECH_IDENTIFIER_PROMPT,
            temperature=0.1,        # low temp for consistent extraction
        )

        cleaned = re.sub(r"```(?:json)?\s*", "", response).strip().rstrip("`").strip()
        techs = json.loads(cleaned)
        return techs if isinstance(techs, list) else list(tech_stack.values())

    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"[Librarian] Tech identification parse error: {e}, falling back")
        # Fallback: flatten the tech_stack dict manually
        fallback = []
        for techs in tech_stack.values():
            if isinstance(techs, list):
                fallback.extend(techs)
        return fallback


async def _store_docs_in_vector_db(docs: list[dict], session_id: str):
    """
    Store fetched documentation in Qdrant for future semantic search.
    Fails silently so it doesn't block the main flow.
    """
    for i, doc in enumerate(docs):
        try:
            await vector_service.store_documentation(
                tech_name=doc.get("tech_name", "Unknown"),
                doc_url=doc.get("doc_url", ""),
                section_title=doc.get("section_title", ""),
                content=doc.get("content", ""),
                chunk_index=i,
            )
        except Exception as e:
            logger.warning(f"[Librarian] Failed to store doc in vector DB: {e}")


async def _synthesize_documentation(
    docs: list[dict],
    context: str,
    techs: list[str],
) -> str:
    """
    Use Groq to synthesize a cited, readable summary from raw scraped docs.
    """
    if not docs:
        return "No documentation was found for the identified technologies."

    # Build numbered citations context for Groq
    citations_text = ""
    for i, doc in enumerate(docs[:15], 1):     # cap at 15 to stay within token limits
        citations_text += f"\n[{i}] {doc.get('tech_name')} — {doc.get('section_title')}\n"
        citations_text += f"URL: {doc.get('doc_url')}\n"
        citations_text += doc.get("content", "")[:600] + "\n"
        citations_text += "---\n"

    prompt = f"""Project Context:
{context}

Technologies: {', '.join(techs)}

Documentation Sources:
{citations_text}

Please synthesize this documentation into a clear, practical guide for building this project.
Reference sources inline using [n] citation numbers."""

    try:
        return await llm_service.groq_chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=LIBRARIAN_SYNTHESIS_PROMPT,
            temperature=0.3,
        )
    except Exception as e:
        logger.error(f"[Librarian] Synthesis error: {e}")
        # Fallback to raw citation formatter
        return crawler_service.format_citations(docs)


def _build_librarian_response(
    techs: list[str],
    synthesis: str,
    docs: list[dict],
) -> str:
    """Build the final response message for the user."""

    # Build sources list
    sources_section = "\n\n---\n### 📎 Sources\n"
    seen_urls: set[str] = set()
    source_index = 1

    for doc in docs:
        url = doc.get("doc_url", "")
        if url and url not in seen_urls:
            sources_section += f"[{source_index}] **{doc.get('tech_name')}** — {doc.get('section_title', 'Documentation')}\n"
            sources_section += f"  🔗 {url}\n"
            seen_urls.add(url)
            source_index += 1

    return f"""📚 **Documentation Research Complete**

I've found and analyzed documentation for: **{', '.join(techs)}**

{synthesis}
{sources_section}

---
✅ Handing off to the **Mentor** to generate your project scaffolding and implementation hints!
"""
