#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Metrics Collector - P1-4: メトリクス収集基盤
=====================================================
エラー、リトライ、パフォーマンスのメトリクスを収集
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from collections import defaultdict
from threading import Lock


class MetricsCollector:
    """
    軽量メトリクス収集システム
    
    収集項目:
    - リトライ回数（イベントID別、カテゴリ別）
    - エラー発生率（カテゴリ別、タイプ別）
    - レイテンシー統計
    - デッドレターキュー増加率
    """
    
    def __init__(self, metrics_path: Path = None):
        """
        Args:
            metrics_path: メトリクスファイルパス
        """
        base_dir = Path(__file__).parent.parent / "logs"
        self.metrics_path = metrics_path or base_dir / "metrics.json"
        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.lock = Lock()
        self.metrics = self._load_metrics()
    
    def _load_metrics(self) -> Dict[str, Any]:
        """メトリクスをロード"""
        if self.metrics_path.exists():
            try:
                with open(self.metrics_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        return {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "counters": {
                "total_events": 0,
                "success_events": 0,
                "failed_events": 0,
                "retried_events": 0,
                "dead_letter_events": 0
            },
            "error_categories": defaultdict(int),
            "error_types": defaultdict(int),
            "retry_counts": [],  # イベントごとのリトライ回数
            "latencies": [],  # レイテンシー（ms）
            "hourly_stats": {}  # 時間別統計
        }
    
    def _save_metrics(self):
        """メトリクスを保存"""
        with self.lock:
            self.metrics["last_updated"] = datetime.now().isoformat()
            
            # defaultdictをdictに変換
            if isinstance(self.metrics.get("error_categories"), defaultdict):
                self.metrics["error_categories"] = dict(self.metrics["error_categories"])
            if isinstance(self.metrics.get("error_types"), defaultdict):
                self.metrics["error_types"] = dict(self.metrics["error_types"])
            
            with open(self.metrics_path, "w", encoding="utf-8") as f:
                json.dump(self.metrics, f, indent=2, ensure_ascii=False)
    
    def record_event(self, status: str, error_category: Optional[str] = None, 
                     error_type: Optional[str] = None, retry_count: int = 0,
                     latency_ms: Optional[int] = None):
        """
        イベントを記録
        
        Args:
            status: イベントステータス (success/failed/retrying/dead_letter)
            error_category: エラーカテゴリ (transient/permanent/unknown)
            error_type: エラータイプ (ValueError, ConnectionError等)
            retry_count: リトライ回数
            latency_ms: レイテンシー（ミリ秒）
        """
        with self.lock:
            counters = self.metrics["counters"]
            counters["total_events"] += 1
            
            # ステータス別カウント
            if status == "success":
                counters["success_events"] += 1
            elif status == "failed":
                counters["failed_events"] += 1
            elif status == "retrying":
                counters["retried_events"] += 1
            elif status == "dead_letter":
                counters["dead_letter_events"] += 1
            
            # エラーカテゴリ
            if error_category:
                if isinstance(self.metrics["error_categories"], dict):
                    self.metrics["error_categories"] = defaultdict(int, self.metrics["error_categories"])
                self.metrics["error_categories"][error_category] += 1
            
            # エラータイプ
            if error_type:
                if isinstance(self.metrics["error_types"], dict):
                    self.metrics["error_types"] = defaultdict(int, self.metrics["error_types"])
                self.metrics["error_types"][error_type] += 1
            
            # リトライ回数
            if retry_count > 0:
                self.metrics["retry_counts"].append(retry_count)
            
            # レイテンシー
            if latency_ms is not None:
                self.metrics["latencies"].append(latency_ms)
                # メモリ節約：最新1000件のみ保持
                if len(self.metrics["latencies"]) > 1000:
                    self.metrics["latencies"] = self.metrics["latencies"][-1000:]
            
            # 時間別統計
            hour_key = datetime.now().strftime("%Y-%m-%d %H:00")
            if hour_key not in self.metrics["hourly_stats"]:
                self.metrics["hourly_stats"][hour_key] = {
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "retried": 0
                }
            
            self.metrics["hourly_stats"][hour_key]["total"] += 1
            if status == "success":
                self.metrics["hourly_stats"][hour_key]["success"] += 1
            elif status in ["failed", "dead_letter"]:
                self.metrics["hourly_stats"][hour_key]["failed"] += 1
            elif status == "retrying":
                self.metrics["hourly_stats"][hour_key]["retried"] += 1
        
        self._save_metrics()
    
    def get_summary(self) -> Dict[str, Any]:
        """メトリクスサマリーを取得"""
        with self.lock:
            counters = self.metrics["counters"]
            total = counters["total_events"]
            
            if total == 0:
                return {
                    "total_events": 0,
                    "success_rate": 0.0,
                    "error_rate": 0.0,
                    "retry_rate": 0.0
                }
            
            # 成功率・エラー率
            success_rate = counters["success_events"] / total * 100
            error_rate = counters["failed_events"] / total * 100
            retry_rate = counters["retried_events"] / total * 100
            
            # レイテンシー統計
            latencies = self.metrics.get("latencies", [])
            latency_stats = {}
            if latencies:
                latencies_sorted = sorted(latencies)
                latency_stats = {
                    "min": min(latencies),
                    "max": max(latencies),
                    "avg": sum(latencies) / len(latencies),
                    "p50": latencies_sorted[len(latencies) // 2],
                    "p95": latencies_sorted[int(len(latencies) * 0.95)],
                    "p99": latencies_sorted[int(len(latencies) * 0.99)]
                }
            
            # リトライ統計
            retry_counts = self.metrics.get("retry_counts", [])
            retry_stats = {}
            if retry_counts:
                retry_stats = {
                    "avg_retries": sum(retry_counts) / len(retry_counts),
                    "max_retries": max(retry_counts),
                    "total_retries": sum(retry_counts)
                }
            
            return {
                "total_events": total,
                "success_events": counters["success_events"],
                "failed_events": counters["failed_events"],
                "dead_letter_events": counters["dead_letter_events"],
                "success_rate": round(success_rate, 2),
                "error_rate": round(error_rate, 2),
                "retry_rate": round(retry_rate, 2),
                "error_categories": dict(self.metrics.get("error_categories", {})),
                "error_types": dict(self.metrics.get("error_types", {})),
                "latency_stats": latency_stats,
                "retry_stats": retry_stats,
                "last_updated": self.metrics.get("last_updated")
            }
    
    def export_prometheus_format(self) -> str:
        """
        Prometheus形式でエクスポート
        
        Returns:
            Prometheus テキスト形式のメトリクス
        """
        summary = self.get_summary()
        lines = []
        
        # カウンター
        lines.append("# HELP resonant_events_total Total number of events")
        lines.append("# TYPE resonant_events_total counter")
        lines.append(f"resonant_events_total {summary['total_events']}")
        lines.append("")
        
        lines.append("# HELP resonant_events_success Success events")
        lines.append("# TYPE resonant_events_success counter")
        lines.append(f"resonant_events_success {summary['success_events']}")
        lines.append("")
        
        lines.append("# HELP resonant_events_failed Failed events")
        lines.append("# TYPE resonant_events_failed counter")
        lines.append(f"resonant_events_failed {summary['failed_events']}")
        lines.append("")
        
        lines.append("# HELP resonant_events_dead_letter Dead letter queue events")
        lines.append("# TYPE resonant_events_dead_letter counter")
        lines.append(f"resonant_events_dead_letter {summary['dead_letter_events']}")
        lines.append("")
        
        # ゲージ（率）
        lines.append("# HELP resonant_success_rate Success rate percentage")
        lines.append("# TYPE resonant_success_rate gauge")
        lines.append(f"resonant_success_rate {summary['success_rate']}")
        lines.append("")
        
        lines.append("# HELP resonant_error_rate Error rate percentage")
        lines.append("# TYPE resonant_error_rate gauge")
        lines.append(f"resonant_error_rate {summary['error_rate']}")
        lines.append("")
        
        # エラーカテゴリ別
        if summary.get("error_categories"):
            lines.append("# HELP resonant_errors_by_category Errors by category")
            lines.append("# TYPE resonant_errors_by_category counter")
            for category, count in summary["error_categories"].items():
                lines.append(f'resonant_errors_by_category{{category="{category}"}} {count}')
            lines.append("")
        
        # レイテンシー
        if summary.get("latency_stats"):
            latency = summary["latency_stats"]
            lines.append("# HELP resonant_latency_ms Latency in milliseconds")
            lines.append("# TYPE resonant_latency_ms summary")
            lines.append(f"resonant_latency_ms_avg {latency.get('avg', 0)}")
            lines.append(f"resonant_latency_ms_p50 {latency.get('p50', 0)}")
            lines.append(f"resonant_latency_ms_p95 {latency.get('p95', 0)}")
            lines.append(f"resonant_latency_ms_p99 {latency.get('p99', 0)}")
            lines.append("")
        
        return "\n".join(lines)
    
    def reset_metrics(self):
        """メトリクスをリセット"""
        with self.lock:
            self.metrics = {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "counters": {
                    "total_events": 0,
                    "success_events": 0,
                    "failed_events": 0,
                    "retried_events": 0,
                    "dead_letter_events": 0
                },
                "error_categories": defaultdict(int),
                "error_types": defaultdict(int),
                "retry_counts": [],
                "latencies": [],
                "hourly_stats": {}
            }
            self._save_metrics()


# グローバルインスタンス
_metrics_collector = None

def get_metrics_collector() -> MetricsCollector:
    """シングルトンのMetricsCollectorを取得"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


if __name__ == "__main__":
    # デモ実行
    collector = MetricsCollector()
    
    print("=== Metrics Collector Demo ===\n")
    
    # メトリクス記録
    collector.record_event("success", latency_ms=120)
    collector.record_event("success", latency_ms=95)
    collector.record_event("failed", error_category="transient", error_type="ConnectionError", retry_count=2, latency_ms=1500)
    collector.record_event("retrying", error_category="transient", error_type="TimeoutError", retry_count=1, latency_ms=3000)
    collector.record_event("dead_letter", error_category="transient", error_type="TimeoutError", retry_count=3, latency_ms=5000)
    
    # サマリー表示
    summary = collector.get_summary()
    print("📊 Metrics Summary:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print()
    
    # Prometheus形式
    print("📈 Prometheus Format:")
    print(collector.export_prometheus_format())
