"""
Planner Agent - Phase I of the Architect workflow.
Uses Gemini to understand user intent and produce a Technical Specification.
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

PLANNER_SYSTEM_PROMPT = """You are the Planner — a senior software architect on the Architect AI platform.

Your job is to understand what the user wants to build, suggest improvements where genuinely useful, and produce a Technical Specification when you have enough context.

## Your Personality
- Direct, friendly, and efficient — like a senior engineer at a startup
- You suggest better approaches when relevant, but always respect the user's final decision
- You never ask a question the user has already answered in this conversation

## How to Handle a Request

### Step 1 — Read the full conversation history first
Before responding, read everything the user has said so far.
Never ask for information the user has already provided.

### Step 2 — Gauge the complexity of the request
Scale the number of questions to the complexity of what's being built.
Simple requests need very few questions. Complex systems need more.
Use your judgment — a senior engineer knows when they have enough to proceed.

### Step 3 — Ask focused questions, not open-ended ones
Instead of "what tech stack do you want?", say:
"Based on what you've described, X seems like the right fit. Does that work for you?"
Suggest a direction and let the user confirm or redirect.
Ask at most 2 questions per turn.

### Step 4 — Know when to stop asking and generate the spec
You do not need perfect information. If you understand:
- What the system needs to do
- How it should be structured
- What technology fits
...then generate the spec. Do not keep asking.

### Step 5 — Respect "proceed" signals immediately
If the user says anything like "just go ahead", "proceed", "that's it", "nothing else", "continue", "just do it" — generate the spec immediately with what you know. Do not ask any more questions.

## Output Format

### When you need more information:
{
  "status": "gathering",
  "response": "Your conversational response. Suggest options, ask at most 2 focused questions."
}

### When you have enough information:
{
  "status": "spec_ready",
  "requirements": "Clear prose describing what the system does and any constraints",
  "architecture": "How the system is structured — components, data flow, deployment approach",
  "tech_stack": {
    "frontend": [],
    "backend": [],
    "database": [],
    "infrastructure": [],
    "ai_ml": []
  },
  "roadmap": [
    {
      "title": "Short action-oriented step title",
      "complexity": "simple|medium|complex"
    }
  ]
}

The roadmap must be:
- Ordered sequentially — each step builds on the previous
- Project-specific — not generic, based on exactly what this project needs
- Action-oriented titles — start with a verb: "Create", "Add", "Implement", "Connect", "Deploy"
- Complexity reflects actual effort: simple (< 30 min), medium (30-90 min), complex (> 90 min)
- Between 3 and 10 steps — no more, no less

Output only valid JSON. No markdown, no explanation outside the JSON.
"""


# ------------------------------------------------------------------
# AGENT NODE
# ------------------------------------------------------------------

async def planner_node(state: AgentState) -> dict[str, Any]:
    """
    LangGraph node for the Planner agent.
    """
    logger.info(f"[Planner] Processing session {state['session_id']}")

    # Build conversation history for Gemini
    gemini_messages = _build_gemini_messages(state["messages"])

    # Add the latest user input
    gemini_messages.append({
        "role": "user",
        "content": state["user_input"]
    })

    try:
        response_text = await llm_service.groq_chat(
            messages=gemini_messages,
            system_prompt=PLANNER_SYSTEM_PROMPT,
            temperature=0.7,
        )

        parsed = _parse_planner_response(response_text)

        # Case 1: Still gathering — ask focused questions
        if parsed.get("status") == "gathering":
            logger.info("[Planner] Still gathering requirements")
            return {
                "messages": [
                    {"role": "user",      "content": state["user_input"]},
                    {"role": "assistant", "content": parsed["response"]},
                ],
                "current_phase":     Phase.PLANNER,
                "needs_clarification": True,
                "metadata": {
                    **state.get("metadata", {}),
                    "planner_status": "gathering"
                },
            }

        # Case 2: Spec ready — move to Librarian
        if parsed.get("status") == "spec_ready":
            logger.info("[Planner] Spec ready — moving to Librarian")
            _build_spec_summary(parsed)

            return {
                "messages": [
                    {"role": "user",      "content": state["user_input"]},
                    {"role": "assistant", "content": "Got it. Researching documentation and generating your scaffolds now…"},
                ],
                "current_phase":       Phase.LIBRARIAN,
                "requirements":        parsed.get("requirements", ""),
                "architecture":        parsed.get("architecture", ""),
                "tech_stack":          parsed.get("tech_stack", {}),
                "roadmap":             parsed.get("roadmap", []),
                "needs_clarification": False,
                "metadata": {
                    **state.get("metadata", {}),
                    "planner_status": "complete",
                    "roadmap":        parsed.get("roadmap", []),
                },
            }

        # Fallback — treat as gathering
        return {
            "messages": [
                {"role": "user",      "content": state["user_input"]},
                {"role": "assistant", "content": response_text},
            ],
            "current_phase":     Phase.PLANNER,
            "needs_clarification": True,
        }

    except Exception as e:
        logger.error(f"[Planner] Error: {e}")
        return {
            "error_message": str(e),
            "messages": [
                {"role": "user",      "content": state["user_input"]},
                {"role": "assistant", "content": "I encountered an error. Please try again."},
            ],
        }


# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------

def _build_gemini_messages(messages: list[dict]) -> list[dict]:
    """Convert stored messages to chat format."""
    result = []
    for msg in messages:
        role = msg["role"]
        # Normalise — both Groq and Gemini need standard roles
        if role == "model":
            role = "assistant"
        result.append({
            "role": role,
            "content": msg["content"]
        })
    return result


def _parse_planner_response(response_text: str) -> dict:
    """Parse Gemini response — handles clean JSON and markdown-wrapped JSON."""
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

    # Not JSON — treat as gathering response
    return {
        "status":   "gathering",
        "response": response_text
    }


def _build_spec_summary(spec: dict) -> str:
    """Build a human-readable summary of the Technical Spec for the user."""
    tech_stack = spec.get("tech_stack", {})
    stack_lines = []
    for category, techs in tech_stack.items():
        if techs:
            stack_lines.append(f"  • {category.title()}: {', '.join(techs)}")
    stack_str = "\n".join(stack_lines) if stack_lines else "  (none specified)"

    roadmap = spec.get("roadmap", [])
    complexity_emoji = {"simple": "🟢", "medium": "🟡", "complex": "🔴"}
    roadmap_lines = []
    for i, step in enumerate(roadmap, 1):
        emoji = complexity_emoji.get(step.get("complexity", "simple"), "🟢")
        roadmap_lines.append(f"  {i}. {emoji} {step.get('title', '')}")
    roadmap_str = "\n".join(roadmap_lines) if roadmap_lines else "  (no roadmap generated)"

    return f"""✅ **Technical Specification Complete!**

I have a clear picture of your project. Here's what I've captured:

**Requirements**
{spec.get('requirements', '')}

**Architecture**
{spec.get('architecture', '')}

**Tech Stack**
{stack_str}

**Implementation Roadmap**
{roadmap_str}

---
Handing off to the **Librarian** now to fetch the relevant documentation for your stack. 📚
"""