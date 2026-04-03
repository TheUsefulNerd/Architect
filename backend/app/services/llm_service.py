"""
LLM Service - Gemini-only interface for all agents.
Planner, Librarian, and Mentor all use Gemini.

Retry strategy: exponential backoff on 429 ResourceExhausted errors.
  Attempt 1 → immediate
  Attempt 2 → wait 2s
  Attempt 3 → wait 4s
  Attempt 4 → wait 8s
  Attempt 5 → wait 16s  (then raises)
"""
import asyncio
import logging
from typing import Optional, AsyncGenerator

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable

from app.config import settings

logger = logging.getLogger(__name__)

# Read from config so you can swap models via .env without touching code.
# Free-tier quota is per-model — switch instantly by changing GEMINI_MODEL in .env:
# gemini-2.0-flash | gemini-1.5-flash | gemini-1.5-flash-8b
GEMINI_MODEL = "gemini-2.5-flash"

# Retry configuration
MAX_RETRIES    = 5
BASE_DELAY_SEC = 2.0   # doubles each attempt: 2 → 4 → 8 → 16


def _is_retryable(exc: Exception) -> bool:
    """Return True for transient Gemini errors worth retrying."""
    if isinstance(exc, (ResourceExhausted, ServiceUnavailable)):
        return True
    msg = str(exc).lower()
    return "429" in msg or "resource_exhausted" in msg or "quota" in msg


async def _with_retry(coro_fn, label: str):
    """
    Execute an async callable with exponential backoff.

    Args:
        coro_fn: Zero-argument async callable that returns the result.
        label:   Short name used in log messages (e.g. "gemini_chat").
    """
    delay = BASE_DELAY_SEC
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return await coro_fn()
        except Exception as exc:
            if not _is_retryable(exc) or attempt == MAX_RETRIES:
                logger.error(f"[{label}] Failed after {attempt} attempt(s): {exc}")
                raise
            logger.warning(
                f"[{label}] Attempt {attempt}/{MAX_RETRIES} hit quota/rate limit — "
                f"retrying in {delay:.0f}s. Error: {exc}"
            )
            await asyncio.sleep(delay)
            delay *= 2


class LLMService:
    """
    Unified Gemini interface for all three Architect agents.
    Provides chat (multi-turn), generate (single-turn), and stream variants.
    All public methods automatically retry on 429 / quota errors.
    """

    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.gemini_model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config={
                "temperature": settings.temperature,
                "max_output_tokens": settings.max_tokens,
            }
        )
        logger.info(f"✅ LLM Service initialized (Gemini — {GEMINI_MODEL})")

    # ------------------------------------------------------------------
    # GEMINI CHAT  (multi-turn, used by Planner and Librarian)
    # ------------------------------------------------------------------

    async def gemini_chat(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Send a multi-turn conversation to Gemini and return the response.
        Retries automatically on quota / rate-limit errors.

        Args:
            messages:      List of {"role": "user"|"model"|"assistant", "content": str} dicts.
                           "assistant" is normalised to "model" automatically.
            system_prompt: Optional instruction prepended as the first exchange.
            temperature:   Override default temperature for this call.

        Returns:
            Assistant response as a string.
        """
        async def _call():
            # Normalise "assistant" → "model" (Gemini's expected role name)
            normalised = [
                {
                    "role": "model" if m["role"] == "assistant" else m["role"],
                    "content": m["content"],
                }
                for m in messages
            ]

            # Inject system prompt as a seeded user/model exchange at the front
            if system_prompt:
                normalised = [
                    {"role": "user",  "content": system_prompt},
                    {"role": "model", "content": "Understood. I will follow these instructions."},
                ] + normalised

            model = self._model_with_temp(temperature)

            # History = everything except the final user message
            history = [
                {"role": m["role"], "parts": [m["content"]]}
                for m in normalised[:-1]
            ]

            chat = model.start_chat(history=history)
            response = await chat.send_message_async(normalised[-1]["content"])
            return response.text

        return await _with_retry(_call, "gemini_chat")

    # ------------------------------------------------------------------
    # GEMINI GENERATE  (single-turn, used by Librarian and Mentor)
    # ------------------------------------------------------------------

    async def gemini_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Single-turn generation with Gemini.
        Retries automatically on quota / rate-limit errors.

        Args:
            prompt:        The user prompt.
            system_prompt: Optional instruction prepended to the prompt.
            temperature:   Override default temperature for this call.

        Returns:
            Generated text as a string.
        """
        async def _call():
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            model = self._model_with_temp(temperature)
            response = await model.generate_content_async(full_prompt)
            return response.text

        return await _with_retry(_call, "gemini_generate")

    # ------------------------------------------------------------------
    # GEMINI STREAM  (streaming single-turn, available for future use)
    # ------------------------------------------------------------------

    async def gemini_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a Gemini response chunk by chunk.
        Note: streaming is not retried — the caller receives chunks in real time.
        On a 429, the generator raises immediately so the SSE handler can surface
        a user-friendly error without leaving the stream hanging.

        Yields:
            Text chunks as they arrive.
        """
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config={
                "temperature": settings.temperature,
                "max_output_tokens": settings.max_tokens,
            }
        )
        try:
            response = await model.generate_content_async(full_prompt, stream=True)
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"[gemini_stream] Error: {e}")
            raise

    # ------------------------------------------------------------------
    # INTERNAL HELPERS
    # ------------------------------------------------------------------

    def _model_with_temp(self, temperature: Optional[float]) -> genai.GenerativeModel:
        """Return a model instance, overriding temperature when specified."""
        if temperature is None:
            return self.gemini_model
        return genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": settings.max_tokens,
            }
        )


# Singleton instance
llm_service = LLMService()