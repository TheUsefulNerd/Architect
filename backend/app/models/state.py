"""
LangGraph state definitions for the multi-agent orchestration system.
State is passed between agents and maintains the workflow context.
"""
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langgraph.graph.message import add_messages
from app.models.schemas import Phase


class AgentState(TypedDict):
    """
    Main state object passed between agents in the LangGraph workflow.
    Uses TypedDict for type safety and LangGraph compatibility.
    """
    # Session and tracking
    session_id: str
    current_phase: Phase
    
    # Messages
    messages: Annotated[List[Dict[str, str]], add_messages]
    """Chat history with automatic message accumulation via add_messages"""
    
    # User input
    user_input: str
    """Current user message/query"""
    
    # Phase I: Planner outputs
    requirements: Optional[str]
    architecture: Optional[str]
    tech_stack: Dict[str, List[str]]
    """Tech stack organized as {frontend: [], backend: [], database: [], etc.}"""
    
    # Phase II: Librarian outputs
    identified_technologies: List[str]
    """List of technologies extracted from tech_stack that need documentation"""
    documentation_links: List[Dict[str, Any]]
    """
    Documentation links with structure:
    {
        'tech_name': str,
        'doc_url': str,
        'section': str,
        'relevance_score': float,
        'scraped_content': str (optional)
    }
    """
    
    # Phase III: Mentor outputs
    code_scaffolds: List[Dict[str, Any]]
    """
    Code scaffolds with structure:
    {
        'file_path': str,
        'content': str,
        'hints': List[str],
        'completed': bool
    }
    """
    implementation_hints: List[str]
    """General guidance for the user to implement"""
    
    # Metadata and control
    iteration_count: int
    """Track number of iterations through the workflow"""
    
    error_message: Optional[str]
    """Any error that occurred during processing"""
    
    needs_clarification: bool
    """Flag if agents need more info from user"""
    
    workflow_complete: bool
    """Flag indicating if all phases are done"""
    
    metadata: Dict[str, Any]
    """Additional metadata for context"""


# Helper function to create initial state
def create_initial_state(session_id: str, user_input: str) -> AgentState:
    """Create a fresh AgentState with default values."""
    return {
        "session_id": session_id,
        "current_phase": Phase.PLANNER,
        "messages": [],
        "user_input": user_input,
        "requirements": None,
        "architecture": None,
        "tech_stack": {},
        "identified_technologies": [],
        "documentation_links": [],
        "code_scaffolds": [],
        "implementation_hints": [],
        "iteration_count": 0,
        "error_message": None,
        "needs_clarification": False,
        "workflow_complete": False,
        "metadata": {}
    }


# State transitions helper
class StateTransitions:
    """Helper class for managing state transitions between phases."""
    
    @staticmethod
    def should_move_to_librarian(state: AgentState) -> bool:
        """Check if we should transition from Planner to Librarian."""
        return (
            (state["current_phase"] == Phase.PLANNER or state["current_phase"] == Phase.LIBRARIAN)
            and state.get("tech_stack") is not None
            and len(state.get("tech_stack", {})) > 0
            and not state.get("needs_clarification", False)
        )
    
    @staticmethod
    def should_move_to_mentor(state: AgentState) -> bool:
        """Check if we should transition from Librarian to Mentor."""
        return (
            (state["current_phase"] == Phase.LIBRARIAN or state["current_phase"] == Phase.MENTOR)
            and len(state.get("documentation_links", [])) > 0
            and not state.get("needs_clarification", False)
        )
    
    @staticmethod
    def should_complete_workflow(state: AgentState) -> bool:
        """Check if the workflow is complete."""
        return (
            state["current_phase"] == Phase.MENTOR
            and len(state.get("code_scaffolds", [])) > 0
            and not state.get("needs_clarification", False)
        )
    
    @staticmethod
    def has_error(state: AgentState) -> bool:
        """Check if there's an error in the state."""
        return state.get("error_message") is not None