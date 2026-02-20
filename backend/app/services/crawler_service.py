"""
Crawler Service - Web scraping and documentation fetching.
Scrapes official documentation pages, extracts clean content,
and formats results with citations (Perplexity-style).
"""
import asyncio
import logging
import re
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import settings

logger = logging.getLogger(__name__)

# Known documentation base URLs for common technologies
KNOWN_DOC_URLS: dict[str, str] = {
    # Backend
    "fastapi":       "https://fastapi.tiangolo.com",
    "flask":         "https://flask.palletsprojects.com",
    "django":        "https://docs.djangoproject.com",
    "express":       "https://expressjs.com",
    "langchain":     "https://python.langchain.com/docs",
    "langgraph":     "https://langchain-ai.github.io/langgraph",
    "pydantic":      "https://docs.pydantic.dev",
    "sqlalchemy":    "https://docs.sqlalchemy.org",
    "celery":        "https://docs.celeryq.dev",
    # AI / ML
    "openai":        "https://platform.openai.com/docs",
    "gemini":        "https://ai.google.dev/docs",
    "groq":          "https://console.groq.com/docs",
    "huggingface":   "https://huggingface.co/docs",
    "pytorch":       "https://pytorch.org/docs",
    "tensorflow":    "https://www.tensorflow.org/api_docs",
    # Databases
    "supabase":      "https://supabase.com/docs",
    "qdrant":        "https://qdrant.tech/documentation",
    "mongodb":       "https://www.mongodb.com/docs",
    "redis":         "https://redis.io/docs",
    "postgresql":    "https://www.postgresql.org/docs",
    # Frontend
    "nextjs":        "https://nextjs.org/docs",
    "next.js":       "https://nextjs.org/docs",
    "react":         "https://react.dev",
    "vue":           "https://vuejs.org/guide",
    "tailwind":      "https://tailwindcss.com/docs",
    "tailwindcss":   "https://tailwindcss.com/docs",
    "typescript":    "https://www.typescriptlang.org/docs",
    # Infrastructure
    "terraform":     "https://developer.hashicorp.com/terraform/docs",
    "docker":        "https://docs.docker.com",
    "kubernetes":    "https://kubernetes.io/docs",
    "gcp":           "https://cloud.google.com/docs",
    "aws":           "https://docs.aws.amazon.com",
}


