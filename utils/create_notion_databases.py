#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create Notion Databases - データベース作成ツール
----------------------------------------------
Resonant Engine用のTasks/Reviewsデータベースを自動作成

使い方:
  python utils/create_notion_databases.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# utils/ からの import
sys.path.append(str(Path(__file__).parent))

try:
    from notion_client import Client
except ImportError:
    print("⚠️ notion-client がインストールされていません")
    sys.exit(1)

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
# 親ページID（データベースを作成する場所）
# Notionのワークスペースのルートページか、特定のページのID
PARENT_PAGE_ID = os.getenv("NOTION_PARENT_PAGE_ID")


def create_tasks_database(client: Client, parent_page_id: str) -> str:
    """
    Tasks データベースを作成
    
    Returns:
        作成されたデータベースのID
    """
    print("📋 Tasks データベースを作成中...")
    
    response = client.request(
        path="databases",
        method="POST",
        body={
            "parent": {
                "type": "page_id",
                "page_id": parent_page_id
            },
            "title": [
                {
                    "type": "text",
                    "text": {
                        "content": "Resonant Engine - Tasks"
                    }
                }
            ],
            "properties": {
                "タスク名": {
                    "title": {}
                },
                "対象ページID": {
                    "rich_text": {}
                },
                "担当": {
                    "rich_text": {}
                },
                "優先度": {
                    "select": {
                        "options": [
                            {"name": "Low", "color": "gray"},
                            {"name": "Medium", "color": "blue"},
                            {"name": "High", "color": "yellow"},
                            {"name": "Urgent", "color": "red"}
                        ]
                    }
                },
                "状態": {
                    "select": {
                        "options": [
                            {"name": "ToDo", "color": "gray"},
                            {"name": "Doing", "color": "blue"},
                            {"name": "Blocked", "color": "red"},
                            {"name": "Done", "color": "green"}
                        ]
                    }
                },
                "期限": {
                    "date": {}
                },
                "備考": {
                    "rich_text": {}
                },
                "作成日時": {
                    "created_time": {}
                },
                "更新日時": {
                    "last_edited_time": {}
                }
            }
        }
    )
    
    db_id = response["id"]
    db_url = response["url"]
    
    print(f"✅ Tasks データベース作成完了")
    print(f"   ID: {db_id}")
    print(f"   URL: {db_url}")
    
    return db_id


def create_reviews_database(client: Client, parent_page_id: str) -> str:
    """
    Reviews データベースを作成
    
    Returns:
        作成されたデータベースのID
    """
    print("\n💬 Reviews データベースを作成中...")
    
    response = client.request(
        path="databases",
        method="POST",
        body={
            "parent": {
                "type": "page_id",
                "page_id": parent_page_id
            },
            "title": [
                {
                    "type": "text",
                    "text": {
                        "content": "Resonant Engine - Reviews"
                    }
                }
            ],
            "properties": {
                "対象ページID": {
                    "title": {}  # Reviews DBではこれをタイトルにする
                },
                "レビュー種別": {
                    "select": {
                        "options": [
                            {"name": "ユノ", "color": "blue"},
                            {"name": "アトラス", "color": "purple"},
                            {"name": "外部", "color": "gray"}
                        ]
                    }
                },
                "ステータス": {
                    "select": {
                        "options": [
                            {"name": "Open", "color": "red"},
                            {"name": "In Review", "color": "yellow"},
                            {"name": "Resolved", "color": "green"}
                        ]
                    }
                },
                "重要度": {
                    "select": {
                        "options": [
                            {"name": "Low", "color": "gray"},
                            {"name": "Medium", "color": "blue"},
                            {"name": "High", "color": "yellow"},
                            {"name": "Critical", "color": "red"}
                        ]
                    }
                },
                "レビュアー": {
                    "rich_text": {}
                },
                "コメント": {
                    "rich_text": {}
                },
                "公開可": {
                    "checkbox": {}
                },
                "作成日時": {
                    "created_time": {}
                },
                "更新日時": {
                    "last_edited_time": {}
                }
            }
        }
    )
    
    db_id = response["id"]
    db_url = response["url"]
    
    print(f"✅ Reviews データベース作成完了")
    print(f"   ID: {db_id}")
    print(f"   URL: {db_url}")
    
    return db_id


