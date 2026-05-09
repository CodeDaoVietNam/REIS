"""
Insight generation package for REIS.
"""

from backend.insights.insight_cache import aqi_bucket, build_cache_key, get_or_create_insight
from backend.insights.llm_client import generate_insight, generate_insight_with_source
from backend.insights.prompt_builder import InsightContext, build_prompt, build_template_insight

__all__ = [
    "InsightContext",
    "aqi_bucket",
    "build_cache_key",
    "build_prompt",
    "build_template_insight",
    "generate_insight",
    "generate_insight_with_source",
    "get_or_create_insight",
]
