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

## Your Role
You are a senior engineer who teaches through conversation, not monologues.
You guide the user to implement the project themselves using the roadmap the Planner created.

## How You Communicate
- SHORT responses only — 2 to 5 sentences maximum in chat
- Never dump code in the chat message
- All generated code goes to the Code tab — reference it by file name
- Talk like a senior engineer pair programming: direct, precise, encouraging
- Ask one focused question at the end of each response to keep momentum

## Your Workflow
1. Acknowledge the project briefly
2. Tell the user which file to start with and what the first TODO is
3. Reference the Code tab: "Open `filename` in the Code tab"
4. End with one Socratic question or a clear next action

## When User Asks for Changes
- Acknowledge what they want to change
- Explain briefly WHY the change makes sense (or push back if it doesn't)
- Update the relevant scaffold and tell them which file changed
- Keep it conversational — one response, not an essay

## When User Submits Their Code
- Never rewrite their code completely
- Point out specific issues with line-level precision
- Ask "What do you think happens when X?" before giving the answer
- Only provide corrected code when the user is very close (minor fixes only)

## Tone Examples
Good: "Open `index.html` in the Code tab. Your first TODO is adding the `<h1>` tag inside `<main>`. What tag would you use for a page's primary title?"
Bad: "Here is a complete implementation of your portfolio website with all the features you requested..."

Good: "That centering issue is a classic Flexbox problem. Check line 12 in `style.css` — what value does `height` have on the body?"
Bad: "Here is the corrected CSS with all the fixes applied..."

## Output Format
Return ONLY valid JSON:
{
  "chat_response": "Your short conversational response (2-5 sentences max)",
  "scaffolds": [
    {
      "file_path": "relative/path/to/file",
      "content": "Full scaffold code with TODO comments and hints",
      "hints": ["Hint 1", "Hint 2"]
    }
  ],
  "implementation_hints": ["Short hint 1", "Short hint 2"],
  "first_steps": "One sentence describing where to start"
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

    messages = state.get("messages", [])
    recent_messages = messages[-10:] if len(messages) > 10 else messages

    if not requirements:
        logger.warning("[Mentor] No requirements found in state")
        return {
            "error_message": "No requirements found. Please complete the Planner phase.",
            "current_phase": Phase.MENTOR,
        }

    try:
        # Step 1: Retrieve relevant code patterns from Qdrant
        patterns = await _fetch_relevant_patterns(requirements, tech_stack)

        # Step 2: Build the full prompt
        prompt = _build_mentor_prompt(
            requirements, architecture, tech_stack, docs, patterns, recent_messages
        )

        # Step 3: Generate scaffolds using Gemini
        response_text = await llm_service.gemini_generate(
            prompt=prompt,
            system_prompt=MENTOR_SYSTEM_PROMPT,
            temperature=0.4,    # low-medium: creative but consistent
        )

        parsed = _parse_mentor_response(response_text)
        scaffolds     = parsed.get("scaffolds", [])
        impl_hints    = parsed.get("implementation_hints", [])
        first_steps   = parsed.get("first_steps", "")
        chat_response = parsed.get("chat_response", "")

        # Fallback chat message if model didn't follow format
        if not chat_response:
            file_names = [s.get("file_path", "") for s in scaffolds]
            files_str  = ", ".join(f"`{f}`" for f in file_names) if file_names else "the Code tab"
            chat_response = (
                f"I've generated your scaffolds. Open {files_str} in the Code tab "
                f"and start with the first TODO. {first_steps}"
            )

        return {
            "messages": [
                {"role": "assistant", "content": chat_response}
            ],
            "current_phase":        Phase.MENTOR,
            "code_scaffolds":       scaffolds,
            "implementation_hints": impl_hints,
            "workflow_complete":    True,
            "needs_clarification":  False,
            "metadata": {
                **state.get("metadata", {}),
                "mentor_status":  "complete",
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


def _extract_message_parts(msg: Any) -> tuple[str, str]:
    """
    Safely extract (role, content) from either a plain dict or a
    LangChain message object (HumanMessage, AIMessage, etc.).
    """
    # LangChain message objects have a .content attribute and a class name
    if hasattr(msg, "content"):
        class_name = msg.__class__.__name__.lower()
        if "human" in class_name:
            role = "user"
        elif "ai" in class_name or "assistant" in class_name:
            role = "assistant"
        else:
            role = "user"
        return role, str(msg.content)

    # Plain dict (our standard internal format)
    if isinstance(msg, dict):
        return msg.get("role", ""), msg.get("content", "")

    # Fallback — stringify whatever it is
    return "user", str(msg)


def _build_mentor_prompt(
    requirements: str,
    architecture: str,
    tech_stack: dict,
    docs: list[dict],
    patterns: list[dict],
    conversation_history: list = [],
) -> str:
    """Assemble the full prompt for scaffold generation and follow-up guidance."""

    stack_lines = []
    for category, techs in tech_stack.items():
        if techs:
            stack_lines.append(f"  {category}: {', '.join(techs)}")
    stack_summary = "\n".join(stack_lines)

    doc_context = ""
    for doc in docs[:8]:
        doc_context += f"\n### {doc.get('tech_name')} — {doc.get('section_title')}\n"
        doc_context += doc.get("content", "")[:400] + "\n"

    pattern_context = ""
    for p in patterns:
        pattern_context += f"\n### Pattern: {p.get('pattern_name')}\n"
        pattern_context += f"Use case: {p.get('use_case')}\n"
        pattern_context += f"```\n{p.get('code_snippet', '')[:300]}\n```\n"

    history_context = ""
    if conversation_history:
        history_context = "\n## Recent Conversation\n"
        for msg in conversation_history:
            role, content = _extract_message_parts(msg)
            if role in ("user", "assistant") and content:
                prefix    = "User" if role == "user" else "Mentor"
                truncated = content[:300] + "..." if len(content) > 300 else content
                history_context += f"{prefix}: {truncated}\n"

    is_followup = len(conversation_history) > 2

    instruction = (
        """Based on the conversation history above, continue guiding the user.
Do NOT repeat what you already said. Progress the conversation forward.
If the user submitted code, review it specifically.
If the user said yes/ok/proceed, move to the next TODO item."""
        if is_followup else
        """Generate the project scaffold following your system instructions.
Create scaffolds for the most important files based on the tech stack above.
Prioritize core infrastructure files first (config, models, main entry points)."""
    )

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
{history_context}
---
{instruction}
"""


def _parse_mentor_response(response_text: str) -> dict:
    """Parse mentor response — handles JSON and plain conversational text."""
    cleaned = re.sub(r"```(?:json)?\s*", "", response_text).strip().rstrip("`").strip()

    # Try direct JSON parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to find a JSON block anywhere in the response
    json_matches = list(re.finditer(r"\{[\s\S]*\}", cleaned))
    for match in reversed(json_matches):
        try:
            parsed = json.loads(match.group())
            if "chat_response" in parsed or "scaffolds" in parsed:
                return parsed
        except json.JSONDecodeError:
            continue

    # Fallback — treat entire response as a chat message
    logger.info("[Mentor] Plain text response — treating as chat message")
    return {
        "chat_response":        response_text,
        "scaffolds":            [],
        "implementation_hints": [],
        "first_steps":          "",
    }


def _build_scaffold_details(
    scaffolds: list[dict],
    impl_hints: list[str],
    first_steps: str,
) -> str:
    """Build the full scaffold content for the Code tab (not shown in chat)."""

    file_tree = "📁 **Generated Files**\n"
    for scaffold in scaffolds:
        file_tree += f"  └─ `{scaffold.get('file_path', 'unknown')}`\n"

    hints_section = ""
    if impl_hints:
        hints_section = "\n\n💡 **Implementation Hints**\n"
        for i, hint in enumerate(impl_hints, 1):
            hints_section += f"{i}. {hint}\n"

    steps_section = ""
    if first_steps:
        steps_section = f"\n\n🗺️ **Where to Start**\n{first_steps}"

    scaffold_details = "\n\n---\n## 📄 Files\n\n"
    for scaffold in scaffolds:
        scaffold_details += f"### `{scaffold.get('file_path', 'unknown')}`\n"
        lang = scaffold.get("file_path", "").split(".")[-1] or "text"
        scaffold_details += f"```{lang}\n{scaffold.get('content', '')}\n```\n"
        hints = scaffold.get("hints", [])
        if hints:
            scaffold_details += "**Hints:**\n"
            for hint in hints:
                scaffold_details += f"- 🤔 {hint}\n"
        scaffold_details += "\n"

    return (
        f"{file_tree}{hints_section}{steps_section}{scaffold_details}\n\n"
        "---\n"
        "⚠️ These scaffolds are intentionally incomplete. "
        "The TODO sections are yours to implement. Good luck! 🚀\n"
    )