"""
Librarian Agent - Phase II of the Architect workflow.
Uses Gemini to identify which technologies need documentation,
then builds Google search links for each technology as documentation references.
"""
import json
import logging
import re
from typing import Any

from app.models.state import AgentState
from app.models.schemas import Phase
from app.services.llm_service import llm_service
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

    1. Uses Gemini to identify technologies from the tech stack
    2. Crawls official documentation for each technology
    3. Stores embeddings in Qdrant
    4. Uses Gemini to synthesize a cited response

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

        # Step 2: Build Google search links for all identified technologies
        docs = _build_search_links(identified_techs, context)
        logger.info(f"[Librarian] Built {len(docs)} documentation search links")

        # Step 3: Store docs in Qdrant for semantic search (skipped if vector service disabled)
        await _store_docs_in_vector_db(docs, state["session_id"])

        # Step 4: Synthesize a cited response using Gemini
        synthesis = await _synthesize_documentation(docs, context, identified_techs)

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
    Use Gemini to extract a clean, normalized list of technologies
    from the tech_stack dict.
    """
    stack_text = json.dumps(tech_stack, indent=2)
    prompt = f"""Tech stack from project spec:
{stack_text}

Return a JSON array of all technology names that need documentation lookup."""

    try:
        response = await llm_service.gemini_generate(
            prompt=prompt,
            system_prompt=TECH_IDENTIFIER_PROMPT,
            temperature=0.1,    # low temp for consistent extraction
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
    Use Gemini to synthesize a cited, readable summary from raw scraped docs.
    """
    if not docs:
        return "No documentation was found for the identified technologies."

    # Build numbered citations context — cap at 15 to stay within token limits
    citations_text = ""
    for i, doc in enumerate(docs[:15], 1):
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
        return await llm_service.gemini_chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=LIBRARIAN_SYNTHESIS_PROMPT,
            temperature=0.3,
        )
    except Exception as e:
        logger.error(f"[Librarian] Synthesis error: {e}")
        # Fallback to raw citation formatter
        return '\n'.join(f"[{i+1}] {d.get('tech_name')} — {d.get('doc_url')}" for i, d in enumerate(docs))


def _build_search_links(techs: list[str], context: str = "") -> list[dict]:
    """
    Build Google search links for each identified technology.
    Returns doc-shaped dicts so the rest of the pipeline stays unchanged.
    """
    # Well-known official doc URLs — fall back to Google search for everything else
    KNOWN_DOCS = {
        "fastapi":      "https://fastapi.tiangolo.com/",
        "django":       "https://docs.djangoproject.com/",
        "flask":        "https://flask.palletsprojects.com/",
        "sqlalchemy":   "https://docs.sqlalchemy.org/",
        "sqlite":       "https://www.sqlite.org/docs.html",
        "postgresql":   "https://www.postgresql.org/docs/",
        "mysql":        "https://dev.mysql.com/doc/",
        "mongodb":      "https://www.mongodb.com/docs/",
        "redis":        "https://redis.io/docs/",
        "react":        "https://react.dev/",
        "next.js":      "https://nextjs.org/docs",
        "nextjs":       "https://nextjs.org/docs",
        "vue":          "https://vuejs.org/guide/",
        "tailwind css": "https://tailwindcss.com/docs",
        "tailwindcss":  "https://tailwindcss.com/docs",
        "typescript":   "https://www.typescriptlang.org/docs/",
        "python":       "https://docs.python.org/3/",
        "pydantic":     "https://docs.pydantic.dev/",
        "langchain":    "https://python.langchain.com/docs/",
        "langgraph":    "https://langchain-ai.github.io/langgraph/",
        "qdrant":       "https://qdrant.tech/documentation/",
        "supabase":     "https://supabase.com/docs",
        "docker":       "https://docs.docker.com/",
        "kubernetes":   "https://kubernetes.io/docs/",
        "celery":       "https://docs.celeryq.dev/",
        "alembic":      "https://alembic.sqlalchemy.org/en/latest/",
        "jwt":          "https://jwt.io/introduction",
        "html":         "https://developer.mozilla.org/en-US/docs/Web/HTML",
        "css":          "https://developer.mozilla.org/en-US/docs/Web/CSS",
        "javascript":   "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
    }

    docs = []
    for tech in techs:
        key = tech.lower().strip()
        if key in KNOWN_DOCS:
            doc_url = KNOWN_DOCS[key]
            section_title = f"Official Documentation"
        else:
            # Fall back to a Google search for official docs
            query = f"{tech} official documentation"
            doc_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            section_title = f"Search: {tech} documentation"

        docs.append({
            "tech_name":     tech,
            "doc_url":       doc_url,
            "section_title": section_title,
            "content":       f"Refer to the official {tech} documentation at: {doc_url}",
        })

    return docs


def _build_librarian_response(
    techs: list[str],
    synthesis: str,
    docs: list[dict],
) -> str:
    """Minimal chat message — Documentation Links are in the Docs tab."""
    doc_count = len({doc.get("doc_url") for doc in docs if doc.get("doc_url")})
    return f"📚 Found {doc_count} documentation sources. Check the **Docs tab** to review them."