"""
tests/test_llm_client.py — Mocked tests for LLM insight client.
"""
from __future__ import annotations

import asyncio

import pytest

from backend.insights import llm_client


@pytest.fixture(autouse=True)
def _fast_retries(monkeypatch):
    monkeypatch.setattr(llm_client, "BACKOFF_SECONDS", (0, 0, 0))


def _context():
    return {
        "province_id": 1,
        "province_name": "Hà Nội",
        "current": {"aqi": 120, "pm2_5": 45},
        "anomaly": {"score": 0.4, "label": "NORMAL"},
        "forecast": {"values": [120] * 12},
    }


@pytest.mark.asyncio
async def test_gemini_success_returns_gemini_text(monkeypatch):
    monkeypatch.setattr(llm_client.settings, "GEMINI_API_KEY", "gemini-key")
    monkeypatch.setattr(llm_client.settings, "LLM_API_KEY", "")
    monkeypatch.setattr(llm_client.settings, "OPENAI_API_KEY", "openai-key")
    monkeypatch.setattr(
        llm_client,
        "_call_gemini_once",
        lambda *args: "(1) Hiện trạng: Gemini insight.",
    )

    text, source = await llm_client.generate_insight_with_source("prompt", _context())

    assert source == "gemini"
    assert "Gemini insight" in text


@pytest.mark.asyncio
async def test_gemini_failure_falls_back_to_openai(monkeypatch):
    monkeypatch.setattr(llm_client.settings, "GEMINI_API_KEY", "gemini-key")
    monkeypatch.setattr(llm_client.settings, "LLM_API_KEY", "")
    monkeypatch.setattr(llm_client.settings, "OPENAI_API_KEY", "openai-key")
    monkeypatch.setattr(
        llm_client,
        "_call_gemini_once",
        lambda *args: (_ for _ in ()).throw(RuntimeError("gemini down")),
    )
    monkeypatch.setattr(
        llm_client,
        "_call_openai_once",
        lambda *args: "(1) Hiện trạng: OpenAI fallback.",
    )

    text, source = await llm_client.generate_insight_with_source("prompt", _context())

    assert source == "openai"
    assert "OpenAI fallback" in text


@pytest.mark.asyncio
async def test_all_providers_fail_returns_template(monkeypatch):
    monkeypatch.setattr(llm_client.settings, "GEMINI_API_KEY", "gemini-key")
    monkeypatch.setattr(llm_client.settings, "LLM_API_KEY", "")
    monkeypatch.setattr(llm_client.settings, "OPENAI_API_KEY", "openai-key")
    monkeypatch.setattr(
        llm_client,
        "_call_gemini_once",
        lambda *args: (_ for _ in ()).throw(RuntimeError("gemini down")),
    )
    monkeypatch.setattr(
        llm_client,
        "_call_openai_once",
        lambda *args: (_ for _ in ()).throw(RuntimeError("openai down")),
    )

    text, source = await llm_client.generate_insight_with_source("prompt", _context())

    assert source == "template"
    assert "(1) Hiện trạng" in text


@pytest.mark.asyncio
async def test_timeout_returns_template(monkeypatch):
    monkeypatch.setattr(llm_client.settings, "GEMINI_API_KEY", "gemini-key")
    monkeypatch.setattr(llm_client.settings, "LLM_API_KEY", "")
    monkeypatch.setattr(llm_client.settings, "OPENAI_API_KEY", "")
    monkeypatch.setattr(llm_client.settings, "LLM_TIMEOUT", 0.01)

    def slow_provider(*args):
        import time

        time.sleep(0.1)
        return "too late"

    monkeypatch.setattr(llm_client, "_call_gemini_once", slow_provider)

    text, source = await llm_client.generate_insight_with_source("prompt", _context())

    assert source == "template"
    assert "(1) Hiện trạng" in text
