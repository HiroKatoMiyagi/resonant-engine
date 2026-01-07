#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rename Notion Databases - データベース名変更ツール
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent))

try:
    from notion_client import Client
except ImportError:
    print("⚠️ notion-client がインストールされていません")
    sys.exit(1)

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
TASKS_DB_ID = os.getenv("NOTION_TASKS_DB_ID")
REVIEWS_DB_ID = os.getenv("NOTION_REVIEWS_DB_ID")


def rename_database(client: Client, db_id: str, new_name: str):
    """データベース名を変更"""
    print(f"📝 データベース名を '{new_name}' に変更中...")
    
    # UUID形式に変換
    if len(db_id) == 32:
        db_id = f"{db_id[0:8]}-{db_id[8:12]}-{db_id[12:16]}-{db_id[16:20]}-{db_id[20:32]}"
    
    response = client.request(
        path=f"databases/{db_id}",
        method="PATCH",
        body={
            "title": [
                {
                    "type": "text",
                    "text": {
                        "content": new_name
                    }
                }
            ]
        }
    )
    
    print(f"✅ 変更完了: {new_name}")


def main():
    print("🔧 Notion データベース名変更ツール\n")
    
    if not NOTION_TOKEN:
        print("❌ エラー: NOTION_TOKEN が設定されていません")
        sys.exit(1)
    
    client = Client(auth=NOTION_TOKEN, notion_version="2022-06-28")
    
    try:
        # Tasks データベース名変更
        if TASKS_DB_ID:
            rename_database(client, TASKS_DB_ID, "tasks")
        else:
            print("⚠️ NOTION_TASKS_DB_ID が設定されていません")
        
        # Reviews データベース名変更
        if REVIEWS_DB_ID:
            rename_database(client, REVIEWS_DB_ID, "reviews")
        else:
            print("⚠️ NOTION_REVIEWS_DB_ID が設定されていません")
        
        print("\n✅ 全て完了しました！")
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()














