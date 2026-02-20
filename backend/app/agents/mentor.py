"""
Mentor Agent - Phase III of the Architect workflow.
Uses Gemini to generate code scaffolds with intentional gaps
and Socratic hints — forcing the user to implement, not just copy.
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

MENTOR_SYSTEM_PROMPT = """You are the Mentor — the final agent in the Architect AI platform.

## Your Philosophy
You are a senior engineer who TEACHES, not just codes.
Your scaffolds are intentionally INCOMPLETE.
You leave gaps with TODO comments and provide HINTS that guide — not give — the answer.

## Your Responsibilities
Given a Technical Spec and documentation context:
1. Generate a logical FILE STRUCTURE for the project
2. For each file, provide scaffold code with:
   - Complete imports and class/function signatures
   - Docstrings explaining WHAT each function must do
   - TODO comments with hints (not solutions!) for the implementation
   - A few working examples to set the pattern
3. Provide implementation hints: what to tackle first, common pitfalls, useful docs sections

## Scaffold Quality Rules
- NEVER write complete implementations — leave the logic as TODO
- Write clear, descriptive docstrings so the developer understands the contract
- Add type hints to ALL functions
- Show one complete example function per file, then leave the rest as TODO
- Hints must be questions or nudges, not answers: "Have you considered how X handles Y?"

## Output Format
Return ONLY valid JSON in this exact format:
{
  "scaffolds": [
    {
      "file_path": "relative/path/to/file.py",
      "content": "# Full scaffold code as a string",
      "hints": ["Hint 1", "Hint 2", "Hint 3"]
    }
  ],
  "implementation_hints": [
    "Start with the database models before the API routes",
    "Hint about common pitfall",
    "Hint about testing approach"
  ],
  "first_steps": "Prose description of recommended implementation order"
}
"""


# ------------------------------------------------------------------
# AGENT NODE
# ------------------------------------------------------------------

async def mentor_node(state: AgentState) -> dict[str, Any]:
    """
    LangGraph node for the Mentor agent.

    1. Searches Qdrant for relevant code patterns
    2. Uses Gemini to generate scaffolds based on the tech spec + docs
    3. Returns file scaffolds with hints

    Returns:
        Partial state dict with updated fields
    """
    logger.info(f"[Mentor] Processing session {state['session_id']}")

    requirements = state.get("requirements", "")
    architecture = state.get("architecture", "")
    tech_stack = state.get("tech_stack", {})
    docs = state.get("documentation_links", [])

    if not requirements:
        logger.warning("[Mentor] No requirements found in state")
        return {
            "error_message": "No requirements found. Please complete the Planner phase.",
            "current_phase": Phase.MENTOR,
        }

    try:
        # Step 1: Retrieve relevant code patterns from Qdrant
        patterns = await _fetch_relevant_patterns(requirements, tech_stack)

        # Step 2: Build the prompt with spec + docs + patterns
        prompt = _build_mentor_prompt(requirements, architecture, tech_stack, docs, patterns)

        # Step 3: Generate scaffolds using Gemini
        response_text = await llm_service.gemini_generate(
            prompt=prompt,
            system_prompt=MENTOR_SYSTEM_PROMPT,
            temperature=0.4,        # low-medium: creative but consistent
        )

        parsed = _parse_mentor_response(response_text)
        scaffolds = parsed.get("scaffolds", [])
        impl_hints = parsed.get("implementation_hints", [])
        first_steps = parsed.get("first_steps", "")

        response_message = _build_mentor_response(scaffolds, impl_hints, first_steps)

        return {
            "messages": [
                {"role": "assistant", "content": response_message}
            ],
            "current_phase": Phase.MENTOR,
            "code_scaffolds": scaffolds,
            "implementation_hints": impl_hints,
            "workflow_complete": True,
            "needs_clarification": False,
            "metadata": {
                **state.get("metadata", {}),
                "mentor_status": "complete",
                "scaffold_count": len(scaffolds),
            },
        }

    except Exception as e:
        logger.error(f"[Mentor] Error: {e}")
        return {
            "error_message": str(e),
            "current_phase": Phase.MENTOR,
            "messages": [
                {"role": "assistant", "content": f"Scaffold generation encountered an error: {e}"}
            ],
        }


# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------

async def _fetch_relevant_patterns(requirements: str, tech_stack: dict) -> list[dict]:
    """
    Query Qdrant for code patterns relevant to the project's tech stack.
    Fails silently so it doesn't block scaffold generation.
    """
    try:
        query = f"{requirements} {' '.join(str(v) for v in tech_stack.values())}"
        return await vector_service.search_code_patterns(query, top_k=3)
    except Exception as e:
        logger.warning(f"[Mentor] Pattern search failed: {e}")
        return []


def _build_mentor_prompt(
    requirements: str,
    architecture: str,
    tech_stack: dict,
    docs: list[dict],
    patterns: list[dict],
) -> str:
    """Assemble the full Gemini prompt for scaffold generation."""

    # Summarize tech stack
    stack_lines = []
    for category, techs in tech_stack.items():
        if techs:
            stack_lines.append(f"  {category}: {', '.join(techs)}")
    stack_summary = "\n".join(stack_lines)

    # Include top doc summaries (cap to avoid token overflow)
    doc_context = ""
    for doc in docs[:8]:
        doc_context += f"\n### {doc.get('tech_name')} — {doc.get('section_title')}\n"
        doc_context += doc.get("content", "")[:400] + "\n"

    # Include relevant code patterns
    pattern_context = ""
    for p in patterns:
        pattern_context += f"\n### Pattern: {p.get('pattern_name')}\n"
        pattern_context += f"Use case: {p.get('use_case')}\n"
        pattern_context += f"```\n{p.get('code_snippet', '')[:300]}\n```\n"

    return f"""## Project Requirements
{requirements}

