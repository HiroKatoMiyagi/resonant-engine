#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion Sync Agent v1.0
----------------------
Resonant Engine用 Notion統合エージェント

Notionの4つのデータベースを統合:
1. specs - 仕様書DB（トリガー層）
2. tasks - タスクDB
3. reviews - レビューDB
4. resonant_archive - アーカイブDB

統一イベントストリームと連携し、仕様駆動開発を実現。
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Notion API
try:
    from notion_client import Client
except ImportError:
    print("⚠️ notion-client がインストールされていません")
    print("インストール: pip install notion-client")
    sys.exit(1)

# utils/ からの import
sys.path.append(str(Path(__file__).parent))
from resonant_event_stream import get_stream
from error_recovery import (
    with_retry,
    ErrorClassifier,
    RetryStrategy,
    DeadLetterQueue
)

load_dotenv()

# 環境変数
NOTION_TOKEN = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")  # NOTION_API_KEY も対応
SPECS_DB_ID = os.getenv("NOTION_SPECS_DB_ID")
TASKS_DB_ID = os.getenv("NOTION_TASKS_DB_ID")
REVIEWS_DB_ID = os.getenv("NOTION_REVIEWS_DB_ID")
ARCHIVE_DB_ID = os.getenv("NOTION_ARCHIVE_DB_ID")


