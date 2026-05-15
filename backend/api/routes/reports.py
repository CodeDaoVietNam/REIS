from __future__ import annotations

import logging
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

import asyncpg
from fastapi import APIRouter, HTTPException, Query, Request, Response
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from backend.api.db import get_pool
from backend.api.inference_cache import get_cached_inference
from backend.api.rate_limit import general_limiter
from backend.api.routes.provinces import (
    ALLOWED_COMPARE_METRICS,
    _is_anomaly_payload_alert,
    _radar_from_reading,
    fetch_current_reading,
    fetch_history,
    province_meta,
)
from backend.insights.insight_cache import get_or_create_insight
from backend.models.predict import DEFAULT_ANOMALY, DEFAULT_FORECAST

logger = logging.getLogger(__name__)

router = APIRouter(tags=["reports"])

FONT_NAME = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _register_fonts() -> tuple[str, str]:
    regular = Path(FONT_PATHS[0])
    bold = Path(FONT_PATHS[1])
    if regular.exists() and bold.exists():
        try:
            pdfmetrics.registerFont(TTFont("DejaVuSans", str(regular)))
            pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", str(bold)))
            return "DejaVuSans", "DejaVuSans-Bold"
        except Exception as exc:
            logger.debug("PDF font registration fallback: %s", exc)
    return FONT_NAME, FONT_BOLD


BASE_FONT, BASE_FONT_BOLD = _register_fonts()


def _styles() -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReisTitle",
            parent=sample["Title"],
            fontName=BASE_FONT_BOLD,
            fontSize=22,
            leading=27,
            textColor=colors.HexColor("#143f2d"),
            spaceAfter=12,
        ),
        "h2": ParagraphStyle(
            "ReisH2",
            parent=sample["Heading2"],
            fontName=BASE_FONT_BOLD,
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#143f2d"),
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "ReisBody",
            parent=sample["BodyText"],
            fontName=BASE_FONT,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1f2a24"),
        ),
        "small": ParagraphStyle(
            "ReisSmall",
            parent=sample["BodyText"],
            fontName=BASE_FONT,
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#56635b"),
        ),
    }


def _pdf_response(content: bytes, filename: str) -> Response:
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _safe_float(value: Any, fallback: float = 0.0) -> float:
    try:
        if value is None:
            return fallback
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _fmt(value: Any, digits: int = 1, suffix: str = "") -> str:
    if value is None:
        return "N/A"
    number = _safe_float(value)
    if digits == 0:
        return f"{number:.0f}{suffix}"
    return f"{number:.{digits}f}{suffix}"


def _aqi_label(aqi: Any) -> str:
    value = _safe_float(aqi)
    if value <= 50:
        return "Good"
    if value <= 100:
        return "Moderate"
    if value <= 150:
        return "Unhealthy for sensitive groups"
    if value <= 200:
        return "Unhealthy"
    if value <= 300:
        return "Very unhealthy"
    return "Hazardous"


def _now_label() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def _table(data: list[list[Any]], widths: list[float] | None = None) -> Table:
    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), BASE_FONT),
                ("FONTNAME", (0, 0), (-1, 0), BASE_FONT_BOLD),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#143f2d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f4f8f5")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cdd8d0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


async def _province_payload(
    pool: asyncpg.Pool | None,
    province_id: int,
    hours: int,
) -> dict[str, Any]:
    meta = province_meta(province_id)
    current = await fetch_current_reading(pool, province_id)
    history = await fetch_history(pool, province_id, hours=hours) if current is not None else []

    inference = {"anomaly": DEFAULT_ANOMALY, "forecast": DEFAULT_FORECAST}
    inference_source = "default"
    if current is not None:
        try:
            inference, inference_source = await get_cached_inference(province_id, pool=pool)
        except Exception as exc:
            logger.warning("Report inference fallback for province %s: %s", province_id, exc)
            inference_source = "fallback"

    anomaly = inference.get("anomaly", DEFAULT_ANOMALY)
    if current is not None and inference_source != "default":
        current = {
            **current,
            "anomaly_score": _safe_float(anomaly.get("score")),
            "is_anomaly": _is_anomaly_payload_alert(anomaly),
        }

    if current is None:
        insight = {
            "summary": "No current reading is available for this province.",
            "health_advice": "Start the realtime pipeline or run historical backfill before using this report operationally.",
            "recommended_actions": ["Verify database connectivity", "Run collector and consumer", "Refresh the report after data arrives"],
            "risk_level": "unknown",
        }
    else:
        try:
            insight = await get_or_create_insight(
                province_id=province_id,
                current=current,
                anomaly=anomaly,
                forecast=inference.get("forecast", DEFAULT_FORECAST),
            )
        except Exception as exc:
            logger.warning("Report insight fallback for province %s: %s", province_id, exc)
            insight = {
                "summary": "No insight available.",
                "health_advice": "Check data pipeline and retry when API data is available.",
                "recommended_actions": ["Verify database connectivity", "Review latest AQI readings"],
                "risk_level": "unknown",
            }

    return {
        "province": meta,
        "current": current,
        "history": history,
        "anomaly": anomaly,
        "forecast": inference.get("forecast", DEFAULT_FORECAST),
        "inference_source": inference_source,
        "insight": insight,
    }