class CrawlerService:
    """
    Scrapes documentation pages for the Librarian agent.
    Returns structured content with citations.
    """

    def __init__(self):
        self.headers = {
            "User-Agent": settings.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self.timeout = settings.request_timeout
        logger.info("✅ Crawler Service initialized")

    # ------------------------------------------------------------------
    # MAIN ENTRY POINT
    # ------------------------------------------------------------------

    async def fetch_docs_for_tech_stack(
        self,
        tech_stack: dict[str, list[str]],
        context: str,
    ) -> list[dict]:
        """
        Given a full tech stack dict and project context,
        fetch relevant documentation for each technology.

        Args:
            tech_stack: e.g. {"backend": ["FastAPI", "LangGraph"], "database": ["Supabase"]}
            context:    Project description to guide relevance

        Returns:
            List of documentation results with citations
        """
        # Flatten all technologies from all categories
        all_techs: list[str] = []
        for techs in tech_stack.values():
            all_techs.extend(techs)

        logger.info(f"Fetching docs for: {all_techs}")

        # Fetch docs for all technologies concurrently
        tasks = [self.fetch_docs_for_technology(tech, context) for tech in all_techs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results, skipping errors
        docs: list[dict] = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Doc fetch error: {result}")
                continue
            if isinstance(result, list):
                docs.extend(result)

        return docs

    async def fetch_docs_for_technology(
        self,
        tech_name: str,
        context: str,
    ) -> list[dict]:
        """
        Fetch documentation for a single technology.

        Args:
            tech_name:  Technology name (e.g., "FastAPI", "LangGraph")
            context:    Project description for relevance filtering

        Returns:
            List of documentation chunks with citations
        """
        normalized = tech_name.lower().strip()
        base_url = KNOWN_DOC_URLS.get(normalized)

        if not base_url:
            logger.warning(f"No known doc URL for '{tech_name}', skipping.")
            return [{
                "tech_name": tech_name,
                "doc_url": f"https://www.google.com/search?q={tech_name}+documentation",
                "section_title": f"{tech_name} Documentation",
                "content": f"Documentation for {tech_name} is not indexed. Search online for official docs.",
                "relevance_score": 0.5,
                "is_fallback": True,
            }]

        try:
            page = await self._fetch_page(base_url)
            if not page:
                return []

            sections = self._extract_sections(page, base_url)

            return [
                {
                    "tech_name": tech_name,
                    "doc_url": section["url"],
                    "section_title": section["title"],
                    "content": section["content"],
                    "relevance_score": 1.0,
                    "is_fallback": False,
                }
                for section in sections[:5]     # cap at 5 sections per tech
            ]

        except Exception as e:
            logger.error(f"Error fetching docs for {tech_name}: {e}")
            return []

    async def fetch_single_url(self, url: str) -> Optional[dict]:
        """
        Fetch and parse a single documentation URL.

        Args:
            url: Full URL to scrape

        Returns:
            Dict with title, content, and url, or None on failure
        """
        try:
            page = await self._fetch_page(url)
            if not page:
                return None

            sections = self._extract_sections(page, url)
            if not sections:
                return None

            # Merge all sections into one result
            return {
                "url": url,
                "title": sections[0]["title"],
                "content": "\n\n".join(s["content"] for s in sections),
            }
        except Exception as e:
            logger.error(f"Error fetching URL {url}: {e}")
            return None

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    async def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a URL and return a BeautifulSoup object."""
        try:
            async with httpx.AsyncClient(
                headers=self.headers,
                timeout=self.timeout,
                follow_redirects=True,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                return BeautifulSoup(response.text, "html.parser")

        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching {url}")
            return None
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP {e.response.status_code} for {url}")
            return None
        except Exception as e:
            logger.error(f"Fetch error for {url}: {e}")
            return None

    # ------------------------------------------------------------------
    # CONTENT EXTRACTION
    # ------------------------------------------------------------------

    def _extract_sections(
        self,
        soup: BeautifulSoup,
        base_url: str,
    ) -> list[dict]:
        """
        Extract clean sections from a documentation page.

        Args:
            soup:     Parsed HTML
            base_url: Base URL for resolving relative links

        Returns:
            List of sections with title, content, and url
        """
        sections: list[dict] = []

        # Remove noise
        for tag in soup(["nav", "footer", "script", "style",
                          "head", "header", "aside", "advertisement"]):
            tag.decompose()

        # Try to find the main content area
        main = (
            soup.find("main")
            or soup.find("article")
            or soup.find(class_=re.compile(r"content|main|docs|documentation", re.I))
            or soup.find("body")
        )

        if not main:
            return []

        # Extract page title
        page_title = ""
        title_tag = soup.find("h1") or soup.find("title")
        if title_tag:
            page_title = self._clean_text(title_tag.get_text())

        # Split content by headings
        current_section = {"title": page_title, "content": "", "url": base_url}

        for element in main.children:
            if not hasattr(element, "name") or element.name is None:
                continue

            if element.name in ["h1", "h2", "h3"]:
                # Save current section if it has enough content
                if len(current_section["content"].strip()) > 80:
                    sections.append(current_section)

                # Start new section
                heading_text = self._clean_text(element.get_text())

                # Build anchor URL if possible
                section_id = element.get("id", "")
                section_url = f"{base_url}#{section_id}" if section_id else base_url

                current_section = {
                    "title": heading_text or page_title,
                    "content": "",
                    "url": section_url,
                }

            else:
                text = self._clean_text(element.get_text())
                if text:
                    current_section["content"] += text + "\n"

        # Don't forget the last section
        if len(current_section["content"].strip()) > 80:
            sections.append(current_section)

        return sections

    def _clean_text(self, text: str) -> str:
        """Remove excessive whitespace and normalize text."""
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    # ------------------------------------------------------------------
    # CITATION FORMATTER
    # ------------------------------------------------------------------

    def format_citations(self, docs: list[dict]) -> str:
        """
        Format documentation results as a Perplexity-style cited response.

        Args:
            docs: List of documentation dicts from fetch methods

        Returns:
            Formatted string with inline citations and a sources list
        """
        if not docs:
            return "No documentation found."

        lines: list[str] = []

        # Group by technology
        by_tech: dict[str, list[dict]] = {}
        for doc in docs:
            tech = doc.get("tech_name", "Unknown")
            by_tech.setdefault(tech, []).append(doc)

        citation_index = 1
        citation_map: list[dict] = []

        for tech, tech_docs in by_tech.items():
            lines.append(f"\n## {tech} Documentation\n")
            for doc in tech_docs:
                ref = citation_index
                citation_map.append({
                    "index": ref,
                    "title": doc.get("section_title", tech),
                    "url": doc.get("doc_url", ""),
                })

                lines.append(f"**{doc.get('section_title', tech)}** [{ref}]")
                lines.append(doc.get("content", "")[:800])   # cap snippet length
                lines.append("")
                citation_index += 1

        # Sources section
        lines.append("\n---\n### Sources\n")
        for cite in citation_map:
            lines.append(f"[{cite['index']}] {cite['title']} — {cite['url']}")

        return "\n".join(lines)


# Singleton instance
crawler_service = CrawlerService()
