#!/usr/bin/env python3
"""
Intent → Bridge → Kana (Claude API) 統合処理 (PostgreSQL版)
DB統合: Intentをintentsテーブルで管理
"""
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import asyncpg
import asyncio

# Anthropic API (Claude) インポート
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    print("⚠️ anthropic パッケージがインストールされていません")

# プロジェクトルート
ROOT = Path(__file__).parent.parent.parent
BRIDGE = ROOT / "bridge"
LOGS = ROOT / "logs"
LOGS.mkdir(exist_ok=True)

# 環境変数を.envファイルから読み込む
load_dotenv(ROOT / ".env")

# データベース接続情報
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://resonant@localhost:5432/resonant")

# ファイルパス（レガシー互換用）
INTENT_FILE = BRIDGE / "intent_protocol.json"
PROCESS_LOG = LOGS / "intent_processor.log"
RESPONSE_LOG = LOGS / "kana_responses.log"


class IntentProcessorDB:
    """Intent処理とClaude API統合クラス（DB版）"""
    
    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key and CLAUDE_AVAILABLE:
            self.log("⚠️ ANTHROPIC_API_KEY が設定されていません")
        
        self.client = None
        if CLAUDE_AVAILABLE and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.log("✅ Claude API クライアント初期化完了")
        
        self.db_pool = None
    
    def log(self, msg: str):
        """処理ログを記録"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {msg}\n"
        print(log_entry.strip())
        with open(PROCESS_LOG, "a", encoding="utf-8") as f:
            f.write(log_entry)
    
    async def init_db(self):
        """データベース接続プールを初期化"""
        if not self.db_pool:
            self.db_pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=2,
                max_size=10
            )
            self.log("✅ Database pool created")
    
    async def close_db(self):
        """データベース接続プールをクローズ"""
        if self.db_pool:
            await self.db_pool.close()
            self.log("✅ Database pool closed")
    
    async def create_intent(
        self,
        intent_type: str,
        data: Dict[str, Any],
        source: str = "api",
        user_id: Optional[str] = None
    ) -> str:
        """
        新しいIntentをDBに作成
        
        Args:
            intent_type: Intent種別（例: 'review_spec', 'create_task'）
            data: Intent詳細データ
            source: 発生源（'message', 'spec_trigger', 'api'）
            user_id: ユーザーID（オプション）
        
        Returns:
            作成されたIntentのID
        """
        await self.init_db()
        
        async with self.db_pool.acquire() as conn:
            intent_id = await conn.fetchval("""
                INSERT INTO intents (type, data, status, source, user_id)
                VALUES ($1, $2, 'pending', $3, $4)
                RETURNING id
            """, intent_type, json.dumps(data), source, user_id)
            
            self.log(f"✅ Intent作成: {intent_id} (type={intent_type})")
            return str(intent_id)
    
    async def get_pending_intents(self, limit: int = 10) -> list:
        """
        処理待ちIntentを取得
        
        Args:
            limit: 取得件数上限
        
        Returns:
            Intent一覧
        """
        await self.init_db()
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, type, data, source, created_at
                FROM intents
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT $1
            """, limit)
            
            return [dict(row) for row in rows]
    
    async def update_intent_status(
        self,
        intent_id: str,
        status: str,
        completed_at: Optional[str] = None
    ):
        """
        Intentのステータスを更新
        
        Args:
            intent_id: IntentのID
            status: 新しいステータス（'processing', 'completed', 'error'）
            completed_at: 完了時刻（オプション）
        """
        await self.init_db()
        
        async with self.db_pool.acquire() as conn:
            if completed_at:
                await conn.execute("""
                    UPDATE intents
                    SET status = $1, completed_at = NOW()
                    WHERE id = $2
                """, status, intent_id)
            else:
                await conn.execute("""
                    UPDATE intents
                    SET status = $1
                    WHERE id = $2
                """, status, intent_id)
            
            self.log(f"✅ Intent更新: {intent_id} → {status}")
    
    def call_kana(self, intent_data: Dict[str, Any]) -> Optional[str]:
        """
        Claude API経由でKana（翻訳層）を呼び出す
        
        Args:
            intent_data: Intent情報
        
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
        """Intent情報からKana用のプロンプトを構築"""
        intent_type = intent_data.get("type", "unknown")
        data = intent_data.get("data", {})
        
        prompt = f"""あなたはKana（翻訳層）として機能します。
Yunoから受け取ったIntentを実行可能な処理に翻訳してください。

## Intent情報
- Type: {intent_type}
- Data: {json.dumps(data, ensure_ascii=False, indent=2)}

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
        # UUID型をstrに変換
        intent_data_copy = dict(intent_data)
        if 'id' in intent_data_copy:
            intent_data_copy['id'] = str(intent_data_copy['id'])
        
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "intent": intent_data_copy,
            "kana_response": response
        }
        
        with open(RESPONSE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False, indent=2) + "\n")
    
    async def process_intent(self, intent_id: str) -> bool:
        """
        指定されたIntentを処理する
        
        Args:
            intent_id: 処理するIntentのID
        
        Returns:
            処理成功したらTrue
        """
        await self.init_db()
        
        try:
            # Intentデータ取得
            async with self.db_pool.acquire() as conn:
                intent_row = await conn.fetchrow("""
                    SELECT id, type, data, source
                    FROM intents
                    WHERE id = $1
                """, intent_id)
                
                if not intent_row:
                    self.log(f"❌ Intent not found: {intent_id}")
                    return False
                
                intent_data = dict(intent_row)
            
            # ステータスを'processing'に更新
            await self.update_intent_status(intent_id, "processing")
            
            # Kana呼び出し
            response = self.call_kana(intent_data)
            
            if response:
                # 成功: 'completed'に更新
                await self.update_intent_status(intent_id, "completed", completed_at=True)
                self.log(f"✅ Intent処理完了: {intent_id}")
                return True
            else:
                # 失敗: 'error'に更新
                await self.update_intent_status(intent_id, "error")
                self.log(f"❌ Intent処理失敗: {intent_id}")
                return False
                
        except Exception as e:
            self.log(f"❌ Intent処理エラー: {e}")
            await self.update_intent_status(intent_id, "error")
            return False
    
    async def process_all_pending(self) -> int:
        """
        すべての処理待ちIntentを処理
        
        Returns:
            処理したIntent数
        """
        intents = await self.get_pending_intents()
        self.log(f"📥 処理待ちIntent: {len(intents)}件")
        
        processed = 0
        for intent in intents:
            success = await self.process_intent(str(intent['id']))
            if success:
                processed += 1
        
        self.log(f"✅ 処理完了: {processed}/{len(intents)}件")
        return processed


async def main():
    """スタンドアロン実行用エントリーポイント"""
    processor = IntentProcessorDB()
    
    try:
        # 処理待ちIntentを処理
        processed = await processor.process_all_pending()
        print(f"\n✅ {processed}件のIntentを処理しました")
        
    finally:
        await processor.close_db()


if __name__ == "__main__":
    asyncio.run(main())
