"""
LangGraph Orchestration Graph - Wires all three agents together.
Manages state transitions: Planner → Librarian → Mentor.
"""
import logging
from typing import Literal

from langgraph.graph import StateGraph, END

from app.models.state import AgentState, create_initial_state, StateTransitions
from app.models.schemas import Phase
from app.agents.planner import planner_node
from app.agents.librarian import librarian_node
from app.agents.mentor import mentor_node

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# ROUTING FUNCTIONS
# ------------------------------------------------------------------

def route_after_planner(state: AgentState) -> Literal["planner", "librarian", "__end__"]:
    """
    Decide what happens after the Planner node runs.

    - Still gathering info?  → Loop back to planner
    - Spec is ready?         → Move to librarian
    - Error?                 → End
    """
    if state.get("error_message"):
        logger.warning(f"[Graph] Planner error, ending: {state['error_message']}")
        return END

    if StateTransitions.should_move_to_librarian(state):
        logger.info("[Graph] Planner complete → Librarian")
        return "librarian"

    logger.info("[Graph] Planner still gathering → waiting for user")
    return END          # Return to user for more input; next message re-enters the graph


def route_after_librarian(state: AgentState) -> Literal["mentor", "__end__"]:
    """
    Decide what happens after the Librarian node runs.

    - Docs ready?  → Move to mentor
    - Error?       → End
    """
    if state.get("error_message"):
        logger.warning(f"[Graph] Librarian error, ending: {state['error_message']}")
        return END

    if StateTransitions.should_move_to_mentor(state):
        logger.info("[Graph] Librarian complete → Mentor")
        return "mentor"

    logger.info("[Graph] Librarian done, no docs found — ending")
    return END


def route_after_mentor(state: AgentState) -> Literal["__end__"]:
    """Mentor is always the final phase — always ends."""
    logger.info("[Graph] Mentor complete → workflow done")
    return END


# ------------------------------------------------------------------
# GRAPH CONSTRUCTION
# ------------------------------------------------------------------

def build_graph() -> StateGraph:
    """
    Build and compile the LangGraph state machine.

    Graph structure:
        [START]
           ↓
        planner ──(still gathering)──→ [END / await user input]
           ↓ (spec ready)
        librarian
           ↓
        mentor
           ↓
        [END]
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("planner", planner_node)
    graph.add_node("librarian", librarian_node)
    graph.add_node("mentor", mentor_node)

    # Set entry point
    graph.set_entry_point("planner")

    # Add conditional edges
    graph.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "planner": "planner",
            "librarian": "librarian",
            END: END,
        }
    )

    graph.add_conditional_edges(
        "librarian",
        route_after_librarian,
        {
            "mentor": "mentor",
            END: END,
        }
    )

    graph.add_conditional_edges(
        "mentor",
        route_after_mentor,
        {END: END}
    )

    return graph.compile()


# ------------------------------------------------------------------
# GRAPH RUNNER
# ------------------------------------------------------------------

# Compile the graph once at module load (shared across requests)
architect_graph = build_graph()


async def run_graph(session_id: str, user_input: str, existing_state: dict = None) -> AgentState:
    """
    Run the Architect graph for a given session and user message.

    Args:
        session_id:     The session identifier
        user_input:     The user's latest message
        existing_state: Previously persisted state (for multi-turn conversations)

    Returns:
        The final AgentState after graph execution
    """
    # Build state: restore from DB if continuing, or create fresh
    if existing_state:
        # Merge existing state with new user input, ensuring all required fields exist
        state = {
            "session_id": session_id,
            "current_phase": existing_state.get("current_phase", Phase.PLANNER),
            "messages": existing_state.get("messages", []),
            "user_input": user_input,
            "requirements": existing_state.get("requirements"),
            "architecture": existing_state.get("architecture"),
            "tech_stack": existing_state.get("tech_stack", {}),
            "identified_technologies": existing_state.get("identified_technologies", []),
            "documentation_links": existing_state.get("documentation_links", []),
            "code_scaffolds": existing_state.get("code_scaffolds", []),
            "implementation_hints": existing_state.get("implementation_hints", []),
            "iteration_count": existing_state.get("iteration_count", 0),
            "error_message": None,
            "needs_clarification": existing_state.get("needs_clarification", False),
            "workflow_complete": existing_state.get("workflow_complete", False),
            "metadata": existing_state.get("metadata", {})
        }
    else:
        state = create_initial_state(session_id, user_input)

    logger.info(f"[Graph] Running — session={session_id}, phase={state.get('current_phase')}")

    try:
        final_state = await architect_graph.ainvoke(state)
        logger.info(f"[Graph] Completed — phase={final_state.get('current_phase')}")
        return final_state

    except Exception as e:
        logger.error(f"[Graph] Execution error: {e}")
        raise


async def run_graph_stream(
    session_id: str,
    user_input: str,
    existing_state: dict = None,
):
    """
    Stream the Architect graph execution, yielding state after each node.

    Args:
        session_id:     The session identifier
        user_input:     The user's latest message
        existing_state: Previously persisted state

    Yields:
        Partial state updates after each node completes
    """
    if existing_state:
        state = {**existing_state, "user_input": user_input}
    else:
        state = create_initial_state(session_id, user_input)

    logger.info(f"[Graph] Streaming — session={session_id}")

    try:
        async for chunk in architect_graph.astream(state):
            # chunk is {node_name: partial_state}
            for node_name, partial_state in chunk.items():
                logger.info(f"[Graph] Node completed: {node_name}")
                yield {
                    "node": node_name,
                    "state": partial_state,
                }
    except Exception as e:
        logger.error(f"[Graph] Stream error: {e}")
        raise