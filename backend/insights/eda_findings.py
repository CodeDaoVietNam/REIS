from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import asyncpg

from backend.config.constants import PROVINCES_BY_ID

WARNING_AQI_THRESHOLD = 150

REGION_LABELS = {
    "Bac": "Miền Bắc",
    "Trung": "Miền Trung",
    "Nam": "Miền Nam",
}

BASELINE_FINDINGS: list[dict[str, Any]] = [
    {
        "id": "daily-weekly-cycle",
        "title": "AQI tăng theo chu kỳ chiều tối",
        "question": "Xu hướng chính của dữ liệu là gì?",
        "claim": "AQI thường tăng rõ vào khung 17h-20h và biến động theo ngày trong tuần.",
        "evidence": "EDA cho thấy peak quanh giờ chiều tối; thứ Ba là ngày ô nhiễm nổi bật, thứ Bảy thường sạch hơn.",
        "interpretation": "Mẫu này phù hợp với tác động của giao thông, hoạt động đô thị và điều kiện khuếch tán khí quyển cuối ngày.",
        "practical_value": "Người dùng nên ưu tiên lịch thể thao/di chuyển ngoài trời ngoài khung giờ rủi ro, nhất là nhóm nhạy cảm.",
        "confidence": "medium_high",
    },
    {
        "id": "north-south-split",
        "title": "Miền Bắc là cụm ô nhiễm nổi bật",
        "question": "Có pattern nào đáng chú ý?",
        "claim": "Dữ liệu EDA cho thấy miền Bắc có mặt bằng AQI cao hơn miền Nam, đặc biệt quanh Hà Nội và các tỉnh vệ tinh.",
        "evidence": "Notebook EDA ghi nhận median AQI miền Bắc xấp xỉ 120, gần gấp đôi miền Nam khoảng 70.",
        "interpretation": "Đây có thể là tổ hợp của mật độ đô thị, công nghiệp, giao thông và điều kiện khí tượng giữ bụi.",
        "practical_value": "Dashboard cần ưu tiên cảnh báo vùng thay vì chỉ cảnh báo từng tỉnh rời rạc.",
        "confidence": "high",
    },
    {
        "id": "regional-crisis",
        "title": "Sự kiện AQI cao thường xuất hiện theo cụm vùng",
        "question": "Có pattern nào đáng chú ý?",
        "claim": "Các đợt AQI rất cao không chỉ là hiện tượng một tỉnh, mà có thể xuất hiện đồng thời trên nhiều tỉnh lân cận.",
        "evidence": "EDA phát hiện nhiều thời điểm AQI > 200 xảy ra theo cụm tỉnh trong cùng cửa sổ thời gian.",
        "interpretation": "Điều này gợi ý vai trò của khí tượng diện rộng hoặc nguồn phát thải vùng, không chỉ nguồn cục bộ.",
        "practical_value": "Alert Center nên phân biệt cảnh báo tỉnh đơn lẻ và cảnh báo có tính vùng.",
        "confidence": "medium_high",
    },
    {
        "id": "autoregression",
        "title": "AQI có tính nhớ theo thời gian",
        "question": "Có thể dự đoán hoặc giải thích điều gì?",
        "claim": "AQI hiện tại phụ thuộc mạnh vào các mốc trước đó, nhất là 1h và chu kỳ 24h.",
        "evidence": "EDA feature engineering cho thấy lag 1h, lag 3h, lag 6h và lag 24h là nhóm tín hiệu quan trọng.",
        "interpretation": "Ô nhiễm không đổi ngẫu nhiên từng điểm; nó có quán tính, nên forecast ngắn hạn có cơ sở kỹ thuật.",
        "practical_value": "Forecast 12h giúp người dùng chuẩn bị trước thay vì chỉ phản ứng khi AQI đã xấu.",
        "confidence": "high",
    },
    {
        "id": "hanoi-hotspot",
        "title": "Hà Nội là hotspot cần theo dõi sâu",
        "question": "Insight có giá trị thực tế gì?",
        "claim": "Hà Nội vừa có mức ô nhiễm cao, vừa có nhiều pattern bất thường hơn nhiều tỉnh khác.",
        "evidence": "EDA anomaly cho thấy Hà Nội là tỉnh có số anomaly nổi bật, khoảng gấp đôi nhóm đứng sau trong notebook.",
        "interpretation": "Một đô thị lớn có nhiều nguồn tác động chồng lên nhau, nên cần kết hợp AQI warning, anomaly và forecast.",
        "practical_value": "Người dùng ở Hà Nội nên theo dõi cả chỉ số hiện tại lẫn xu hướng dự báo trước khi ra quyết định.",
        "confidence": "medium_high",
    },
]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _round_or_none(value: float | None, digits: int = 1) -> float | None:
    if value is None:
        return None
    return round(value, digits)