def create_specs_database(client: Client, parent_page_id: str) -> str:
    """
    Specs データベースを作成
    
    Returns:
        作成されたデータベースのID
    """
    print("📄 Specs データベースを作成中...")
    
    response = client.request(
        path="databases",
        method="POST",
        body={
            "parent": {
                "type": "page_id",
                "page_id": parent_page_id
            },
            "title": [
                {
                    "type": "text",
                    "text": {
                        "content": "specs"
                    }
                }
            ],
            "properties": {
                "名前": {
                    "title": {}
                },
                "公開可": {
                    "checkbox": {}
                },
                "同期トリガー": {
                    "checkbox": {}
                },
                "実行メモ": {
                    "rich_text": {}
                },
                "最終同期": {
                    "date": {}
                },
                "検収": {
                    "rich_text": {}
                },
                "構築ステータス": {
                    "select": {
                        "options": [
                            {"name": "未構築", "color": "gray"},
                            {"name": "構築中", "color": "blue"},
                            {"name": "実稼働", "color": "green"}
                        ]
                    }
                }
            }
        }
    )
    
    db_id = response["id"]
    db_url = response["url"]
    
    print(f"✅ Specs データベース作成完了")
    print(f"   ID: {db_id}")
    print(f"   URL: {db_url}")
    
    return db_id


def create_resonant_archive_database(client: Client, parent_page_id: str) -> str:
    """
    Resonant Archive データベースを作成
    
    Returns:
        作成されたデータベースのID
    """
    print("\n📊 Resonant Archive データベースを作成中...")
    
    response = client.request(
        path="databases",
        method="POST",
        body={
            "parent": {
                "type": "page_id",
                "page_id": parent_page_id
            },
            "title": [
                {
                    "type": "text",
                    "text": {
                        "content": "resonant_archive"
                    }
                }
            ],
            "properties": {
                "Phase": {
                    "title": {}
                },
                "Stability Index": {
                    "rich_text": {}
                },
                "Coherence Ratio": {
                    "rich_text": {}
                },
                "Last Update": {
                    "rich_text": {}
                },
                "Telemetry (Base64)": {
                    "rich_text": {}
                }
            }
        }
    )
    
    db_id = response["id"]
    db_url = response["url"]
    
    print(f"✅ Resonant Archive データベース作成完了")
    print(f"   ID: {db_id}")
    print(f"   URL: {db_url}")
    
    return db_id


def main():
    """メイン処理"""
    print("🔧 Notion データベース作成ツール（4つのDB一括作成）\n")
    
    if not NOTION_TOKEN:
        print("❌ エラー: NOTION_TOKEN が設定されていません")
        print("   .env ファイルに NOTION_API_KEY を設定してください")
        sys.exit(1)
    
    if not PARENT_PAGE_ID:
        print("⚠️ NOTION_PARENT_PAGE_ID が設定されていません")
        print()
        print("データベースを作成する親ページのIDを入力してください。")
        print("（Notionの任意のページを開き、URLから32文字のIDをコピー）")
        print()
        parent_page_id = input("親ページID: ").strip()
        
        if not parent_page_id:
            print("❌ キャンセルされました")
            sys.exit(1)
    else:
        parent_page_id = PARENT_PAGE_ID
    
    # ハイフンを削除して正規化
    parent_page_id = parent_page_id.replace("-", "")
    
    # UUID形式に変換
    if len(parent_page_id) == 32:
        parent_page_id = f"{parent_page_id[0:8]}-{parent_page_id[8:12]}-{parent_page_id[12:16]}-{parent_page_id[16:20]}-{parent_page_id[20:32]}"
    
    print(f"親ページID: {parent_page_id}\n")
    
    # Notion Client初期化
    client = Client(auth=NOTION_TOKEN, notion_version="2022-06-28")
    
    try:
        # 1. Specs データベース作成
        specs_db_id = create_specs_database(client, parent_page_id)
        
        # 2. Tasks データベース作成
        tasks_db_id = create_tasks_database(client, parent_page_id)
        
        # 3. Reviews データベース作成
        reviews_db_id = create_reviews_database(client, parent_page_id)
        
        # 4. Resonant Archive データベース作成
        archive_db_id = create_resonant_archive_database(client, parent_page_id)
        
        print("\n" + "="*60)
        print("🎉 全てのデータベース作成完了！")
        print("="*60)
        print()
        print("以下を .env ファイルに設定してください：")
        print()
        print(f"NOTION_SPECS_DB_ID={specs_db_id}")
        print(f"NOTION_TASKS_DB_ID={tasks_db_id}")
        print(f"NOTION_REVIEWS_DB_ID={reviews_db_id}")
        print(f"NOTION_ARCHIVE_DB_ID={archive_db_id}")
        print()
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

