"""
LLM Service - Unified interface for Gemini and Groq APIs.
Gemini handles Planner and Mentor agents (reasoning heavy).
Groq handles Librarian agent (speed critical).
"""
import logging
from typing import Optional, AsyncGenerator
from enum import Enum

import google.generativeai as genai
from groq import AsyncGroq

from app.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    GEMINI = "gemini"
    GROQ = "groq"


# Model constants
GEMINI_MODEL = "gemini-3-flash-preview"
GROQ_MODEL = "llama-3.3-70b-versatile"


class LLMService:
    """
    Unified interface for Gemini and Groq.
    - Gemini  → Planner, Mentor (deep reasoning)
    - Groq    → Librarian (fast processing)
    """

    def __init__(self):
        # Configure Gemini
        genai.configure(api_key=settings.gemini_api_key)
        self.gemini_model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config={
                "temperature": settings.temperature,
                "max_output_tokens": settings.max_tokens,
            }
        )

        # Configure Groq
        self.groq_client = AsyncGroq(api_key=settings.groq_api_key)

        logger.info("✅ LLM Service initialized (Gemini + Groq)")

    # ------------------------------------------------------------------
    # GEMINI
    # ------------------------------------------------------------------

    async def gemini_chat(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Send a multi-turn conversation to Gemini and return the response.

        Args:
            messages:       List of {"role": "user"|"model", "parts": [str]} dicts
            system_prompt:  Optional system instruction prepended to the chat
            temperature:    Override default temperature

        Returns:
            Assistant response as a string
        """
        try:
            # Prepend system prompt as first user message if provided
            if system_prompt:
                messages = [
                    {"role": "user", "content": system_prompt},
                    {"role": "model", "content": "Understood. I will follow these instructions."},
                ] + messages

            model = self.gemini_model
            if temperature is not None:
                model = genai.GenerativeModel(
                    model_name=GEMINI_MODEL,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": settings.max_tokens,
                    }
                )

            # Build Gemini history (all messages except the last user message)
            history = []
            for msg in messages[:-1]:
                history.append({
                    "role": msg["role"],          # "user" or "model"
                    "parts": [msg["content"]]
                })

            chat = model.start_chat(history=history)
            response = await chat.send_message_async(messages[-1]["content"])

            return response.text

        except Exception as e:
            logger.error(f"Gemini chat error: {e}")
            raise

    async def gemini_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Simple single-turn generation with Gemini.

        Args:
            prompt:         The user prompt
            system_prompt:  Optional system instruction
            temperature:    Override default temperature

        Returns:
            Generated text as a string
        """
        try:
            # Prepend system prompt to user prompt if provided
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            else:
                full_prompt = prompt

            model = self.gemini_model
            if temperature is not None:
                model = genai.GenerativeModel(
                    model_name=GEMINI_MODEL,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": settings.max_tokens,
                    }
                )

            response = await model.generate_content_async(full_prompt)
            return response.text

        except Exception as e:
            logger.error(f"Gemini generate error: {e}")
            raise

    async def gemini_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a Gemini response chunk by chunk.

        Yields:
            Text chunks as they arrive
        """
        try:
            # Prepend system prompt if provided
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            else:
                full_prompt = prompt

            model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                generation_config={
                    "temperature": settings.temperature,
                    "max_output_tokens": settings.max_tokens,
                }
            )

            response = await model.generate_content_async(full_prompt, stream=True)
            async for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Gemini stream error: {e}")
            raise

    # ------------------------------------------------------------------
    # GROQ
    # ------------------------------------------------------------------

    async def groq_chat(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Send a conversation to Groq and return the response.

        Args:
            messages:       List of {"role": "user"|"assistant", "content": str} dicts
            system_prompt:  Optional system message prepended to messages
            temperature:    Override default temperature

        Returns:
            Assistant response as a string
        """
        try:
            formatted = []
            if system_prompt:
                formatted.append({"role": "system", "content": system_prompt})

            for msg in messages:
                formatted.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            response = await self.groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=formatted,
                temperature=temperature or settings.temperature,
                max_tokens=settings.max_tokens,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Groq chat error: {e}")
            raise

    async def groq_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Simple single-turn generation with Groq.

        Args:
            prompt:         The user prompt
            system_prompt:  Optional system message
            temperature:    Override default temperature

        Returns:
            Generated text as a string
        """
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await self.groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=temperature or settings.temperature,
                max_tokens=settings.max_tokens,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Groq generate error: {e}")
            raise

    async def groq_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a Groq response chunk by chunk.

        Yields:
            Text chunks as they arrive
        """
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            stream = await self.groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                stream=True,
            )

            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta

        except Exception as e:
            logger.error(f"Groq stream error: {e}")
            raise


# Singleton instance
llm_service = LLMService()