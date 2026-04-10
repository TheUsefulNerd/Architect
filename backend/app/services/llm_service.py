"""
LLM Service - Groq primary, Gemini fallback interface for all agents.
Planner, Librarian, and Mentor all go through this service.

Provider priority:
  1. Groq  (llama-3.3-70b-versatile) — fast, generous free tier
  2. Gemini (gemini-2.5-flash)        — fallback on any Groq failure

Retry strategy (applied per provider before falling back):
  Attempt 1 → immediate
  Attempt 2 → wait 2s
  Attempt 3 → wait 4s
  Attempt 4 → wait 8s
  Attempt 5 → wait 16s  (then falls back to next provider)
"""
import asyncio
import logging
from typing import Optional, AsyncGenerator

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable
from groq import AsyncGroq, RateLimitError, APIStatusError

from app.config import settings

logger = logging.getLogger(__name__)

# Model constants — override via .env (default_model / fallback_model)
GROQ_MODEL   = settings.default_model    # e.g. "llama-3.3-70b-versatile"
GEMINI_MODEL = settings.fallback_model   # e.g. "gemini-2.5-flash"

# Retry configuration
MAX_RETRIES    = 5
BASE_DELAY_SEC = 2.0   # doubles each attempt: 2 → 4 → 8 → 16


# ------------------------------------------------------------------
# RETRY HELPERS
# ------------------------------------------------------------------

def _is_groq_retryable(exc: Exception) -> bool:
    """Return True for transient Groq errors worth retrying."""
    if isinstance(exc, RateLimitError):
        return True
    if isinstance(exc, APIStatusError) and exc.status_code in (429, 503):
        return True
    msg = str(exc).lower()
    return "429" in msg or "rate_limit" in msg or "quota" in msg


def _is_gemini_retryable(exc: Exception) -> bool:
    """Return True for transient Gemini errors worth retrying."""
    if isinstance(exc, (ResourceExhausted, ServiceUnavailable)):
        return True
    msg = str(exc).lower()
    return "429" in msg or "resource_exhausted" in msg or "quota" in msg


async def _with_retry(coro_fn, label: str, is_retryable_fn) -> str:
    """
    Execute an async callable with exponential backoff.

    Args:
        coro_fn:          Zero-argument async callable that returns the result.
        label:            Short name used in log messages (e.g. "groq_chat").
        is_retryable_fn:  Function(exc) → bool deciding whether to retry.

    Raises:
        The last exception if all retries are exhausted.
    """
    delay = BASE_DELAY_SEC
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return await coro_fn()
        except Exception as exc:
            if not is_retryable_fn(exc) or attempt == MAX_RETRIES:
                logger.error(f"[{label}] Failed after {attempt} attempt(s): {exc}")
                raise
            logger.warning(
                f"[{label}] Attempt {attempt}/{MAX_RETRIES} hit rate limit — "
                f"retrying in {delay:.0f}s. Error: {exc}"
            )
            await asyncio.sleep(delay)
            delay *= 2


# ------------------------------------------------------------------
# LLM SERVICE
# ------------------------------------------------------------------

