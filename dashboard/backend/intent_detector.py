#!/usr/bin/env python3
"""
Intent Detection from Messages
メッセージ内容からIntentを自動検出
"""
import re
from typing import Optional, Dict, Any

# Intentキーワードマッピング
INTENT_PATTERNS = {
    "review": {
        "keywords": ["レビュー", "review", "確認", "チェック", "見て", "確認して"],
        "description": "コードレビューまたは確認要求"
    },
    "create": {
        "keywords": ["作成", "作って", "create", "新規", "追加", "実装して", "書いて"],
        "description": "新規作成要求"
    },
    "fix": {
        "keywords": ["修正", "直して", "fix", "バグ", "エラー", "問題", "治して"],
        "description": "修正・バグフィックス要求"
    },
    "test": {
        "keywords": ["テスト", "test", "検証", "試して", "動作確認"],
        "description": "テスト実行要求"
    },
    "debug": {
        "keywords": ["デバッグ", "debug", "調査", "原因", "なぜ", "why"],
        "description": "デバッグ・調査要求"
    },
    "refactor": {
        "keywords": ["リファクタ", "refactor", "改善", "最適化", "整理"],
        "description": "リファクタリング要求"
    },
    "implement": {
        "keywords": ["実装", "implement", "開発", "コーディング"],
        "description": "機能実装要求"
    },
    "document": {
        "keywords": ["ドキュメント", "document", "説明", "書類", "README"],
        "description": "ドキュメント作成要求"
    },
    "deploy": {
        "keywords": ["デプロイ", "deploy", "リリース", "公開"],
        "description": "デプロイ要求"
    }
}

def detect_intent_from_message(content: str) -> Optional[Dict[str, Any]]:
    """
    メッセージ内容からIntentを検出
    
    Args:
        content: メッセージ内容
    
    Returns:
        Intent情報の辞書、または None（検出されなかった場合）
        {
            "type": "review",
            "data": {
                "request": "元のメッセージ内容",
                "keywords_matched": ["レビュー"],
                "confidence": "high"
            }
        }
    """
    if not content or len(content.strip()) < 3:
        return None
    
    content_lower = content.lower()
    
    # 各Intentパターンをチェック
    for intent_type, pattern_info in INTENT_PATTERNS.items():
        for keyword in pattern_info["keywords"]:
            if keyword.lower() in content_lower:
                # マッチしたキーワードを収集
                matched_keywords = [
                    kw for kw in pattern_info["keywords"] 
                    if kw.lower() in content_lower
                ]
                
                return {
                    "type": intent_type,
                    "data": {
                        "request": content,
                        "keywords_matched": matched_keywords,
                        "confidence": "high" if len(matched_keywords) > 1 else "medium",
                        "description": pattern_info["description"]
                    }
                }
    
    # 疑問符がある場合は調査として扱う
    if "?" in content or "？" in content:
        return {
            "type": "debug",
            "data": {
                "request": content,
                "keywords_matched": ["?"],
                "confidence": "low",
                "description": "質問・調査要求（疑問符検出）"
            }
        }
    
    return None


def extract_target_from_message(content: str) -> Optional[str]:
    """
    メッセージから対象（ファイル名、機能名など）を抽出
    
    Args:
        content: メッセージ内容
    
    Returns:
        抽出されたターゲット文字列、または None
    """
    # ファイルパスパターン（例: /path/to/file.py, file.js）
    file_pattern = r'[\/\w]+\.\w+'
    file_matches = re.findall(file_pattern, content)
    if file_matches:
        return file_matches[0]
    
    # バッククォートで囲まれたコード・名前
    backtick_pattern = r'`([^`]+)`'
    backtick_matches = re.findall(backtick_pattern, content)
    if backtick_matches:
        return backtick_matches[0]
    
    # 「〜を」「〜の」パターン
    target_pattern = r'([^\s]+)[をの]'
    target_matches = re.findall(target_pattern, content)
    if target_matches:
        return target_matches[0]
    
    return None


def should_auto_generate_intent(content: str) -> bool:
    """
    自動Intent生成すべきかどうかを判定
    
    Args:
        content: メッセージ内容
    
    Returns:
        True: 自動生成すべき、False: 不要
    """
    # 短すぎるメッセージは除外
    if len(content.strip()) < 5:
        return False
    
    # 挨拶や雑談は除外
    casual_patterns = [
        r'^(こんにちは|hello|hi|おはよう|こんばんは)',
        r'^(ありがとう|thanks|thank you)',
        r'^(了解|ok|わかった|はい)',
    ]
    
    content_lower = content.lower().strip()
    for pattern in casual_patterns:
        if re.match(pattern, content_lower):
            return False
    
    # Intentパターンにマッチするか確認
    intent = detect_intent_from_message(content)
    return intent is not None


if __name__ == "__main__":
    # テスト
    test_messages = [
        "このコードをレビューして",
        "ユーザー認証機能を実装して",
        "バグを修正してください",
        "なぜエラーが出るの？",
        "こんにちは",
        "WebSocketのテストをお願い",
    ]
    
    print("🧪 Intent Detection Test\n")
    for msg in test_messages:
        intent = detect_intent_from_message(msg)
        should_gen = should_auto_generate_intent(msg)
        target = extract_target_from_message(msg)
        
        print(f"Message: {msg}")
        print(f"  Intent: {intent['type'] if intent else 'None'}")
        print(f"  Should Generate: {should_gen}")
        print(f"  Target: {target}")
        print()
