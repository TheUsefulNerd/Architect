"""
Pydantic models for API request/response validation and data structures.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, UUID4
from enum import Enum


# Enums
class ProjectStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Phase(str, Enum):
    PLANNER = "planner"
    LIBRARIAN = "librarian"
    MENTOR = "mentor"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class LLMProvider(str, Enum):
    GEMINI = "gemini"
    GROQ = "groq"


# Request Models
class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class SessionCreateRequest(BaseModel):
    project_id: UUID4


class MessageCreateRequest(BaseModel):
    session_id: UUID4
    content: str = Field(..., min_length=1)
    role: MessageRole = MessageRole.USER


class ChatRequest(BaseModel):
    """Main chat request for the orchestration system."""
    session_id: UUID4
    message: str = Field(..., min_length=1)
    phase: Optional[Phase] = None  # Auto-detected if not provided


# Response Models
class UserResponse(BaseModel):
    id: UUID4
    email: str
    created_at: datetime
    updated_at: datetime


class ProjectResponse(BaseModel):
    id: UUID4
    user_id: UUID4
    name: str
    description: Optional[str]
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime


class SessionResponse(BaseModel):
    id: UUID4
    project_id: UUID4
    current_phase: Phase
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    id: UUID4
    session_id: UUID4
    role: MessageRole
    content: str
    phase: Optional[Phase]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class TechnicalSpecResponse(BaseModel):
    id: UUID4
    session_id: UUID4
    requirements: Optional[str]
    architecture: Optional[str]
    tech_stack: Dict[str, List[str]] = Field(default_factory=dict)
    version: int
    created_at: datetime


class DocumentationLinkResponse(BaseModel):
    id: UUID4
    session_id: UUID4
    tech_name: str
    doc_url: str
    scraped_content: Optional[str]
    relevance_score: Optional[float]
    created_at: datetime


class CodeScaffoldResponse(BaseModel):
    id: UUID4
    session_id: UUID4
    file_path: str
    content: str
    hints: List[str] = Field(default_factory=list)
    completed: bool
    created_at: datetime


# Agent-specific models
class PlannerOutput(BaseModel):
    """Output from the Planner agent (Phase I)."""
    requirements: str
    architecture: str
    tech_stack: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Technology stack grouped by category"
    )
    success: bool = True
    error_message: Optional[str] = None


class LibrarianOutput(BaseModel):
    """Output from the Librarian agent (Phase II)."""
    documentation_links: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of relevant documentation with citations"
    )
    tech_identified: List[str] = Field(
        default_factory=list,
        description="Technologies identified from the tech stack"
    )
    success: bool = True
    error_message: Optional[str] = None


class MentorOutput(BaseModel):
    """Output from the Mentor agent (Phase III)."""
    scaffolds: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Code scaffolds with hints"
    )
    implementation_hints: List[str] = Field(
        default_factory=list,
        description="General implementation guidance"
    )
    success: bool = True
    error_message: Optional[str] = None


# Streaming response models
class StreamChunk(BaseModel):
    """Single chunk in a streaming response."""
    type: str = Field(..., description="Type of chunk: text, phase_change, metadata, error")
    content: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatResponse(BaseModel):
    """Complete response from the chat orchestration."""
    session_id: UUID4
    message_id: UUID4
    response: str
    phase: Phase
    metadata: Dict[str, Any] = Field(default_factory=dict)
    planner_output: Optional[PlannerOutput] = None
    librarian_output: Optional[LibrarianOutput] = None
    mentor_output: Optional[MentorOutput] = None
