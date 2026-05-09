"""
tests/test_prompt_builder.py — Tests for Vietnamese insight prompts.
"""
from __future__ import annotations

from backend.insights.prompt_builder import build_prompt, build_template_insight, summarize_forecast


def _context():
    return {
        "province_id": 1,
        "province_name": "Hà Nội",
        "current": {
            "time": "2026-05-10T08:00:00+07:00",
            "aqi": 121,
            "pm2_5": 45.5,
            "pm10": 70.2,
            "temperature": 31.0,
            "humidity": 72.0,
            "wind_speed": 3.5,
        },
        "anomaly": {
            "score": 0.58,
            "label": "ANOMALY",
            "strict_alert": True,
        },
        "forecast": {
            "values": [120, 122, 126, 130, 134, 138, 140, 142, 145, 148, 150, 152],
            "lower": [115] * 12,
            "upper": [160] * 12,
            "model_family": "lstm",
        },
    }


def test_build_prompt_contains_required_context_and_sections():
    prompt = build_prompt(_context())

    assert "Hà Nội" in prompt
    assert "AQI: 121" in prompt
    assert "PM2.5: 45.5" in prompt
    assert "Anomaly score: 0.580" in prompt
    assert "Dự báo AQI 12h tới" in prompt
    assert "(1) Hiện trạng" in prompt
    assert "(2) Nguyên nhân" in prompt
    assert "(3) Dự báo" in prompt
    assert "(4) Khuyến nghị" in prompt
    assert "Không bịa nguồn phát thải" in prompt


def test_template_fallback_is_short_and_handles_missing_fields():
    text = build_template_insight({"province_id": 99, "current": {"aqi": 80}})

    assert "(1) Hiện trạng" in text
    assert "(4) Khuyến nghị" in text
    assert len(text.split()) <= 150


def test_summarize_forecast_trend_detection():
    increasing = summarize_forecast({"values": [80, 82, 85, 90]}, current_aqi=80)
    stable = summarize_forecast({"values": [80, 81, 82]}, current_aqi=80)
    decreasing = summarize_forecast({"values": [90, 86, 82]}, current_aqi=90)

    assert increasing["trend"] == "tăng"
    assert stable["trend"] == "ổn định"
    assert decreasing["trend"] == "giảm"