class NotionSyncAgent:
    """
    Notion統合エージェント
    
    主要機能:
    1. specs DBの監視（同期トリガー検知）
    2. tasks DB からタスク取得
    3. reviews DB からレビュー取得
    4. resonant_archive へメトリクス書き込み
    5. 全てをイベントストリームに統合
    """
    
    def __init__(self):
        if not NOTION_TOKEN:
            raise ValueError("NOTION_TOKEN が設定されていません")
        
        # Notion Client（APIバージョン指定が必要）
        self.client = Client(auth=NOTION_TOKEN, notion_version="2022-06-28")
        self.stream = get_stream()
        self.dlq = DeadLetterQueue()
        
        # データベースID（UUID形式に変換）
        self.specs_db_id = self._format_uuid(SPECS_DB_ID)
        self.tasks_db_id = self._format_uuid(TASKS_DB_ID)
        self.reviews_db_id = self._format_uuid(REVIEWS_DB_ID)
        self.archive_db_id = self._format_uuid(ARCHIVE_DB_ID)
    
    def _format_uuid(self, id_str: Optional[str]) -> Optional[str]:
        """
        データベースIDをUUID形式（ハイフン付き）に変換
        既にハイフンがある場合はそのまま返す
        """
        if not id_str:
            return None
        
        # ハイフンを削除して32文字の文字列にする
        id_clean = id_str.replace("-", "")
        
        if len(id_clean) != 32:
            return id_str  # 長さが異なる場合はそのまま返す
        
        # UUID形式（8-4-4-4-12）に変換
        return f"{id_clean[0:8]}-{id_clean[8:12]}-{id_clean[12:16]}-{id_clean[16:20]}-{id_clean[20:32]}"
    
    def _handle_retry(self, event_id: str, attempt: int, error: Exception, error_classifier: ErrorClassifier):
        """リトライ時の処理"""
        error_category = error_classifier.classify_error(error)
        
        # リトライイベントを記録
        self.stream.emit(
            event_type="retry",
            source="notion_sync",
            data={
                "parent_event_id": event_id,
                "attempt": attempt,
                "error": str(error),
                "error_type": type(error).__name__
            },
            parent_event_id=event_id,
            tags=["notion", "retry"],
            status="retrying",
            error_info={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "error_category": error_category.value
            },
            retry_info={
                "retry_count": attempt,
                "retryable": True
            }
        )
        print(f"🔄 リトライ {attempt}: {type(error).__name__}: {error}")
    
    def _handle_failure(self, event_id: str, error: Exception, error_classifier: ErrorClassifier, retry_count: int):
        """最終失敗時の処理"""
        error_category = error_classifier.classify_error(error)
        
        # 失敗イベントは既にメイン処理で記録されるため、ここではログのみ
        print(f"❌ 最終失敗（リトライ回数: {retry_count}）: {type(error).__name__}: {error}")
    
    # ============================================
    # 1. Specs DB（仕様書）の監視
    # ============================================
    
    def get_specs_with_sync_trigger(self) -> List[Dict[str, Any]]:
        """
        同期トリガーが「Yes」の仕様書を取得
        
        Returns:
            同期対象の仕様書リスト
        """
        if not self.specs_db_id:
            print("⚠️ NOTION_SPECS_DB_ID が設定されていません")
            return []
        
        # イベント記録: 同期開始
        sync_id = self.stream.emit(
            event_type="action",
            source="notion_sync",
            data={
                "action": "fetch_specs",
                "database": "specs",
                "filter": "sync_trigger=Yes"
            },
            tags=["notion", "specs", "sync"]
        )
        
        # エラー分類とリカバリー戦略の取得
        error_category = None
        retry_count = 0
        
        def fetch_specs():
            """仕様書取得の内部関数（リトライ対象）"""
            nonlocal retry_count
            retry_count += 1
            
            import time
            start_time = time.time()
            
            # Notion API: データベースクエリ（requestメソッドを直接使用）
            # 「同期トリガー」はCheckbox型なので、checkbox filterを使用
            response = self.client.request(
                path=f"databases/{self.specs_db_id}/query",
                method="POST",
                body={
                    "filter": {
                        "property": "同期トリガー",
                        "checkbox": {
                            "equals": True
                        }
                    }
                }
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            specs = []
            for page in response.get("results", []):
                spec = self._parse_spec_page(page)
                specs.append(spec)
                
                # イベント記録: 仕様書検知
                self.stream.emit(
                    event_type="observation",
                    source="notion_sync",
                    data={
                        "spec_name": spec.get("name"),
                        "page_id": spec.get("id"),
                        "status": spec.get("status"),
                        "memo": spec.get("memo", "")[:100]  # 長すぎる場合は切り詰め
                    },
                    parent_event_id=sync_id,
                    tags=["notion", "spec", "trigger"],
                    latency_ms=latency_ms
                )
            
            return specs
        
        # エラー分類器の初期化
        error_classifier = ErrorClassifier()
        
        # デフォルトのリトライ戦略（エラーが発生したら動的に変更）
        strategy = RetryStrategy(
            max_retries=3,
            initial_delay=1.0,
            max_delay=60.0,
            exponential_base=2.0
        )
        
        try:
            # 自動リトライ付きで実行
            specs = with_retry(
                fetch_specs,
                strategy=strategy,
                error_context={
                    "action": "fetch_specs",
                    "database": "specs",
                    "database_id": self.specs_db_id
                },
                on_retry=lambda attempt, error: self._handle_retry(
                    sync_id, attempt, error, error_classifier
                ),
                on_failure=lambda error: self._handle_failure(
                    sync_id, error, error_classifier, retry_count
                )
            )
            
            # イベント記録: 取得成功
            self.stream.emit(
                event_type="result",
                source="notion_sync",
                data={
                    "status": "success",
                    "specs_count": len(specs)
                },
                parent_event_id=sync_id,
                tags=["notion", "success"],
                status="success"
            )
            
            return specs
            
        except Exception as e:
            # エラー分類
            error_category = ErrorClassifier.classify_error(e)
            
            # イベント記録: エラー（構造化されたエラー情報）
            import traceback
            error_info = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_category": error_category.value,
                "stack_trace": traceback.format_exc()
            }
            
            self.stream.emit(
                event_type="result",
                source="notion_sync",
                data={
                    "status": "error",
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                parent_event_id=sync_id,
                tags=["notion", "error"],
                status="failed",
                error_info=error_info,
                retry_info={
                    "retry_count": retry_count,
                    "max_retries": strategy.max_retries if 'strategy' in locals() else 0,
                    "retryable": ErrorClassifier.is_retryable(e)
                }
            )
            
            # リトライ不可能なエラーはデッドレターキューに追加
            if not ErrorClassifier.is_retryable(e):
                self.dlq.add(
                    event_id=sync_id,
                    error=e,
                    error_category=error_category,
                    context={
                        "action": "fetch_specs",
                        "database": "specs",
                        "database_id": self.specs_db_id
                    },
                    retry_count=retry_count
                )
            
            print(f"❌ Specs DB取得エラー: {type(e).__name__}: {e}")
            print(f"詳細:\n{traceback.format_exc()}")
            return []
    
    def _parse_spec_page(self, page: Dict) -> Dict[str, Any]:
        """Notion APIのページオブジェクトを解析"""
        props = page.get("properties", {})
        
        # タイトルの取得
        name_prop = props.get("名前", {})
        name = ""
        if name_prop.get("title"):
            name = name_prop["title"][0]["plain_text"]
        
        # 各プロパティの取得
        return {
            "id": page.get("id"),
            "name": name,
            "public": self._get_checkbox(props.get("公開可")),
            "sync_trigger": self._get_checkbox(props.get("同期トリガー")),  # checkbox型
            "memo": self._get_rich_text(props.get("実行メモ")),
            "last_sync": self._get_date(props.get("最終同期")),
            "status": self._get_select(props.get("構築ステータス")),
            "url": page.get("url")
        }
    
    # ============================================
    # 2. Tasks DB（タスク）の取得
    # ============================================
    
    def get_tasks_for_spec(self, spec_page_id: str) -> List[Dict[str, Any]]:
        """
        特定の仕様書に紐付くタスクを取得
        
        Args:
            spec_page_id: 仕様書ページのID
        
        Returns:
            タスクのリスト
        """
        if not self.tasks_db_id:
            print("⚠️ NOTION_TASKS_DB_ID が設定されていません")
            return []
        
        try:
            # Notion API: データベースクエリ（requestメソッドを直接使用）
            response = self.client.request(
                path=f"databases/{self.tasks_db_id}/query",
                method="POST",
                body={
                    "filter": {
                        "property": "対象ページID",
                        "rich_text": {
                            "contains": spec_page_id
                        }
                    }
                }
            )
            
            tasks = []
            for page in response.get("results", []):
                task = self._parse_task_page(page)
                tasks.append(task)
            
            return tasks
            
        except Exception as e:
            print(f"❌ Tasks DB取得エラー: {e}")
            return []
    
    def _parse_task_page(self, page: Dict) -> Dict[str, Any]:
        """タスクページを解析"""
        props = page.get("properties", {})
        
        # タイトルの取得
        title_prop = props.get("タスク名", {})
        title = ""
        if title_prop.get("title"):
            title = title_prop["title"][0]["plain_text"]
        
        return {
            "id": page.get("id"),
            "title": title,
            "target_page_id": self._get_text(props.get("対象ページID")),
            "assignee": self._get_text(props.get("担当")),
            "priority": self._get_select(props.get("優先度")),
            "status": self._get_select(props.get("状態")),
            "deadline": self._get_date(props.get("期限")),
            "notes": self._get_rich_text(props.get("備考")),
            "url": page.get("url")
        }
    
    # ============================================
    # 3. Reviews DB（レビュー）の取得
    # ============================================
    
    def get_reviews_for_spec(self, spec_page_id: str) -> List[Dict[str, Any]]:
        """
        特定の仕様書に紐付くレビューを取得
        
        Args:
            spec_page_id: 仕様書ページのID
        
        Returns:
            レビューのリスト
        """
        if not self.reviews_db_id:
            print("⚠️ NOTION_REVIEWS_DB_ID が設定されていません")
            return []
        
        try:
            response = self.client.request(
                path=f"databases/{self.reviews_db_id}/query",
                method="POST",
                body={
                    "filter": {
                        "property": "対象ページID",
                        "rich_text": {
                            "contains": spec_page_id
                        }
                    }
                }
            )
            
            reviews = []
            for page in response.get("results", []):
                review = self._parse_review_page(page)
                reviews.append(review)
            
            return reviews
            
        except Exception as e:
            print(f"❌ Reviews DB取得エラー: {e}")
            return []
    
    def _parse_review_page(self, page: Dict) -> Dict[str, Any]:
        """レビューページを解析"""
        props = page.get("properties", {})
        
        return {
            "id": page.get("id"),
            "target_page_id": self._get_text(props.get("対象ページID")),
            "review_type": self._get_select(props.get("レビュー種別")),
            "status": self._get_select(props.get("ステータス")),
            "severity": self._get_select(props.get("重要度")),
            "reviewer": self._get_text(props.get("レビュアー")),
            "comment": self._get_rich_text(props.get("コメント")),
            "public": self._get_checkbox(props.get("公開可")),
            "url": page.get("url")
        }
    
    # ============================================
    # 4. Resonant Archive（メトリクス）への書き込み
    # ============================================
    
    def write_archive(self, phase: str, metrics: Dict[str, Any]) -> bool:
        """
        Resonant Archiveにメトリクスを書き込み
        
        Args:
            phase: フェーズ名
            metrics: メトリクスデータ
        
        Returns:
            成功したかどうか
        """
        if not self.archive_db_id:
            print("⚠️ NOTION_ARCHIVE_DB_ID が設定されていません")
            return False
        
        try:
            # Notion API: ページ作成（requestメソッドを直接使用）
            self.client.request(
                path="pages",
                method="POST",
                body={
                    "parent": {"database_id": self.archive_db_id},
                    "properties": {
                        "Phase": {
                            "title": [{"text": {"content": phase}}]
                        },
                        "Stability Index": {
                            "rich_text": [{"text": {"content": str(metrics.get("stability_index", "N/A"))}}]
                        },
                        "Coherence Ratio": {
                            "rich_text": [{"text": {"content": str(metrics.get("coherence_ratio", "N/A"))}}]
                        },
                        "Last Update": {
                            "rich_text": [{"text": {"content": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}}]
                        },
                        "Telemetry (Base64)": {
                            "rich_text": [{"text": {"content": metrics.get("telemetry_b64", "N/A")}}]
                        }
                    }
                }
            )
            
            print(f"✅ Archive書き込み成功: {phase}")
            return True
            
        except Exception as e:
            print(f"❌ Archive書き込みエラー: {e}")
            return False
    
    # ============================================
    # ユーティリティ: プロパティ解析
    # ============================================
    
    def _get_text(self, prop: Optional[Dict]) -> str:
        """Textプロパティを取得"""
        if not prop or "rich_text" not in prop:
            return ""
        texts = prop["rich_text"]
        if not texts:
            return ""
        return texts[0]["plain_text"]
    
    def _get_rich_text(self, prop: Optional[Dict]) -> str:
        """Rich textプロパティを取得"""
        return self._get_text(prop)
    
    def _get_select(self, prop: Optional[Dict]) -> str:
        """Selectプロパティを取得"""
        if not prop or "select" not in prop:
            return ""
        select = prop["select"]
        if not select:
            return ""
        return select.get("name", "")
    
    def _get_checkbox(self, prop: Optional[Dict]) -> bool:
        """Checkboxプロパティを取得"""
        if not prop or "checkbox" not in prop:
            return False
        return prop["checkbox"]
    
    def _get_date(self, prop: Optional[Dict]) -> Optional[str]:
        """Dateプロパティを取得"""
        if not prop or "date" not in prop:
            return None
        date = prop["date"]
        if not date:
            return None
        return date.get("start")


# ============================================
# CLI実行
# ============================================

def main():
    """メイン処理"""
    print("🔄 Notion Sync Agent - 同期トリガー検知テスト\n")
    
    agent = NotionSyncAgent()
    
    # 同期トリガーが「Yes」の仕様書を取得
    specs = agent.get_specs_with_sync_trigger()
    
    if not specs:
        print("📭 同期トリガーが「Yes」の仕様書が見つかりませんでした")
        return
    
    print(f"✅ {len(specs)}件の仕様書が同期対象です\n")
    
    for spec in specs:
        print(f"📄 {spec['name']}")
        print(f"   ID: {spec['id']}")
        print(f"   ステータス: {spec['status']}")
        print(f"   メモ: {spec['memo'][:100] if spec['memo'] else '(なし)'}")
        print(f"   URL: {spec['url']}")
        
        # 紐付くタスクを取得
        tasks = agent.get_tasks_for_spec(spec['id'])
        if tasks:
            print(f"   📋 タスク: {len(tasks)}件")
            for task in tasks:
                print(f"      - {task['title']} ({task['status']} / {task['priority']})")
        
        # 紐付くレビューを取得
        reviews = agent.get_reviews_for_spec(spec['id'])
        if reviews:
            print(f"   💬 レビュー: {len(reviews)}件")
            for review in reviews:
                print(f"      - [{review['review_type']}] {review['status']} ({review['severity']})")
        
        print()


if __name__ == "__main__":
    main()

