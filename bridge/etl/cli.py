"""CLI helpers for running the audit log ETL."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
from typing import Iterable, List, Optional

from .audit_log_etl import AuditLogETL, AuditLogETLConfig, EventDrivenAuditLogETL

logger = logging.getLogger(__name__)

_DEFAULT_MODE = "hybrid"
_DEFAULT_BATCH = 100
_DEFAULT_INTERVAL = 5.0
_DEFAULT_LOG_LEVEL = "INFO"

_SOURCE_DSN_ENV_ORDER: tuple[str, ...] = (
    "BRIDGE_SOURCE_DSN",
    "POSTGRES_DSN",
    "DATABASE_URL",
)
_TARGET_DSN_ENV_ORDER: tuple[str, ...] = (
    "BRIDGE_TIMESCALE_DSN",
    "TIMESCALE_DSN",
    "TIMESCALE_DATABASE_URL",
    "DATABASE_URL",
)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments and apply environment defaults."""

    parser = argparse.ArgumentParser(description="Run Bridge Lite audit log ETL")
    parser.add_argument(
        "--mode",
        choices=("polling", "event", "hybrid"),
        help="Run polling ETL, event-driven ETL, or both",
    )
    parser.add_argument("--source-dsn", dest="source_dsn", help="PostgreSQL DSN for audit_logs")
    parser.add_argument("--target-dsn", dest="target_dsn", help="TimescaleDB DSN for audit_logs_ts")
    parser.add_argument("--batch-size", type=int, help="Batch size for polling ETL (default: 100)")
    parser.add_argument("--interval", type=float, help="Polling interval in seconds (default: 5.0)")
    parser.add_argument("--log-level", help="Python logging level (default: INFO)")

    args = parser.parse_args(argv)

    if args.mode is None:
        args.mode = os.getenv("BRIDGE_ETL_MODE", _DEFAULT_MODE)
    if args.batch_size is None:
        args.batch_size = _parse_int_env("BRIDGE_ETL_BATCH_SIZE", _DEFAULT_BATCH)
    if args.interval is None:
        args.interval = _parse_float_env("BRIDGE_ETL_INTERVAL", _DEFAULT_INTERVAL)
    if args.log_level is None:
        args.log_level = os.getenv("BRIDGE_ETL_LOG_LEVEL", _DEFAULT_LOG_LEVEL)

    return args


def _parse_int_env(var: str, default: int) -> int:
    value = os.getenv(var)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning("Invalid integer for %s (%s); falling back to %s", var, value, default)
        return default


def _parse_float_env(var: str, default: float) -> float:
    value = os.getenv(var)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        logger.warning("Invalid float for %s (%s); falling back to %s", var, value, default)
        return default


def build_config(args: argparse.Namespace) -> AuditLogETLConfig:
    """Construct an :class:`AuditLogETLConfig` from CLI arguments."""

    source = _resolve_dsn(args.source_dsn, _SOURCE_DSN_ENV_ORDER)
    if not source:
        raise RuntimeError(
            "Source DSN is required (set --source-dsn or BRIDGE_SOURCE_DSN/POSTGRES_DSN/DATABASE_URL)"
        )

    target = _resolve_dsn(args.target_dsn, _TARGET_DSN_ENV_ORDER) or source

    return AuditLogETLConfig(
        source_db_url=source,
        target_db_url=target,
        batch_size=args.batch_size,
        interval_seconds=args.interval,
    )


def _resolve_dsn(explicit: Optional[str], env_keys: Iterable[str]) -> Optional[str]:
    if explicit:
        return explicit
    for key in env_keys:
        candidate = os.getenv(key)
        if candidate:
            return candidate
    return None


def configure_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def main(argv: Optional[List[str]] = None) -> None:
    """Entrypoint used by ``python -m bridge.etl``."""

    args = parse_args(argv)
    configure_logging(args.log_level)

    config = build_config(args)

    try:
        asyncio.run(_run_mode(args.mode, config))
    except KeyboardInterrupt:  # pragma: no cover - CLI convenience
        logger.info("Audit log ETL interrupted; shutting down")


async def _run_mode(mode: str, config: AuditLogETLConfig) -> None:
    if mode not in {"polling", "event", "hybrid"}:  # Defensive guard
        raise ValueError(f"Unsupported ETL mode: {mode}")

    tasks = []
    if mode in {"polling", "hybrid"}:
        tasks.append(asyncio.create_task(_run_polling(config)))
    if mode in {"event", "hybrid"}:
        tasks.append(asyncio.create_task(_run_event_driven(config)))

    if not tasks:
        raise RuntimeError("No ETL tasks scheduled")

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise


async def _run_polling(config: AuditLogETLConfig) -> None:
    etl = AuditLogETL(config)
    logger.info(
        "Starting polling ETL (batch_size=%s, interval=%ss)", config.batch_size, config.interval_seconds
    )
    await etl.start()


async def _run_event_driven(config: AuditLogETLConfig) -> None:
    etl = EventDrivenAuditLogETL(config)
    await etl.start()
    logger.info("Event-driven AuditLogETL subscribed; entering idle loop")
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("Stopping event-driven AuditLogETL")
        await etl.stop()
        raise


__all__ = [
    "build_config",
    "configure_logging",
    "main",
    "parse_args",
]
