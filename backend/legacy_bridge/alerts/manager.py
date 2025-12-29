"""Alert evaluation runtime for Bridge Lite."""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Awaitable, Callable, Dict, Iterable, List, Optional, Sequence

import aiohttp
import asyncpg

from .config import AlertChannel, AlertRule, AlertSeverity, DEFAULT_ALERT_RULES

logger = logging.getLogger(__name__)


ClockFn = Callable[[], datetime]
SessionFactory = Callable[[], aiohttp.ClientSession]
PoolFactory = Callable[[], Awaitable[asyncpg.Pool]]


class AlertManager:
    """Evaluate alert rules against PostgreSQL metrics."""

    def __init__(
        self,
        database_url: str,
        *,
        rules: Sequence[AlertRule] | None = None,
        pool_factory: Optional[PoolFactory] = None,
        session_factory: Optional[SessionFactory] = None,
        clock: Optional[ClockFn] = None,
    ) -> None:
        if not database_url:
            raise ValueError("database_url is required for AlertManager")

        self._database_url = database_url
        self._rules: Sequence[AlertRule] = rules or DEFAULT_ALERT_RULES
        self._pool_factory: PoolFactory = pool_factory or (lambda: asyncpg.create_pool(database_url))
        self._session_factory: SessionFactory = session_factory or aiohttp.ClientSession
        self._clock: ClockFn = clock or datetime.utcnow

        self._pool: Optional[asyncpg.Pool] = None
        self._running = False
        self.last_alerts: Dict[str, datetime] = {}

    async def start(self, interval_seconds: float = 60.0) -> None:
        """Start evaluating alert rules periodically."""

        logger.info("Alert manager starting with %d rules", len(self._rules))
        self._running = True

        try:
            while self._running:
                await self._evaluate_all_rules()
                await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:  # pragma: no cover - cooperative cancellation
            logger.info("Alert manager cancelled, shutting down")
            raise
        finally:
            self._running = False

    async def stop(self) -> None:
        """Stop the manager loop."""

        self._running = False

    async def close(self) -> None:
        """Dispose resources (connection pool)."""

        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await self._pool_factory()
        return self._pool

    async def _evaluate_all_rules(self) -> None:
        pool = await self._ensure_pool()
        for rule in self._rules:
            try:
                await self._evaluate_rule(rule, pool)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.exception("Error evaluating rule %s: %s", rule.name, exc)

    async def _evaluate_rule(self, rule: AlertRule, pool: asyncpg.Pool) -> None:
        if not self._can_alert(rule):
            return

        async with pool.acquire() as connection:
            value = await connection.fetchval(rule.condition)

        if value is None:
            return

        numeric = float(value)
        if self._check_threshold(rule, numeric):
            await self._send_alert(rule, numeric)
            self.last_alerts[rule.name] = self._clock()

    def _can_alert(self, rule: AlertRule) -> bool:
        last_alert = self.last_alerts.get(rule.name)
        if not last_alert:
            return True
        cooldown = timedelta(minutes=rule.cooldown_minutes or 0)
        return self._clock() - last_alert > cooldown

    def _check_threshold(self, rule: AlertRule, value: float) -> bool:
        if rule.name == "no_activity":
            return value < rule.threshold
        return value > rule.threshold

    async def _send_alert(self, rule: AlertRule, value: float) -> None:
        if not rule.channels:
            logger.warning("Rule %s triggered but has no channels", rule.name)
            return

        message = (
            f"[{rule.severity.value.upper()}] {rule.name}: {rule.description}\n"
            f"Current value: {value:.2f} (threshold: {rule.threshold})\n"
            f"Time: {self._clock().isoformat()}"
        )

        tasks: List[Awaitable[None]] = []
        for channel in rule.channels:
            if channel == AlertChannel.SLACK:
                tasks.append(self._send_slack(rule, message, value))
            elif channel == AlertChannel.EMAIL:
                tasks.append(self._send_email(rule, message))
            elif channel == AlertChannel.WEBHOOK:
                tasks.append(self._send_webhook(rule, message, value))
            elif channel == AlertChannel.LOG:
                tasks.append(self._log_alert(rule, message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_slack(self, rule: AlertRule, message: str, value: float) -> None:
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            logger.warning("SLACK_WEBHOOK_URL not configured; skipping Slack alert for %s", rule.name)
            return

        payload = {
            "attachments": [
                {
                    "color": self._severity_color(rule.severity),
                    "title": f"\ud83d\udd14 {rule.name}",
                    "text": message,
                    "footer": "Bridge Lite Alert System",
                    "ts": int(self._clock().timestamp()),
                }
            ]
        }

        async with self._session_factory() as session:
            await session.post(webhook_url, json=payload, timeout=5)

    async def _send_email(self, rule: AlertRule, message: str) -> None:
        logger.info("Email channel for %s not implemented; message: %s", rule.name, message)

    async def _send_webhook(self, rule: AlertRule, message: str, value: float) -> None:
        webhook_url = os.getenv("ALERT_WEBHOOK_URL")
        if not webhook_url:
            logger.warning("ALERT_WEBHOOK_URL not configured; skipping webhook alert for %s", rule.name)
            return

        payload = {
            "rule": rule.name,
            "severity": rule.severity.value,
            "message": message,
            "value": value,
            "threshold": rule.threshold,
            "timestamp": self._clock().isoformat(),
        }

        async with self._session_factory() as session:
            await session.post(webhook_url, json=payload, timeout=5)

    async def _log_alert(self, rule: AlertRule, message: str) -> None:
        logger.warning("%s", message)

    @staticmethod
    def _severity_color(severity: AlertSeverity) -> str:
        return {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ff9800",
            AlertSeverity.ERROR: "#f44336",
            AlertSeverity.CRITICAL: "#9c27b0",
        }[severity]


async def run_forever(interval_seconds: float = 60.0) -> None:
    """Helper to run the manager using environment configuration."""

    database_url = os.getenv("POSTGRES_DSN") or os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("POSTGRES_DSN or DATABASE_URL must be configured for AlertManager")

    manager = AlertManager(database_url)
    try:
        await manager.start(interval_seconds=interval_seconds)
    finally:
        await manager.close()


__all__ = ["AlertManager", "run_forever"]
