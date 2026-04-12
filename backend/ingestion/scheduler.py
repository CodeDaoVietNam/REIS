"""
scheduler.py — APScheduler orchestration: fetch → validate → publish.

Luồng hoạt động:
    1. Chạy collect_and_publish() NGAY khi start (immediate first cycle)
    2. Sau đó lặp lại mỗi 15 phút
    3. Nhận SIGTERM → graceful shutdown (đợi job đang chạy xong rồi mới exit)

Chạy độc lập:
    python backend/ingestion/scheduler.py
Chạy như module:
    from ingestion.scheduler import main
"""
from __future__ import annotations

import asyncio
import logging
import signal
import sys
from pathlib import Path

# ── Add project root to sys.path for absolute imports ──────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

from backend.ingestion.collector import collect_all_provinces
from backend.ingestion.producer import publish_records, close as close_producer

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Scheduler ───────────────────────────────────────────────────────────────

scheduler = AsyncIOScheduler(timezone="Asia/Ho_Chi_Minh")


async def collect_and_publish() -> None:
    """
    Một cycle hoàn chỉnh: fetch → validate → publish.

    Error handling:
        - Collector/Producer lỗi → log ERROR, KHÔNG raise
        - Scheduler tiếp tục cycle tiếp theo (không crash)
        - Mục tiêu: pipeline phải chạy liên tục 24/7
    """
    logger.info("=== Collection cycle started ===")
    try:
        # 1. Fetch raw data từ Open-Meteo
        records = await collect_all_provinces()
        logger.info("Fetched %d raw records from Open-Meteo", len(records))

        # 2. Validate + publish lên Kafka (producer.py xử lý cả 2)
        #    Valid → Kafka | Invalid → Redis DLQ
        stats = await publish_records(records)
        logger.info(
            "Cycle complete: published=%d, dlq=%d",
            stats.get("published", 0),
            stats.get("dlq", 0),
        )

    except Exception as exc:
        logger.error("Collection cycle FAILED: %s", exc, exc_info=True)
        # KHÔNG raise — scheduler tiếp tục, retry cycle tiếp theo


def _job_event_listener(event) -> None:
    """Log kết quả mỗi lần job chạy (thành công hoặc thất bại)."""
    job = scheduler.get_job(event.job_id)
    job_name = job.name if job else event.job_id

    if event.exception:
        logger.error("Job '%s' FAILED: %s", job_name, event.exception)
    else:
        logger.info("Job '%s' SUCCESS at %s", job_name, event.scheduled_run_time)


def _sigterm_handler(signum, frame) -> None:
    """SIGTERM → graceful shutdown."""
    logger.info("SIGTERM received — initiating graceful shutdown...")
    shutdown_event.set()


# ── Graceful shutdown via asyncio.Event ─────────────────────────────────────

shutdown_event = asyncio.Event()


async def main() -> None:
    """
    Entry point chính: khởi tạo scheduler và chạy vĩnh viễn.

    Đăng ký SIGTERM handler để Docker/Kubernetes có thể stop container
    mà không làm mất job đang chạy.
    """
    # Đăng ký SIGTERM handler (Docker sends SIGTERM on `docker stop`)
    signal.signal(signal.SIGTERM, _sigterm_handler)

    # ── Đăng ký job ──────────────────────────────────────────────────────
    scheduler.add_job(
        collect_and_publish,
        trigger="interval",
        minutes=15,
        id="collect_and_publish",
        name="Collect and publish env readings",
        misfire_grace_time=300,   # Cho phép backlog tối đa 5 phút
        max_instances=1,           # Không chạy 2 cycle cùng lúc
        coalesce=True,            # Missed cycle → chỉ bù 1 lần (không spam)
    )
    scheduler.add_listener(
        _job_event_listener,
        EVENT_JOB_ERROR | EVENT_JOB_EXECUTED,
    )

    # ── Start scheduler ──────────────────────────────────────────────────
    scheduler.start()
    logger.info("Scheduler started | Interval: 15 minutes | Timezone: Asia/Ho_Chi_Minh")

    # ── Chạy 1 cycle NGAY LẬP TỨC khi khởi động ────────────────────────
    # Docs requirement: "Chạy 1 cycle ngay lập tức khi khởi động"
    logger.info("Running immediate first cycle...")
    await collect_and_publish()

    # ── Giữ event loop chạy ──────────────────────────────────────────────
    try:
        await shutdown_event.wait()   # Block cho đến khi SIGTERM
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        logger.info("Shutting down scheduler...")
        scheduler.shutdown(wait=True)   # Đợi job đang chạy xong
        await close_producer()         # Đóng Kafka + Redis connections
        logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
