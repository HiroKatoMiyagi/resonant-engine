#!/usr/bin/env python3
"""
Resonant Daemon - PostgreSQL統合版（Service対応）
intentsテーブルを監視してIntent処理を実行
バックグラウンドサービスとして動作
"""
import os
import sys
import time
import json
import asyncio
import signal
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Priority 1: Intent → Bridge → Kana 統合
ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

BRIDGE = ROOT / "bridge"
LOGS = ROOT / "daemon" / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

# Intent Processor統合 (DB版)
sys.path.insert(0, str(ROOT))
try:
    from dashboard.backend.intent_processor_db import IntentProcessorDB
    PROCESSOR_AVAILABLE = True
except ImportError as e:
    PROCESSOR_AVAILABLE = False
    print(f"⚠️ IntentProcessorDB import failed: {e}")

# ログファイル（日次ローテーション）
LOG_FILE = LOGS / f"daemon_{datetime.now().strftime('%Y%m%d')}.log"
STATE_FILE = LOGS / "resonant_state.log"
PID_FILE = ROOT / "daemon" / "pids" / "resonant_daemon.pid"
PID_FILE.parent.mkdir(parents=True, exist_ok=True)

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# グローバル停止フラグ
shutdown_flag = False

def signal_handler(signum, frame):
    """シグナルハンドラー（Ctrl+C, SIGTERM対応）"""
    global shutdown_flag
    logger.info(f"⚠️ Signal {signum} received, shutting down gracefully...")
    shutdown_flag = True

def write_pid():
    """PIDファイルに現在のプロセスIDを書き込み"""
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    logger.info(f"📝 PID written to {PID_FILE}")

def remove_pid():
    """PIDファイルを削除"""
    if PID_FILE.exists():
        PID_FILE.unlink()
        logger.info(f"🗑️ PID file removed")

def write_state(phase, state):
    """状態をログに記録"""
    data = {
        "source": "daemon",
        "phase": phase,
        "state": state,
        "timestamp": datetime.now().isoformat()
    }
    with open(STATE_FILE, "a") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

def cleanup_old_logs(days=30):
    """古いログファイルを削除（デフォルト30日保持）"""
    if not LOGS.exists():
        return
    
    cutoff = time.time() - (days * 86400)
    for log_file in LOGS.glob("daemon_*.log"):
        if log_file.stat().st_mtime < cutoff:
            log_file.unlink()
            logger.info(f"🗑️ Removed old log: {log_file.name}")

async def watch_intents_db():
    """
    PostgreSQL intentsテーブルを監視してIntent処理
    """
    if not PROCESSOR_AVAILABLE:
        logger.error("❌ IntentProcessorDB not available")
        return
    
    processor = IntentProcessorDB()
    
    try:
        await processor.init_db()
        logger.info("✅ Database connection established")
        write_state("connected", "Database connection active")
        
        while not shutdown_flag:
            try:
                # 処理待ちIntentを処理
                processed = await processor.process_all_pending()
                
                if processed > 0:
                    logger.info(f"✅ {processed}件のIntentを処理しました")
                    write_state("intent_processed", f"{processed} intents completed")
                
                # 5秒待機
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                logger.warning("⚠️ Task cancelled")
                break
            except Exception as e:
                logger.error(f"❌ エラー: {e}", exc_info=True)
                write_state("error", str(e))
                await asyncio.sleep(5)
    
    finally:
        await processor.close_db()
        logger.info("✅ Database connection closed")
        write_state("disconnected", "Database connection closed")

def main():
    """メインエントリーポイント"""
    # シグナルハンドラー登録
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # PIDファイル作成
    write_pid()
    
    # 古いログ削除
    cleanup_old_logs()
    
    logger.info("🌿 Resonant Daemon started (PostgreSQL版 - Service Mode)")
    write_state("init", "Daemon started with DB integration")
    
    if not PROCESSOR_AVAILABLE:
        logger.error("⚠️ IntentProcessorDB not available, exiting")
        remove_pid()
        sys.exit(1)
    
    try:
        # asyncioイベントループで実行
        asyncio.run(watch_intents_db())
    except KeyboardInterrupt:
        logger.info("⚠️ Daemon stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        write_state("fatal_error", str(e))
        remove_pid()
        sys.exit(1)
    
    logger.info("🌿 Resonant Daemon stopped")
    write_state("stopped", "Daemon stopped normally")
    remove_pid()

if __name__ == "__main__":
    main()
