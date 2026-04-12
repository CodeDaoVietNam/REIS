"""
setup_db.py — Initialize TimescaleDB schema and seed provinces.

Usage:
    python scripts/setup_db.py [--drop] [--seed]

Options:
    --drop   Drop existing tables before recreating (useful for dev reset).
    --seed   Seed the provinces table from init-db.sql (default: True).
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

import asyncpg

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────
DB_HOST = "localhost"
DB_PORT = 5432
DB_USER = "reis"
DB_PASSWORD = "reis_secret"
DB_NAME = "reis_db"

SCHEMA_SQL = Path(__file__).parent / "init-db.sql"


async def wait_for_db(timeout: int = 30) -> asyncpg.Connection:
    """Block until TimescaleDB is ready to accept connections."""
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        try:
            conn = await asyncpg.connect(
                host=DB_HOST, port=DB_PORT,
                user=DB_USER, password=DB_PASSWORD, database=DB_NAME,
            )
            logger.info("Connected to TimescaleDB ✅")
            return conn
        except (ConnectionRefusedError, asyncpg.InvalidCatalogNameError):
            logger.info("Waiting for TimescaleDB...")
            await asyncio.sleep(2)
    raise RuntimeError("TimescaleDB did not become available within timeout.")


async def run_schema(conn: asyncpg.Connection, drop: bool) -> None:
    """Execute init-db.sql, optionally dropping tables first."""
    schema = SCHEMA_SQL.read_text(encoding="utf-8")

    if drop:
        logger.warning("Dropping existing tables...")
        await conn.execute("DROP TABLE IF EXISTS env_readings CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS provinces CASCADE;")
        await conn.execute("DROP EXTENSION IF EXISTS timescaledb CASCADE;")

    # Execute in a transaction
    async with conn.transaction():
        # Enable timescaledb (ignore errors if already enabled)
        try:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
        except asyncpg.DuplicateObjectError:
            pass

        # Split and execute statements one by one (CREATE TABLE / SELECT can't run together)
        statements = [
            s.strip() for s in schema.split(";")
            if s.strip() and not s.strip().startswith("--")
        ]
        for stmt in statements:
            if stmt.upper().startswith("SELECT create_hypertable"):
                # Extract the function call as-is (TimescaleDB special syntax)
                await conn.execute(stmt)
            elif stmt.upper().startswith("INSERT INTO provinces"):
                # upsert: ON CONFLICT DO NOTHING is fine
                await conn.execute(stmt)
            elif stmt.upper().startswith("CREATE"):
                await conn.execute(stmt)
            elif stmt.upper().startswith("CREATE INDEX"):
                await conn.execute(stmt)

    logger.info("Schema applied successfully.")


async def verify(conn: asyncpg.Connection) -> None:
    """Sanity checks after schema creation."""
    province_count = await conn.fetchval("SELECT COUNT(*) FROM provinces")
    logger.info(f"provinces table: {province_count} rows")

    is_hypertable = await conn.fetchval(
        "SELECT 1 FROM timescaledb_information.hypertables "
        "WHERE hypertable_name = 'env_readings'"
    )
    logger.info(f"env_readings hypertable: {'✅' if is_hypertable else '❌ (not a hypertable)'}")


async def main(drop: bool, seed: bool) -> None:
    conn = await wait_for_db()
    try:
        await run_schema(conn, drop=drop)
        if seed:
            await verify(conn)
        else:
            logger.info("Skipped seed (--no-seed).")
    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize REIS TimescaleDB schema")
    parser.add_argument("--drop", action="store_true", help="Drop tables before recreating")
    parser.add_argument("--no-seed", dest="seed", action="store_false", default=True,
                        help="Skip seeding provinces")
    args = parser.parse_args()

    asyncio.run(main(drop=args.drop, seed=args.seed))