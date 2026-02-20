"""
Planner Agent - Phase I of the Architect workflow.
Uses Gemini to ask Socratic questions until it fully understands
the user's intent, then produces a structured Technical Specification.
"""
import json
import logging
import re
from typing import Any

from app.models.state import AgentState
from app.models.schemas import Phase
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# SYSTEM PROMPTS
# ------------------------------------------------------------------

PLANNER_SYSTEM_PROMPT = """You are the Planner — the first agent in the Architect AI platform.

Your role is to act as a senior software architect conducting a Socratic interview.
You guide users from a vague idea to a precise Technical Specification.

## Your Personality
- Thoughtful, methodical, and precise
- You never assume — you always ask
- You think in terms of systems, not just features
- You push back gently when requirements are vague

## Your Workflow
You will conduct a back-and-forth interview with the user.
Keep asking clarifying questions until you are FULLY CONFIDENT about:
  1. What the system must DO (functional requirements)
  2. How it must PERFORM (non-functional requirements)
  3. What it will be BUILT WITH (tech stack)
  4. How the pieces FIT TOGETHER (architecture)

## Rules
- Ask a MAXIMUM of 3 focused questions per turn (not a wall of questions)
- Questions must be specific and reveal architectural decisions
- Do NOT generate the spec until you are confident
- When ready to generate, output ONLY valid JSON (see format below)

## Spec Output Format (JSON only, no markdown)
When you have enough information, output this exact structure:
{
  "status": "spec_ready",
  "requirements": "Detailed functional and non-functional requirements as prose",
  "architecture": "System architecture description including components, data flow, and interactions",
  "tech_stack": {
    "frontend": ["technology1", "technology2"],
    "backend": ["technology1", "technology2"],
    "database": ["technology1", "technology2"],
    "infrastructure": ["technology1", "technology2"],
    "ai_ml": ["technology1", "technology2"]
  }
}

## If still gathering information
Output this structure:
{
  "status": "gathering",
  "response": "Your question(s) to the user as natural conversational text"
}
"""

SPEC_EXTRACTION_PROMPT = """Based on this entire conversation, generate the final Technical Specification.
Output ONLY valid JSON in this exact format, nothing else:
{
  "status": "spec_ready",
  "requirements": "...",
  "architecture": "...",
  "tech_stack": {
    "frontend": [],
    "backend": [],
    "database": [],
    "infrastructure": [],
    "ai_ml": []
  }
}"""


# ------------------------------------------------------------------
# AGENT NODE
# ------------------------------------------------------------------

async def planner_node(state: AgentState) -> dict[str, Any]:
    """
    LangGraph node for the Planner agent.

    Reads the current state, sends messages to Gemini,
    and returns state updates.

    Returns:
        Partial state dict with updated fields
    """
    logger.info(f"[Planner] Processing session {state['session_id']}")

    # Convert state messages to Gemini format
    gemini_messages = _build_gemini_messages(state["messages"])

    # Add the latest user message
    gemini_messages.append({
        "role": "user",
        "content": state["user_input"]
    })

    try:
        response_text = await llm_service.gemini_chat(
            messages=gemini_messages,
            system_prompt=PLANNER_SYSTEM_PROMPT,
            temperature=0.7,
        )

        parsed = _parse_planner_response(response_text)

        # Case 1: Still asking questions
        if parsed.get("status") == "gathering":
            logger.info("[Planner] Still gathering requirements")
            return {
                "messages": [
                    {"role": "user", "content": state["user_input"]},
                    {"role": "assistant", "content": parsed["response"]},
                ],
                "current_phase": Phase.PLANNER,
                "needs_clarification": True,
                "metadata": {**state.get("metadata", {}), "planner_status": "gathering"},
            }

        # Case 2: Spec is ready
        if parsed.get("status") == "spec_ready":
            logger.info("[Planner] Technical spec ready — moving to Librarian")
            tech_stack = parsed.get("tech_stack", {})

            # Build a human-readable confirmation message
            confirmation = _build_spec_summary(parsed)

            return {
                "messages": [
                    {"role": "user", "content": state["user_input"]},
                    {"role": "assistant", "content": confirmation},
                ],
                "current_phase": Phase.LIBRARIAN,
                "requirements": parsed.get("requirements", ""),
                "architecture": parsed.get("architecture", ""),
                "tech_stack": tech_stack,
                "needs_clarification": False,
                "metadata": {**state.get("metadata", {}), "planner_status": "complete"},
            }

        # Fallback: treat any other response as still gathering
        return {
            "messages": [
                {"role": "user", "content": state["user_input"]},
                {"role": "assistant", "content": response_text},
            ],
            "current_phase": Phase.PLANNER,
            "needs_clarification": True,
        }

    except Exception as e:
        logger.error(f"[Planner] Error: {e}")
        return {
            "error_message": str(e),
            "messages": [
                {"role": "user", "content": state["user_input"]},
                {"role": "assistant", "content": "I encountered an error. Please try again."},
            ],
        }


# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------

def _build_gemini_messages(messages: list[dict]) -> list[dict]:
    """
    Convert stored messages into Gemini-compatible format.
    Gemini uses 'user' / 'model' roles (not 'assistant').
    """
    gemini_messages = []
    for msg in messages:
        role = "model" if msg["role"] == "assistant" else "user"
        gemini_messages.append({
            "role": role,
            "content": msg["content"]
        })
    return gemini_messages


def _parse_planner_response(response_text: str) -> dict:
    """
    Parse Gemini's response into a structured dict.
    Handles both clean JSON and JSON embedded in markdown.
    """
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?\s*", "", response_text).strip().rstrip("`").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to extract JSON block from within the text
        json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

    # Not JSON at all — treat as a gathering response
    return {
        "status": "gathering",
        "response": response_text
    }


def _build_spec_summary(spec: dict) -> str:
    """
    Build a human-readable summary of the generated Technical Spec.
    Shown to the user after the Planner is done.
    """
    tech_stack = spec.get("tech_stack", {})
    stack_lines = []
    for category, techs in tech_stack.items():
        if techs:
            stack_lines.append(f"  • {category.title()}: {', '.join(techs)}")

    stack_str = "\n".join(stack_lines) if stack_lines else "  (none specified)"

    return f"""✅ **Technical Specification Complete!**

I now have a clear picture of your project. Here's what I've captured:

**Requirements**
{spec.get('requirements', '')}

**Architecture**
{spec.get('architecture', '')}

**Tech Stack**
{stack_str}

---
I'm now handing this off to the **Librarian** to fetch the relevant documentation for your stack. Hang tight! 📚
"""
