"""
llm_client.py — Gemini primary + OpenAI fallback insight generation.
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from backend.config.settings import settings
from backend.insights.prompt_builder import build_template_insight

logger = logging.getLogger(__name__)

RETRY_ATTEMPTS = 3
BACKOFF_SECONDS = (1, 2, 4)


def _clean_text(text: str) -> str:
    return " ".join(str(text).strip().split())


def _call_gemini_once(prompt: str, api_key: str, model_name: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    text = getattr(response, "text", "") or ""
    if not text:
        raise RuntimeError("Gemini returned an empty response.")
    return _clean_text(text)


def _call_openai_once(prompt: str, api_key: str, model_name: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": (
                    "Bạn là trợ lý phân tích chất lượng không khí. "
                    "Trả lời ngắn, tiếng Việt, thận trọng, không bịa nguyên nhân."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=350,
    )
    text = response.choices[0].message.content or ""
    if not text:
        raise RuntimeError("OpenAI returned an empty response.")
    return _clean_text(text)


async def _call_with_retries(
    provider_name: str,
    call_fn: Callable[..., str],
    *args: Any,
    attempts: int = RETRY_ATTEMPTS,
    timeout_seconds: int | None = None,
) -> str:
    timeout_seconds = timeout_seconds or settings.LLM_TIMEOUT
    last_error: Exception | None = None

    for attempt in range(attempts):
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(call_fn, *args),
                timeout=timeout_seconds,
            )
        except Exception as exc:
            last_error = exc
            logger.warning(
                "%s insight attempt %d/%d failed: %s",
                provider_name,
                attempt + 1,
                attempts,
                exc,
            )
            if attempt < attempts - 1:
                await asyncio.sleep(BACKOFF_SECONDS[min(attempt, len(BACKOFF_SECONDS) - 1)])

    raise RuntimeError(f"{provider_name} failed after {attempts} attempts") from last_error


async def generate_insight_with_source(
    prompt: str,
    context: Any | None = None,
) -> tuple[str, str]:
    """Generate an insight and return (text, source)."""
    gemini_key = settings.GEMINI_API_KEY or settings.LLM_API_KEY
    gemini_model = settings.GEMINI_MODEL or settings.LLM_MODEL

    if gemini_key:
        try:
            text = await _call_with_retries(
                "Gemini",
                _call_gemini_once,
                prompt,
                gemini_key,
                gemini_model,
            )
            return text, "gemini"
        except Exception as exc:
            logger.warning("Gemini unavailable, falling back to OpenAI/template: %s", exc)
    else:
        logger.warning("Gemini API key missing; skipping Gemini insight provider.")

    if settings.OPENAI_API_KEY:
        try:
            text = await _call_with_retries(
                "OpenAI",
                _call_openai_once,
                prompt,
                settings.OPENAI_API_KEY,
                settings.OPENAI_MODEL,
            )
            return text, "openai"
        except Exception as exc:
            logger.warning("OpenAI fallback unavailable, using template insight: %s", exc)
    else:
        logger.warning("OpenAI API key missing; using template insight fallback.")

    return build_template_insight(context), "template"


async def generate_insight(
    prompt: str,
    context: Any | None = None,
) -> str:
    """Generate an insight text. Tests should mock provider helpers, never real APIs."""
    text, _source = await generate_insight_with_source(prompt, context=context)
    return text