def _build_province_report(payload: dict[str, Any], hours: int) -> bytes:
    styles = _styles()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
        title="REIS Province Report",
    )
    province = payload["province"]
    current = payload["current"] or {}
    anomaly = payload["anomaly"]
    forecast = payload["forecast"]
    insight = payload["insight"]
    story: list[Any] = []

    story.append(Paragraph(f"REIS Province Air Quality Report - {province['name_vi']}", styles["title"]))
    story.append(Paragraph(f"Generated: {_now_label()} | Window: last {hours} hours | Source: FastAPI + TimescaleDB + ML cache", styles["small"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("1. Executive Summary", styles["h2"]))
    summary = (
        f"Current AQI is {_fmt(current.get('aqi'), 0)} ({_aqi_label(current.get('aqi'))}). "
        f"PM2.5 is {_fmt(current.get('pm2_5'), 1, ' ug/m3')}. "
        f"AI anomaly score is {_fmt(anomaly.get('score'), 2)} with label {anomaly.get('label', 'N/A')}. "
        f"Forecast model: {forecast.get('model_family', 'N/A')}."
    )
    story.append(Paragraph(summary, styles["body"]))

    story.append(Paragraph("2. Current Reading", styles["h2"]))
    story.append(
        _table(
            [
                ["Metric", "Value"],
                ["Updated at", current.get("time", "N/A")],
                ["AQI", _fmt(current.get("aqi"), 0)],
                ["AQI level", _aqi_label(current.get("aqi"))],
                ["PM2.5", _fmt(current.get("pm2_5"), 1, " ug/m3")],
                ["PM10", _fmt(current.get("pm10"), 1, " ug/m3")],
                ["Temperature", _fmt(current.get("temperature"), 1, " C")],
                ["Humidity", _fmt(current.get("humidity"), 0, "%")],
                ["Wind speed", _fmt(current.get("wind_speed"), 1, " km/h")],
            ],
            [5 * cm, 11 * cm],
        )
    )

    story.append(Paragraph("3. AI Anomaly Analysis", styles["h2"]))
    story.append(
        _table(
            [
                ["Field", "Value"],
                ["Score", _fmt(anomaly.get("score"), 2)],
                ["Label", anomaly.get("label", "N/A")],
                ["Strict alert", str(bool(anomaly.get("strict_alert")))],
                ["Inference source", payload.get("inference_source", "N/A")],
            ],
            [5 * cm, 11 * cm],
        )
    )

    story.append(Paragraph("4. Forecast 12h", styles["h2"]))
    forecast_rows = [["Step", "Forecast AQI", "Lower", "Upper"]]
    values = forecast.get("values") or []
    lower = forecast.get("lower") or []
    upper = forecast.get("upper") or []
    for index, value in enumerate(values[:12]):
        forecast_rows.append([
            f"+{index + 1}h",
            _fmt(value, 1),
            _fmt(lower[index] if index < len(lower) else None, 1),
            _fmt(upper[index] if index < len(upper) else None, 1),
        ])
    story.append(_table(forecast_rows, [3 * cm, 4 * cm, 4 * cm, 4 * cm]))

    story.append(Paragraph("5. Insight & Recommendations", styles["h2"]))
    insight_text = insight.get("text") or insight.get("summary") or "No narrative insight available."
    story.append(Paragraph(str(insight_text), styles["body"]))
    advice = insight.get("health_advice")
    if advice:
        story.append(Paragraph(str(advice), styles["body"]))
    actions = insight.get("recommended_actions") or insight.get("recommendations") or []
    if actions:
        action_rows = [["Recommended actions"], *[[str(item)] for item in actions[:5]]]
        story.append(_table(action_rows, [16 * cm]))

    story.append(Paragraph("6. Historical Table", styles["h2"]))
    history_rows = [["Time", "AQI", "PM2.5", "Temp", "Wind", "AI score"]]
    for row in payload["history"][-24:]:
        history_rows.append([
            str(row.get("time", "N/A")),
            _fmt(row.get("aqi"), 0),
            _fmt(row.get("pm2_5"), 1),
            _fmt(row.get("temperature"), 1),
            _fmt(row.get("wind_speed"), 1),
            _fmt(row.get("anomaly_score"), 2) if row.get("anomaly_score") is not None else "N/A",
        ])
    story.append(_table(history_rows, [5.2 * cm, 2 * cm, 2.3 * cm, 2 * cm, 2 * cm, 2.3 * cm]))

    doc.build(story)
    return buffer.getvalue()


def _build_compare_report(payload: dict[str, Any]) -> bytes:
    styles = _styles()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1.1 * cm,
        leftMargin=1.1 * cm,
        topMargin=1.1 * cm,
        bottomMargin=1.1 * cm,
        title="REIS Compare Report",
    )
    story: list[Any] = []
    provinces = payload["provinces"]

    story.append(Paragraph("REIS Multi-Province Comparison Report", styles["title"]))
    story.append(Paragraph(f"Generated: {_now_label()} | Days: {payload['days']} | Metric: {payload['metric']}", styles["small"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("1. Executive Comparison", styles["h2"]))
    summary_rows = [["Province", "AQI", "AQI level", "PM2.5", "Temp", "Wind", "AI score", "AI label"]]
    for item in provinces:
        current = item["current"] or {}
        anomaly = item["anomaly"]
        summary_rows.append([
            item["province"]["name_vi"],
            _fmt(current.get("aqi"), 0),
            _aqi_label(current.get("aqi")),
            _fmt(current.get("pm2_5"), 1),
            _fmt(current.get("temperature"), 1),
            _fmt(current.get("wind_speed"), 1),
            _fmt(anomaly.get("score"), 2),
            anomaly.get("label", "N/A"),
        ])
    story.append(_table(summary_rows))

    story.append(Paragraph("2. Radar Metrics", styles["h2"]))
    radar_rows = [["Province", "AQI", "PM2.5", "PM10", "NO2", "Ozone", "UV"]]
    for item in provinces:
        radar = item["radar"]
        radar_rows.append([
            item["province"]["name_vi"],
            _fmt(radar.get("aqi"), 0),
            _fmt(radar.get("pm2_5"), 1),
            _fmt(radar.get("pm10"), 1),
            _fmt(radar.get("no2"), 1),
            _fmt(radar.get("ozone"), 1),
            _fmt(radar.get("uv_index"), 1),
        ])
    story.append(_table(radar_rows))

    story.append(PageBreak())
    story.append(Paragraph("3. Historical Samples", styles["h2"]))
    for item in provinces:
        story.append(Paragraph(item["province"]["name_vi"], styles["h2"]))
        rows = [["Time", "AQI", "PM2.5", "Temp", "Wind"]]
        for row in item["history"][-12:]:
            rows.append([
                str(row.get("time", "N/A")),
                _fmt(row.get("aqi"), 0),
                _fmt(row.get("pm2_5"), 1),
                _fmt(row.get("temperature"), 1),
                _fmt(row.get("wind_speed"), 1),
            ])
        story.append(_table(rows))
        story.append(Spacer(1, 8))

    doc.build(story)
    return buffer.getvalue()


@router.get("/api/report/province/{province_id}.pdf")
async def get_province_report(
    province_id: int,
    request: Request,
    hours: int = Query(default=48, ge=1, le=24 * 60),
) -> Response:
    general_limiter.check(request)
    pool = get_pool(request)
    payload = await _province_payload(pool, province_id, hours)
    content = _build_province_report(payload, hours)
    filename = f"reis-province-{province_id}-report.pdf"
    return _pdf_response(content, filename)


@router.get("/api/report/compare.pdf")
async def get_compare_report(
    request: Request,
    province_ids: str = Query(default="1,2,4"),
    days: int = Query(default=7, ge=1, le=60),
    metric: str = Query(default="aqi"),
) -> Response:
    general_limiter.check(request)
    if metric not in ALLOWED_COMPARE_METRICS:
        raise HTTPException(status_code=400, detail=f"Unsupported metric: {metric}")

    try:
        ids = [int(item.strip()) for item in province_ids.split(",") if item.strip()]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="province_ids must be comma-separated integers") from exc

    unique_ids = list(dict.fromkeys(ids))[:6]
    if not unique_ids:
        raise HTTPException(status_code=400, detail="At least one province id is required")

    pool = get_pool(request)
    provinces: list[dict[str, Any]] = []
    for province_id in unique_ids:
        payload = await _province_payload(pool, province_id, hours=days * 24)
        current = payload["current"]
        provinces.append(
            {
                "province": payload["province"],
                "current": current,
                "history": payload["history"],
                "anomaly": {
                    "score": _safe_float(payload["anomaly"].get("score")),
                    "label": payload["anomaly"].get("label") or "NORMAL",
                    "strict_alert": bool(payload["anomaly"].get("strict_alert")),
                },
                "radar": _radar_from_reading(current),
            }
        )

    content = _build_compare_report({"metric": metric, "days": days, "provinces": provinces})
    return _pdf_response(content, "reis-compare-report.pdf")
