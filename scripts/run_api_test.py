#!/usr/bin/env python3
"""
FastAPIサーバー起動&テスト実行スクリプト
"""
import subprocess
import time
import sys
import signal
import os

def main():
    server_process = None
    try:
        print("🚀 FastAPIサーバーを起動中...")
        
        # サーバー起動
        server_process = subprocess.Popen(
            [
                "/Users/zero/Projects/resonant-engine/venv/bin/uvicorn",
                "dashboard.backend.main:app",
                "--host", "0.0.0.0",
                "--port", "8000"
            ],
            cwd="/Users/zero/Projects/resonant-engine",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # サーバー起動待機
        print("⏳ サーバー起動待機中（5秒）...")
        time.sleep(5)
        
        # テスト実行
        print("\n🧪 APIテスト実行中...\n")
        result = subprocess.run(
            [
                "/Users/zero/Projects/resonant-engine/venv/bin/python",
                "/Users/zero/Projects/resonant-engine/dashboard/backend/test_api.py"
            ],
            capture_output=False
        )
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n⚠️ 中断されました")
        return 1
        
    finally:
        if server_process:
            print("\n🛑 サーバーを停止中...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
            print("✅ サーバー停止完了")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
