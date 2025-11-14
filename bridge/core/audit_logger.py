"""Audit logging utilities for Bridge Lite."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class AuditLogger:
    """JSON Lines形式でイベントを記録する非同期対応ロガー。"""

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        filename: str = "audit.log",
    ) -> None:
        self.base_dir = base_dir or Path("logs") / "audit"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.base_dir / filename

    async def log_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """汎用イベントを記録する。"""

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            **payload,
        }
        await self._write_entry(entry)

    async def log_ai_call(
        self,
        bridge: str,
        model: str,
        prompt_length: Optional[int],
        response_length: Optional[int],
        duration_ms: Optional[float],
        success: bool,
        **extra: Any,
    ) -> None:
        """AI呼び出しイベントを記録する。"""

        payload: Dict[str, Any] = {
            "bridge": bridge,
            "model": model,
            "prompt_length": prompt_length,
            "response_length": response_length,
            "duration_ms": duration_ms,
            "success": success,
        }
        if extra:
            payload["extra"] = extra
        await self.log_event("ai_call", payload)

    async def log_reevaluation(
        self,
        intent_id: str,
        judgment: str,
        score: Optional[float],
        reason: Optional[str],
        duration_ms: Optional[float] = None,
        **criteria: Any,
    ) -> None:
        """再評価結果を記録する。"""

        payload: Dict[str, Any] = {
            "intent_id": intent_id,
            "judgment": judgment,
            "evaluation_score": score,
            "reason": reason,
            "duration_ms": duration_ms,
        }
        if criteria:
            payload["criteria"] = criteria
        await self.log_event("reevaluation", payload)

    async def _write_entry(self, entry: Dict[str, Any]) -> None:
        """イベントをファイルに追記する。"""

        await asyncio.to_thread(self._write_entry_sync, entry)

    def _write_entry_sync(self, entry: Dict[str, Any]) -> None:
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
