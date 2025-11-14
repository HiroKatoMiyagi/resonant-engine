#!/usr/bin/env python3
"""
Intent → Bridge → Kana (Claude API) 統合処理
Priority 1実装: Intent監視とClaude API呼び出し
"""
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Anthropic API (Claude) インポート
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    print("⚠️ anthropic パッケージがインストールされていません")

# プロジェクトルート
ROOT = Path("/Users/zero/Projects/resonant-engine")
BRIDGE = ROOT / "bridge"
LOGS = ROOT / "logs"
LOGS.mkdir(exist_ok=True)

# 環境変数を.envファイルから読み込む
load_dotenv(ROOT / ".env")

# ファイルパス
INTENT_FILE = BRIDGE / "intent_protocol.json"
PROCESS_LOG = LOGS / "intent_processor.log"
RESPONSE_LOG = LOGS / "kana_responses.log"


class IntentProcessor:
    """Intent処理とClaude API統合クラス"""
    
    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key and CLAUDE_AVAILABLE:
            self.log("⚠️ ANTHROPIC_API_KEY が設定されていません")
        
        self.client = None
        if CLAUDE_AVAILABLE and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.log("✅ Claude API クライアント初期化完了")
    
    def log(self, msg: str):
        """処理ログを記録"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {msg}\n"
        print(log_entry.strip())
        with open(PROCESS_LOG, "a", encoding="utf-8") as f:
            f.write(log_entry)
    
    def read_intent(self) -> Optional[Dict[str, Any]]:
        """Intent JSONを読み込む"""
        if not INTENT_FILE.exists():
            return None
        
        try:
            with open(INTENT_FILE, "r", encoding="utf-8") as f:
                intent_data = json.load(f)
            self.log(f"📥 Intent読み込み: {intent_data}")
            return intent_data
        except Exception as e:
            self.log(f"❌ Intent読み込みエラー: {e}")
            return None
    
    def call_kana(self, intent_data: Dict[str, Any]) -> Optional[str]:
        """
        Claude API経由でKana（翻訳層）を呼び出す
        
        Args:
            intent_data: Intent JSON（phase, intentを含む）
        
        Returns:
            Claudeの応答テキスト
        """
        if not self.client:
            self.log("❌ Claude APIクライアントが初期化されていません")
            return None
        
        try:
            # Intent情報を構造化されたプロンプトに変換
            prompt = self._build_kana_prompt(intent_data)
            
            self.log(f"🔄 Kana（Claude）呼び出し開始...")
            
            # Claude API呼び出し
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                temperature=0.7,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            response_text = message.content[0].text
            self.log(f"✅ Kana応答受信 ({len(response_text)}文字)")
            
            # 応答をログに記録
            self._save_response(intent_data, response_text)
            
            return response_text
            
        except Exception as e:
            self.log(f"❌ Kana呼び出しエラー: {e}")
            return None
    
    def _build_kana_prompt(self, intent_data: Dict[str, Any]) -> str:
        """
        Intent情報からKana用のプロンプトを構築
        
        Kanaの役割: 外界APIとの通信、Intent→実行可能コマンドへの翻訳
        """
        phase = intent_data.get("phase", "unknown")
        intent = intent_data.get("intent", "unknown")
        
        prompt = f"""あなたはKana（翻訳層）として機能します。
Yunoから受け取ったIntentを実行可能な処理に翻訳してください。

## Intent情報
- Phase: {phase}
- Intent: {intent}

## Kanaの役割
1. Intentの解釈
2. 必要な外部API/ツールの特定
3. 実行手順の明確化

## 出力形式（JSON）
{{
    "interpretation": "Intentの解釈",
    "required_apis": ["必要なAPI/ツール"],
    "execution_steps": ["ステップ1", "ステップ2", ...],
    "estimated_complexity": "low/medium/high"
}}

上記形式のJSONで応答してください。"""
        
        return prompt
    
    def _save_response(self, intent_data: Dict[str, Any], response: str):
        """Kanaの応答をログに保存"""
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "intent": intent_data,
            "kana_response": response
        }
        
        with open(RESPONSE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False, indent=2) + "\n")
    
    def process_intent(self) -> bool:
        """
        Intentを処理する（メインエントリーポイント）
        
        Returns:
            処理成功したらTrue
        """
        # Intent読み込み
        intent_data = self.read_intent()
        if not intent_data:
            return False
        
        # Kana呼び出し
        response = self.call_kana(intent_data)
        if not response:
            return False
        
        self.log("✅ Intent処理完了")
        return True


def main():
    """スタンドアロン実行用エントリーポイント"""
    processor = IntentProcessor()
    
    if not INTENT_FILE.exists():
        print(f"❌ Intent file not found: {INTENT_FILE}")
        return
    
    success = processor.process_intent()
    if success:
        print("✅ Intent処理成功")
    else:
        print("❌ Intent処理失敗")


if __name__ == "__main__":
    main()