class LLMService:
    """
    Unified LLM interface for all three Architect agents.

    Public API (unchanged from the Gemini-only version):
      - gemini_chat(messages, system_prompt, temperature)   → str
      - gemini_generate(prompt, system_prompt, temperature) → str
      - gemini_stream(prompt, system_prompt)               → AsyncGenerator[str]

    Internally, every call tries Groq first and falls back to Gemini
    on any failure. The method names are kept as-is so no agent code
    needs to change.
    """

    def __init__(self):
        # Groq client
        self._groq = AsyncGroq(api_key=settings.groq_api_key)

        # Gemini client
        genai.configure(api_key=settings.gemini_api_key)
        self._gemini_model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config={
                "temperature": settings.temperature,
                "max_output_tokens": settings.max_tokens,
            }
        )

        logger.info(
            f"✅ LLM Service initialized — "
            f"primary: Groq ({GROQ_MODEL}), fallback: Gemini ({GEMINI_MODEL})"
        )

    # ------------------------------------------------------------------
    # PUBLIC: CHAT  (multi-turn — used by Planner and Librarian)
    # ------------------------------------------------------------------

    async def gemini_chat(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Multi-turn conversation: tries Groq first, falls back to Gemini.

        Args:
            messages:      List of {"role": "user"|"model"|"assistant", "content": str}.
            system_prompt: Optional system instruction.
            temperature:   Per-call temperature override.

        Returns:
            Assistant response as a string.
        """
        try:
            return await self._groq_chat(messages, system_prompt, temperature)
        except Exception as groq_exc:
            logger.warning(f"[LLMService] Groq chat failed — falling back to Gemini. Error: {groq_exc}")
            return await self._gemini_chat(messages, system_prompt, temperature)

    # ------------------------------------------------------------------
    # PUBLIC: GENERATE  (single-turn — used by Librarian and Mentor)
    # ------------------------------------------------------------------

    async def gemini_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Single-turn generation: tries Groq first, falls back to Gemini.

        Args:
            prompt:        The user prompt.
            system_prompt: Optional system instruction.
            temperature:   Per-call temperature override.

        Returns:
            Generated text as a string.
        """
        try:
            return await self._groq_generate(prompt, system_prompt, temperature)
        except Exception as groq_exc:
            logger.warning(f"[LLMService] Groq generate failed — falling back to Gemini. Error: {groq_exc}")
            return await self._gemini_generate(prompt, system_prompt, temperature)

    # ------------------------------------------------------------------
    # PUBLIC: STREAM  (streaming single-turn — Groq primary, Gemini fallback)
    # ------------------------------------------------------------------

    async def gemini_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response chunk by chunk.
        Tries Groq first; on failure, falls back to Gemini streaming.
        Note: streaming is not retried — errors surface immediately.

        Yields:
            Text chunks as they arrive.
        """
        try:
            async for chunk in self._groq_stream(prompt, system_prompt):
                yield chunk
        except Exception as groq_exc:
            logger.warning(f"[LLMService] Groq stream failed — falling back to Gemini. Error: {groq_exc}")
            async for chunk in self._gemini_stream(prompt, system_prompt):
                yield chunk

    # ------------------------------------------------------------------
    # GROQ INTERNALS
    # ------------------------------------------------------------------

    async def _groq_chat(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Multi-turn chat via Groq (OpenAI-compatible messages format)."""

        async def _call():
            groq_messages = []
            if system_prompt:
                groq_messages.append({"role": "system", "content": system_prompt})
            for m in messages:
                role = "assistant" if m["role"] in ("model", "assistant") else m["role"]
                groq_messages.append({"role": role, "content": m["content"]})

            response = await self._groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=groq_messages,
                temperature=temperature if temperature is not None else settings.temperature,
                max_tokens=settings.max_tokens,
            )
            return response.choices[0].message.content

        return await _with_retry(_call, "groq_chat", _is_groq_retryable)

    async def _groq_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Single-turn generation via Groq."""

        async def _call():
            groq_messages = []
            if system_prompt:
                groq_messages.append({"role": "system", "content": system_prompt})
            groq_messages.append({"role": "user", "content": prompt})

            response = await self._groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=groq_messages,
                temperature=temperature if temperature is not None else settings.temperature,
                max_tokens=settings.max_tokens,
            )
            return response.choices[0].message.content

        return await _with_retry(_call, "groq_generate", _is_groq_retryable)

    async def _groq_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Streaming generation via Groq."""
        groq_messages = []
        if system_prompt:
            groq_messages.append({"role": "system", "content": system_prompt})
        groq_messages.append({"role": "user", "content": prompt})

        try:
            stream = await self._groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=groq_messages,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as e:
            logger.error(f"[groq_stream] Error: {e}")
            raise

    # ------------------------------------------------------------------
    # GEMINI INTERNALS
    # ------------------------------------------------------------------

    async def _gemini_chat(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Multi-turn chat via Gemini (fallback)."""

        async def _call():
            normalised = [
                {
                    "role": "model" if m["role"] in ("assistant", "model") else m["role"],
                    "content": m["content"],
                }
                for m in messages
            ]

            if system_prompt:
                normalised = [
                    {"role": "user",  "content": system_prompt},
                    {"role": "model", "content": "Understood. I will follow these instructions."},
                ] + normalised

            model = self._gemini_model_with_temp(temperature)
            history = [
                {"role": m["role"], "parts": [m["content"]]}
                for m in normalised[:-1]
            ]
            chat = model.start_chat(history=history)
            response = await chat.send_message_async(normalised[-1]["content"])
            return response.text

        return await _with_retry(_call, "gemini_chat_fallback", _is_gemini_retryable)

    async def _gemini_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Single-turn generation via Gemini (fallback)."""

        async def _call():
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            model = self._gemini_model_with_temp(temperature)
            response = await model.generate_content_async(full_prompt)
            return response.text

        return await _with_retry(_call, "gemini_generate_fallback", _is_gemini_retryable)

    async def _gemini_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Streaming generation via Gemini (fallback)."""
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
            logger.error(f"[gemini_stream_fallback] Error: {e}")
            raise

    def _gemini_model_with_temp(self, temperature: Optional[float]) -> genai.GenerativeModel:
        """Return a Gemini model instance, overriding temperature when specified."""
        if temperature is None:
            return self._gemini_model
        return genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": settings.max_tokens,
            }
        )


# Singleton instance
llm_service = LLMService()