"""
Vector Service - Qdrant operations for semantic search and embeddings.
Handles documentation embeddings, conversation context, and code patterns.
Uses Gemini's embedding model to generate vectors.
"""
import logging
from typing import Optional
from uuid import uuid4

import google.generativeai as genai
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.config import settings

logger = logging.getLogger(__name__)

# Collection names
DOCS_COLLECTION = "documentation_embeddings"
CONV_COLLECTION = "conversation_embeddings"
CODE_COLLECTION = "code_patterns"


class VectorService:
    """
    Qdrant service for semantic search across documentation,
    conversations, and code patterns.
    """

    def __init__(self):
        try:
            self.client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
            )
            genai.configure(api_key=settings.gemini_api_key)
            self.enabled = True
            logger.info("✅ Vector Service initialized (Qdrant)")
        except Exception as e:
            logger.warning(f"⚠️ Qdrant initialization failed: {e}")
            logger.warning("Vector search will be disabled. The app will still work without it.")
            self.enabled = False
            self.client = None

    # ------------------------------------------------------------------
    # COLLECTION SETUP
    # ------------------------------------------------------------------

    def _ensure_collections(self):
        """Create Qdrant collections if they don't already exist."""
        if not self.enabled:
            return
            
        try:
            existing = [c.name for c in self.client.get_collections().collections]
        except Exception as e:
            logger.error(f"⚠️ Could not connect to Qdrant: {e}")
            logger.warning("Vector search will be disabled. Check your QDRANT_URL and QDRANT_API_KEY")
            self.enabled = False
            return

        collections = {
            DOCS_COLLECTION: "Documentation chunks from official docs",
            CONV_COLLECTION: "Conversation context per session",
            CODE_COLLECTION: "Reusable code patterns and snippets",
        }

        for name, description in collections.items():
            if name not in existing:
                try:
                    self.client.create_collection(
                        collection_name=name,
                        vectors_config=VectorParams(
                            size=settings.vector_dimension,
                            distance=Distance.COSINE,
                        ),
                    )
                    logger.info(f"Created Qdrant collection: {name} ({description})")
                except Exception as e:
                    logger.error(f"Failed to create collection {name}: {e}")
            else:
                logger.info(f"Qdrant collection already exists: {name}")

    # ------------------------------------------------------------------
    # EMBEDDINGS
    # ------------------------------------------------------------------

    async def embed(self, text: str) -> list[float]:
        """
        Generate an embedding vector for a piece of text using Gemini.

        Args:
            text: The text to embed

        Returns:
            A list of floats representing the embedding vector
        """
        if not self.enabled:
            logger.warning("Vector service is disabled - returning empty embedding")
            return []
            
        try:
            result = genai.embed_content(
                model=settings.embedding_model,
                content=text,
                task_type="retrieval_document",
            )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return []

    async def embed_query(self, text: str) -> list[float]:
        """
        Generate a query embedding (different task type for better retrieval).

        Args:
            text: The search query to embed

        Returns:
            A list of floats representing the query embedding vector
        """
        if not self.enabled:
            logger.warning("Vector service is disabled - returning empty embedding")
            return []
            
        try:
            result = genai.embed_content(
                model=settings.embedding_model,
                content=text,
                task_type="retrieval_query",
            )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Query embedding error: {e}")
            return []

    # ------------------------------------------------------------------
    # DOCUMENTATION EMBEDDINGS
    # ------------------------------------------------------------------

    async def store_documentation(
        self,
        tech_name: str,
        doc_url: str,
        section_title: str,
        content: str,
        chunk_index: int = 0,
    ) -> str:
        """
        Embed and store a documentation chunk in Qdrant.

        Args:
            tech_name:      Technology name (e.g., "FastAPI")
            doc_url:        Source URL
            section_title:  Section or page title
            content:        The actual documentation text
            chunk_index:    Position of this chunk within the document

        Returns:
            The ID of the stored point
        """
        if not self.enabled:
            logger.warning("Vector service disabled - skipping doc storage")
            return ""
            
        try:
            self._ensure_collections()  # Lazy init collections
            vector = await self.embed(content)
            if not vector:
                return ""
                
            point_id = str(uuid4())

            self.client.upsert(
                collection_name=DOCS_COLLECTION,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "tech_name": tech_name,
                            "doc_url": doc_url,
                            "section_title": section_title,
                            "content": content,
                            "chunk_index": chunk_index,
                        },
                    )
                ],
            )
            return point_id
        except Exception as e:
            logger.error(f"Error storing documentation: {e}")
            return ""

    async def search_documentation(
        self,
        query: str,
        tech_name: Optional[str] = None,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Semantic search over stored documentation.

        Args:
            query:      Natural language search query
            tech_name:  Optional filter to search within a specific technology
            top_k:      Number of results to return

        Returns:
            List of matching documentation chunks with scores
        """
        if not self.enabled:
            logger.warning("Vector service disabled - skipping doc search")
            return []
            
        try:
            self._ensure_collections()
            query_vector = await self.embed_query(query)
            if not query_vector:
                return []

            query_filter = None
            if tech_name:
                query_filter = Filter(
                    must=[FieldCondition(
                        key="tech_name",
                        match=MatchValue(value=tech_name)
                    )]
                )

            results = self.client.search(
                collection_name=DOCS_COLLECTION,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
            )

            return [
                {
                    "score": hit.score,
                    "tech_name": hit.payload.get("tech_name"),
                    "doc_url": hit.payload.get("doc_url"),
                    "section_title": hit.payload.get("section_title"),
                    "content": hit.payload.get("content"),
                }
                for hit in results
            ]
        except Exception as e:
            logger.error(f"Documentation search error: {e}")
            return []

    # ------------------------------------------------------------------
    # CONVERSATION EMBEDDINGS
    # ------------------------------------------------------------------

    async def store_conversation_message(
        self,
        session_id: str,
        message_id: str,
        phase: str,
        content: str,
        timestamp: int,
    ) -> str:
        """
        Embed and store a conversation message for context retrieval.

        Args:
            session_id:  Session identifier
            message_id:  Message identifier
            phase:       Current agent phase (planner/librarian/mentor)
            content:     Message content
            timestamp:   Unix timestamp

        Returns:
            The ID of the stored point
        """
        try:
            vector = await self.embed(content)

            self.client.upsert(
                collection_name=CONV_COLLECTION,
                points=[
                    PointStruct(
                        id=message_id,
                        vector=vector,
                        payload={
                            "session_id": session_id,
                            "phase": phase,
                            "content": content,
                            "timestamp": timestamp,
                        },
                    )
                ],
            )
            return message_id
        except Exception as e:
            logger.error(f"Error storing conversation message: {e}")
            raise

    async def search_conversation_context(
        self,
        query: str,
        session_id: str,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Retrieve the most relevant past messages from a session.

        Args:
            query:      Current message or query
            session_id: Session to search within
            top_k:      Number of results to return

        Returns:
            List of relevant past messages with scores
        """
        try:
            query_vector = await self.embed_query(query)

            results = self.client.search(
                collection_name=CONV_COLLECTION,
                query_vector=query_vector,
                query_filter=Filter(
                    must=[FieldCondition(
                        key="session_id",
                        match=MatchValue(value=session_id)
                    )]
                ),
                limit=top_k,
                with_payload=True,
            )

            return [
                {
                    "score": hit.score,
                    "phase": hit.payload.get("phase"),
                    "content": hit.payload.get("content"),
                    "timestamp": hit.payload.get("timestamp"),
                }
                for hit in results
            ]
        except Exception as e:
            logger.error(f"Conversation context search error: {e}")
            return []

    # ------------------------------------------------------------------
    # CODE PATTERNS
    # ------------------------------------------------------------------

    async def store_code_pattern(
        self,
        pattern_name: str,
        tech_stack: list[str],
        code_snippet: str,
        description: str,
        use_case: str,
    ) -> str:
        """
        Store a reusable code pattern for scaffolding suggestions.

        Args:
            pattern_name:  Name of the pattern (e.g., "FastAPI CRUD router")
            tech_stack:    Technologies involved
            code_snippet:  The actual code
            description:   What this pattern does
            use_case:      When to use it

        Returns:
            The ID of the stored point
        """
        try:
            embed_text = f"{pattern_name}: {description}. Use case: {use_case}"
            vector = await self.embed(embed_text)
            point_id = str(uuid4())

            self.client.upsert(
                collection_name=CODE_COLLECTION,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "pattern_name": pattern_name,
                            "tech_stack": tech_stack,
                            "code_snippet": code_snippet,
                            "description": description,
                            "use_case": use_case,
                        },
                    )
                ],
            )
            return point_id
        except Exception as e:
            logger.error(f"Error storing code pattern: {e}")
            raise

    async def search_code_patterns(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[dict]:
        """
        Find relevant code patterns for scaffolding.

        Args:
            query:  Description of what's needed
            top_k:  Number of patterns to return

        Returns:
            List of matching code patterns with scores
        """
        if not self.enabled:
            return []
            
        try:
            self._ensure_collections()
            query_vector = await self.embed_query(query)
            if not query_vector:
                return []

            results = self.client.search(
                collection_name=CODE_COLLECTION,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True,
            )

            return [
                {
                    "score": hit.score,
                    "pattern_name": hit.payload.get("pattern_name"),
                    "tech_stack": hit.payload.get("tech_stack"),
                    "code_snippet": hit.payload.get("code_snippet"),
                    "description": hit.payload.get("description"),
                    "use_case": hit.payload.get("use_case"),
                }
                for hit in results
            ]
        except Exception as e:
            logger.error(f"Code pattern search error: {e}")
            return []


# Singleton instance
vector_service = VectorService()