## Architecture
{architecture}

## Tech Stack
{stack_summary}

## Relevant Documentation
{doc_context if doc_context else "No documentation context available."}

## Code Patterns to Consider
{pattern_context if pattern_context else "No patterns available."}

---
Generate the project scaffold following your system instructions.
Create scaffolds for the most important files based on the tech stack above.
Prioritize core infrastructure files first (config, models, main entry points).
"""


def _parse_mentor_response(response_text: str) -> dict:
    """
    Parse Gemini's scaffold response into a structured dict.
    Handles clean JSON and JSON embedded in markdown code fences.
    """
    cleaned = re.sub(r"```(?:json)?\s*", "", response_text).strip().rstrip("`").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

    logger.warning("[Mentor] Could not parse JSON response, returning raw text")
    return {
        "scaffolds": [],
        "implementation_hints": [],
        "first_steps": response_text,
    }


def _build_mentor_response(
    scaffolds: list[dict],
    impl_hints: list[str],
    first_steps: str,
) -> str:
    """Build the final mentor response message shown to the user."""

    # File tree overview
    file_tree = "📁 **Generated Scaffolds**\n"
    for scaffold in scaffolds:
        file_tree += f"  └─ `{scaffold.get('file_path', 'unknown')}`\n"

    # Hints section
    hints_section = ""
    if impl_hints:
        hints_section = "\n\n💡 **Implementation Hints**\n"
        for i, hint in enumerate(impl_hints, 1):
            hints_section += f"{i}. {hint}\n"

    # First steps
    steps_section = ""
    if first_steps:
        steps_section = f"\n\n🗺️ **Recommended Starting Point**\n{first_steps}"

    # Scaffold details
    scaffold_details = "\n\n---\n## 📄 Scaffolds\n\n"
    for scaffold in scaffolds:
        scaffold_details += f"### `{scaffold.get('file_path', 'unknown')}`\n"
        scaffold_details += f"```python\n{scaffold.get('content', '')}\n```\n"

        hints = scaffold.get("hints", [])
        if hints:
            scaffold_details += "**Hints for this file:**\n"
            for hint in hints:
                scaffold_details += f"- 🤔 {hint}\n"
        scaffold_details += "\n"

    return f"""🎓 **Mentor Scaffolding Complete!**

{file_tree}
{hints_section}
{steps_section}
{scaffold_details}

---
⚠️ **Remember**: These scaffolds are intentionally incomplete.
The TODO sections are *yours* to implement. Use the hints above and the documentation from the Librarian phase.
The learning happens in the gaps. Good luck! 🚀
"""
