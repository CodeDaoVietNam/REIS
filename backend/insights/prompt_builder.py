"""
prompt_builder.py — Vietnamese LLM prompts and fallback insights.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd


MAX_INSIGHT_WORDS = 150


@dataclass(slots=True)
class InsightContext:
    province_id: int
    province_name: str
    current: dict[str, Any] = field(default_factory=dict)
    anomaly: dict[str, Any] = field(default_factory=dict)
    forecast: dict[str, Any] = field(default_factory=dict)


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except TypeError:
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _fmt(value: Any, digits: int = 1, default: str = "N/A") -> str:
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except TypeError:
        pass
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _word_limit(text: str, max_words: int = MAX_INSIGHT_WORDS) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip(" ,.;:") + "..."


def normalize_context(context: InsightContext | dict[str, Any]) -> InsightContext:
    if isinstance(context, InsightContext):
        return context

    current = dict(context.get("current") or {})
    anomaly = dict(context.get("anomaly") or {})
    forecast = dict(context.get("forecast") or {})

    province_id = int(context.get("province_id") or current.get("province_id") or 0)
    province_name = (
        context.get("province_name")
        or current.get("province_name")
        or current.get("name_vi")
        or f"Tỉnh {province_id}"
    )
    return InsightContext(
        province_id=province_id,
        province_name=str(province_name),
        current=current,
        anomaly=anomaly,
        forecast=forecast,
    )


def summarize_forecast(forecast: dict[str, Any], current_aqi: float | None = None) -> dict[str, Any]:
    values = forecast.get("values") or []
    arr = np.asarray(values, dtype=np.float32) if values else np.asarray([], dtype=np.float32)
    if arr.size == 0:
        return {
            "avg": None,
            "max": None,
            "trend": "chưa đủ dữ liệu",
            "model_family": forecast.get("model_family", "unknown"),
        }

    avg = float(np.nanmean(arr))
    max_value = float(np.nanmax(arr))
    start = float(current_aqi) if current_aqi is not None else float(arr[0])
    end = float(arr[-1])
    delta = end - start
    if delta >= 5:
        trend = "tăng"
    elif delta <= -5:
        trend = "giảm"
    else:
        trend = "ổn định"

    return {
        "avg": avg,
        "max": max_value,
        "trend": trend,
        "model_family": forecast.get("model_family", "unknown"),
    }


def build_prompt(context: InsightContext | dict[str, Any]) -> str:
    ctx = normalize_context(context)
    current = ctx.current
    anomaly = ctx.anomaly
    forecast_summary = summarize_forecast(ctx.forecast, _to_float(current.get("aqi")))

    return f"""
Bạn là trợ lý phân tích chất lượng không khí cho hệ thống REIS.
Hãy viết insight tiếng Việt dưới {MAX_INSIGHT_WORDS} từ cho người dân và dashboard vận hành.

Dữ liệu hiện tại:
- Tỉnh/thành: {ctx.province_name} (province_id={ctx.province_id})
- Thời điểm: {current.get("time", "N/A")}
- AQI: {_fmt(current.get("aqi"), 0)}
- PM2.5: {_fmt(current.get("pm2_5"))}
- PM10: {_fmt(current.get("pm10"))}
- Nhiệt độ: {_fmt(current.get("temperature"))}°C
- Độ ẩm: {_fmt(current.get("humidity"))}%
- Gió: {_fmt(current.get("wind_speed"))} m/s
- Anomaly score: {_fmt(anomaly.get("score"), 3)}
- Nhãn anomaly: {anomaly.get("label", "NORMAL")}
- Strict alert: {bool(anomaly.get("strict_alert", False))}
- Dự báo AQI 12h tới: trung bình {_fmt(forecast_summary["avg"])}, cao nhất {_fmt(forecast_summary["max"])}, xu hướng {forecast_summary["trend"]}, model {forecast_summary["model_family"]}.

Yêu cầu trả lời đúng 4 phần, không dùng markdown bảng:
(1) Hiện trạng
(2) Nguyên nhân
(3) Dự báo
(4) Khuyến nghị

Không bịa nguồn phát thải cụ thể. Khi nói nguyên nhân, dùng ngôn ngữ thận trọng như "có thể do" hoặc "cần kiểm chứng thêm".
""".strip()


def build_template_insight(context: InsightContext | dict[str, Any] | None = None) -> str:
    if context is None:
        return (
            "(1) Hiện trạng: Chưa đủ dữ liệu để tạo nhận định chi tiết. "
            "(2) Nguyên nhân: Cần kiểm chứng thêm từ dữ liệu quan trắc. "
            "(3) Dự báo: Chưa có dự báo đáng tin cậy trong 12 giờ tới. "
            "(4) Khuyến nghị: Tiếp tục theo dõi chỉ số AQI và hạn chế hoạt động ngoài trời nếu chất lượng không khí xấu."
        )

    ctx = normalize_context(context)
    current = ctx.current
    anomaly = ctx.anomaly
    forecast_summary = summarize_forecast(ctx.forecast, _to_float(current.get("aqi")))

    aqi = _to_float(current.get("aqi"))
    pm25 = _to_float(current.get("pm2_5"))
    score = _to_float(anomaly.get("score"))
    alert = bool(anomaly.get("strict_alert", False))

    if alert or aqi >= 150 or pm25 >= 100:
        status = "chất lượng không khí đang ở mức đáng chú ý"
        advice = "người nhạy cảm nên hạn chế ra ngoài và theo dõi cập nhật mới"
    elif aqi >= 100:
        status = "chất lượng không khí có dấu hiệu suy giảm"
        advice = "nên giảm hoạt động ngoài trời kéo dài, nhất là với trẻ em và người có bệnh hô hấp"
    else:
        status = "chất lượng không khí tương đối ổn định"
        advice = "có thể sinh hoạt bình thường nhưng vẫn nên theo dõi nếu AQI tăng"

    text = (
        f"(1) Hiện trạng: {ctx.province_name} hiện có AQI {_fmt(aqi, 0)}, "
        f"PM2.5 {_fmt(pm25)}, {status}; anomaly score {_fmt(score, 2)}. "
        "(2) Nguyên nhân: Có thể do biến động thời tiết, giao thông hoặc nguồn phát thải cục bộ; cần kiểm chứng thêm. "
        f"(3) Dự báo: AQI 12 giờ tới dự kiến {forecast_summary['trend']}, "
        f"trung bình {_fmt(forecast_summary['avg'])}, cao nhất {_fmt(forecast_summary['max'])}. "
        f"(4) Khuyến nghị: {advice}."
    )
    return _word_limit(text)


def build_context_from_inference(
    province_id: int,
    current: dict[str, Any],
    anomaly: dict[str, Any],
    forecast: dict[str, Any],
) -> InsightContext:
    province_name = current.get("province_name") or current.get("name_vi") or f"Tỉnh {province_id}"
    if "time" not in current:
        current = dict(current)
        current["time"] = datetime.now().isoformat(timespec="seconds")
    return InsightContext(
        province_id=province_id,
        province_name=str(province_name),
        current=dict(current),
        anomaly=dict(anomaly or {}),
        forecast=dict(forecast or {}),
    )
