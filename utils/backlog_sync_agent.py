#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backlog Sync Agent v1.1 (Read-Only)
------------------------------------
Resonant Engine v3.x 用
仕様書・タスクをBacklogから読み取り専用で取得し、AIが参照可能にする。

v1.1: 統一イベントストリーム統合
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

# utils/ からの import を可能にする
sys.path.append(str(Path(__file__).parent))
from resonant_event_stream import get_stream

load_dotenv()

BACKLOG_SPACE_ID = os.getenv("BACKLOG_SPACE_ID")
BACKLOG_API_KEY = os.getenv("BACKLOG_API_KEY")
BACKLOG_PROJECT_ID = os.getenv("BACKLOG_PROJECT_ID")
BACKLOG_PROJECT_KEY = os.getenv("BACKLOG_PROJECT_KEY", "RESONANTENGINE")

BASE_URL = f"https://{BACKLOG_SPACE_ID}.backlog.com/api/v2"

def get_issues(project_id=BACKLOG_PROJECT_ID):
    """全課題（仕様・タスク）の一覧を取得"""
    stream = get_stream()
    
    # --- イベントストリーム: Backlog同期開始 ---
    sync_id = stream.emit(
        event_type="action",
        source="backlog_sync",
        data={
            "action": "fetch_issues",
            "project_id": project_id
        },
        tags=["backlog", "sync", "start"]
    )
    
    url = f"{BASE_URL}/issues"
    params = {
        "apiKey": BACKLOG_API_KEY,
        "projectId[]": project_id
    }
    
    try:
        res = requests.get(url, params=params)
        res.raise_for_status()
        issues = res.json()
        
        # --- イベントストリーム: 取得成功 ---
        stream.emit(
            event_type="result",
            source="backlog_sync",
            data={
                "status": "success",
                "issues_count": len(issues)
            },
            parent_event_id=sync_id,
            tags=["backlog", "success"]
        )
        
        # 各課題を個別にイベント記録
        for issue in issues:
            stream.emit(
                event_type="observation",
                source="backlog_sync",
                data={
                    "issue_key": issue.get("issueKey"),
                    "summary": issue.get("summary"),
                    "status": issue.get("status", {}).get("name"),
                    "updated": issue.get("updated")
                },
                parent_event_id=sync_id,
                tags=["backlog", "issue"]
            )
        
        return issues
        
    except requests.exceptions.HTTPError as http_err:
        # --- イベントストリーム: エラー記録 ---
        stream.emit(
            event_type="result",
            source="backlog_sync",
            data={
                "status": "error",
                "error_type": "http_error",
                "error": str(http_err)
            },
            parent_event_id=sync_id,
            tags=["backlog", "error"]
        )
        raise

def get_issue_detail(issue_id):
    """個別課題（仕様書）を取得"""
    stream = get_stream()
    
    # --- イベントストリーム: 課題詳細取得 ---
    detail_id = stream.emit(
        event_type="action",
        source="backlog_sync",
        data={
            "action": "fetch_issue_detail",
            "issue_id": issue_id
        },
        tags=["backlog", "detail"]
    )
    
    url = f"{BASE_URL}/issues/{issue_id}"
    params = {"apiKey": BACKLOG_API_KEY}
    
    try:
        res = requests.get(url, params=params)
        res.raise_for_status()
        issue = res.json()
        
        # --- イベントストリーム: 詳細取得成功 ---
        stream.emit(
            event_type="result",
            source="backlog_sync",
            data={
                "status": "success",
                "issue_key": issue.get("issueKey"),
                "summary": issue.get("summary")
            },
            parent_event_id=detail_id,
            tags=["backlog", "success"]
        )
        
        return issue
        
    except requests.exceptions.HTTPError as http_err:
        stream.emit(
            event_type="result",
            source="backlog_sync",
            data={
                "status": "error",
                "error": str(http_err)
            },
            parent_event_id=detail_id,
            tags=["backlog", "error"]
        )
        raise

if __name__ == "__main__":
    try:
        issues = get_issues()
        print(f"🧠 Found {len(issues)} issues in Backlog project {BACKLOG_PROJECT_KEY}")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue['issueKey']} - {issue['summary']}")
    except requests.exceptions.HTTPError as http_err:
        print(f"⚠️ HTTP Error: {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"⚠️ Connection Error: {req_err}")
    except Exception as e:
        print(f"⚠️ Unexpected Error: {e}")