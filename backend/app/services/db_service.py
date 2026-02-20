"""
Database Service - Supabase (PostgreSQL) CRUD operations.
Handles all structured data: projects, sessions, messages, specs, docs, scaffolds.
"""
import logging
from typing import Optional
from uuid import UUID

from supabase import create_client, Client

from app.config import settings

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Supabase service for all relational data operations.
    Uses the service_role key to bypass RLS for backend operations.
    """

    def __init__(self):
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key     # service key bypasses RLS
        )
        logger.info("✅ Database Service initialized (Supabase)")

    # ------------------------------------------------------------------
    # PROJECTS
    # ------------------------------------------------------------------

    async def create_project(self, name: str, description: Optional[str] = None) -> dict:
        """Create a new project."""
        try:
            response = self.client.table("projects").insert({
                "name": name,
                "description": description,
                "status": "in_progress"
            }).execute()
            return response.data[0]
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            raise

    async def get_project(self, project_id: str) -> Optional[dict]:
        """Fetch a project by ID."""
        try:
            response = self.client.table("projects")\
                .select("*")\
                .eq("id", project_id)\
                .single()\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching project {project_id}: {e}")
            return None

    # ------------------------------------------------------------------
    # SESSIONS
    # ------------------------------------------------------------------

    async def create_session(self, project_id: str) -> dict:
        """Create a new session for a project."""
        try:
            response = self.client.table("sessions").insert({
                "project_id": project_id,
                "current_phase": "planner",
                "metadata": {}
            }).execute()
            return response.data[0]
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Fetch a session by ID."""
        try:
            response = self.client.table("sessions")\
                .select("*")\
                .eq("id", session_id)\
                .single()\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching session {session_id}: {e}")
            return None

    async def update_session_phase(self, session_id: str, phase: str) -> dict:
        """Update the current phase of a session."""
        try:
            response = self.client.table("sessions")\
                .update({"current_phase": phase})\
                .eq("id", session_id)\
                .execute()
            return response.data[0]
        except Exception as e:
            logger.error(f"Error updating session phase: {e}")
            raise

    async def update_session_metadata(self, session_id: str, metadata: dict) -> dict:
        """Update session metadata (e.g., tech stack, state flags)."""
        try:
            response = self.client.table("sessions")\
                .update({"metadata": metadata})\
                .eq("id", session_id)\
                .execute()
            return response.data[0]
        except Exception as e:
            logger.error(f"Error updating session metadata: {e}")
            raise

    # ------------------------------------------------------------------
    # MESSAGES
    # ------------------------------------------------------------------

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        phase: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        """Save a chat message to the database."""
        try:
            response = self.client.table("messages").insert({
                "session_id": session_id,
                "role": role,
                "content": content,
                "phase": phase,
                "metadata": metadata or {}
            }).execute()
            return response.data[0]
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            raise

    async def get_messages(self, session_id: str) -> list[dict]:
        """Fetch all messages for a session, ordered by created_at."""
        try:
            response = self.client.table("messages")\
                .select("*")\
                .eq("session_id", session_id)\
                .order("created_at")\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching messages for session {session_id}: {e}")
            return []

    # ------------------------------------------------------------------
    # TECHNICAL SPECS
    # ------------------------------------------------------------------

    async def save_technical_spec(
        self,
        session_id: str,
        requirements: str,
        architecture: str,
        tech_stack: dict
    ) -> dict:
        """Save the Planner agent's output as a technical spec."""
        try:
            response = self.client.table("technical_specs").insert({
                "session_id": session_id,
                "requirements": requirements,
                "architecture": architecture,
                "tech_stack": tech_stack,
                "version": 1
            }).execute()
            return response.data[0]
        except Exception as e:
            logger.error(f"Error saving technical spec: {e}")
            raise

    async def get_technical_spec(self, session_id: str) -> Optional[dict]:
        """Fetch the latest technical spec for a session."""
        try:
            response = self.client.table("technical_specs")\
                .select("*")\
                .eq("session_id", session_id)\
                .order("version", desc=True)\
                .limit(1)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching technical spec: {e}")
            return None

    # ------------------------------------------------------------------
    # DOCUMENTATION LINKS
    # ------------------------------------------------------------------

    async def save_documentation_links(
        self,
        session_id: str,
        links: list[dict]
    ) -> list[dict]:
        """
        Bulk save documentation links from the Librarian agent.

        Each link dict should have:
            - tech_name: str
            - doc_url: str
            - scraped_content: str (optional)
            - relevance_score: float (optional)
        """
        try:
            records = [
                {
                    "session_id": session_id,
                    "tech_name": link.get("tech_name", ""),
                    "doc_url": link.get("doc_url", ""),
                    "scraped_content": link.get("scraped_content"),
                    "relevance_score": link.get("relevance_score")
                }
                for link in links
            ]
            response = self.client.table("documentation_links")\
                .insert(records)\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error saving documentation links: {e}")
            raise

    async def get_documentation_links(self, session_id: str) -> list[dict]:
        """Fetch all documentation links for a session."""
        try:
            response = self.client.table("documentation_links")\
                .select("*")\
                .eq("session_id", session_id)\
                .order("relevance_score", desc=True)\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching documentation links: {e}")
            return []

    # ------------------------------------------------------------------
    # CODE SCAFFOLDS
    # ------------------------------------------------------------------

    async def save_code_scaffolds(
        self,
        session_id: str,
        scaffolds: list[dict]
    ) -> list[dict]:
        """
        Bulk save code scaffolds from the Mentor agent.

        Each scaffold dict should have:
            - file_path: str
            - content: str
            - hints: list[str]
        """
        try:
            records = [
                {
                    "session_id": session_id,
                    "file_path": scaffold.get("file_path", ""),
                    "content": scaffold.get("content", ""),
                    "hints": scaffold.get("hints", []),
                    "completed": False
                }
                for scaffold in scaffolds
            ]
            response = self.client.table("code_scaffolds")\
                .insert(records)\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error saving code scaffolds: {e}")
            raise

    async def get_code_scaffolds(self, session_id: str) -> list[dict]:
        """Fetch all code scaffolds for a session."""
        try:
            response = self.client.table("code_scaffolds")\
                .select("*")\
                .eq("session_id", session_id)\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching code scaffolds: {e}")
            return []


# Singleton instance
db_service = DatabaseService()