async def _fetch_latest_rows(pool: asyncpg.Pool | None) -> list[dict[str, Any]]:
    if pool is None:
        return []

    rows = await pool.fetch(
        """
        SELECT DISTINCT ON (province_id)
            time, province_id, aqi, pm2_5, temperature, wind_speed,
            is_anomaly, anomaly_score
        FROM env_readings
        ORDER BY province_id, time DESC
        """
    )
    return [dict(row) for row in rows]


def _build_live_context(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "available": False,
            "latest_time": None,
            "province_count_with_data": 0,
            "aqi_warning_count": 0,
            "top_polluted": [],
            "regional_aqi": [],
            "hanoi": None,
        }

    enriched: list[dict[str, Any]] = []
    region_values: dict[str, list[float]] = {}
    for row in rows:
        province_id = int(row["province_id"])
        province = PROVINCES_BY_ID.get(province_id, {})
        aqi = _safe_float(row.get("aqi"))
        item = {
            "province_id": province_id,
            "name_vi": province.get("name_vi", f"Province {province_id}"),
            "region": province.get("region", "unknown"),
            "aqi": _round_or_none(aqi, 1),
            "pm2_5": _round_or_none(_safe_float(row.get("pm2_5")), 1),
            "time": row.get("time").isoformat() if hasattr(row.get("time"), "isoformat") else row.get("time"),
        }
        enriched.append(item)
        if aqi is not None:
            region_values.setdefault(item["region"], []).append(aqi)

    top_polluted = sorted(
        [item for item in enriched if item["aqi"] is not None],
        key=lambda item: item["aqi"],
        reverse=True,
    )[:10]
    regional_aqi = [
        {
            "region": region,
            "label": REGION_LABELS.get(region, region),
            "aqi_avg": round(sum(values) / len(values), 1),
            "province_count": len(values),
        }
        for region, values in sorted(region_values.items())
        if values
    ]

    return {
        "available": True,
        "latest_time": max((item["time"] for item in enriched if item["time"]), default=None),
        "province_count_with_data": len(enriched),
        "aqi_warning_count": sum(1 for item in enriched if (item["aqi"] or 0) >= WARNING_AQI_THRESHOLD),
        "top_polluted": top_polluted,
        "regional_aqi": regional_aqi,
        "hanoi": next((item for item in enriched if item["province_id"] == 1), None),
    }


def _with_live_evidence(findings: list[dict[str, Any]], context: dict[str, Any]) -> list[dict[str, Any]]:
    if not context["available"]:
        return [
            {
                **finding,
                "source": "EDA baseline",
            }
            for finding in findings
        ]

    by_id = {finding["id"]: dict(finding) for finding in findings}
    regional = {item["region"]: item for item in context["regional_aqi"]}
    top_names = ", ".join(item["name_vi"] for item in context["top_polluted"][:3]) or "N/A"
    hanoi = context.get("hanoi")

    if regional:
        north = regional.get("Bac", {}).get("aqi_avg")
        south = regional.get("Nam", {}).get("aqi_avg")
        if north is not None and south is not None:
            by_id["north-south-split"]["evidence"] = (
                f"EDA ghi nhận miền Bắc cao hơn miền Nam; live DB hiện có AQI trung bình "
                f"Miền Bắc {north}, Miền Nam {south}."
            )

    by_id["regional-crisis"]["evidence"] = (
        f"EDA phát hiện AQI cao theo cụm vùng; live DB hiện có "
        f"{context['aqi_warning_count']} tỉnh AQI >= {WARNING_AQI_THRESHOLD}. "
        f"Top tỉnh hiện tại: {top_names}."
    )

    if hanoi and hanoi.get("aqi") is not None:
        by_id["hanoi-hotspot"]["evidence"] = (
            f"EDA xem Hà Nội là hotspot; live DB mới nhất ghi nhận Hà Nội AQI {hanoi['aqi']} "
            f"và PM2.5 {hanoi.get('pm2_5', 'N/A')}."
        )

    return [{**finding, "source": "EDA + LIVE DB"} for finding in by_id.values()]


async def build_insight_summary_payload(pool: asyncpg.Pool | None) -> dict[str, Any]:
    """Build dashboard/report findings from EDA baseline plus optional live DB context."""
    try:
        rows = await _fetch_latest_rows(pool)
        context = _build_live_context(rows)
        source = "eda_live_hybrid" if context["available"] else "eda_baseline"
    except Exception:
        context = _build_live_context([])
        source = "eda_baseline"

    findings = _with_live_evidence(BASELINE_FINDINGS, context)
    return {
        "generated_at": _iso_now(),
        "source": source,
        "latest_time": context["latest_time"],
        "context": context,
        "findings": findings,
        "charts": {
            "top_polluted": context["top_polluted"],
            "regional_aqi": context["regional_aqi"],
        },
    }
