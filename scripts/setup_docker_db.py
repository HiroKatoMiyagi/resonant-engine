#!/usr/bin/env python3
"""
Docker環境の状態確認とPostgreSQLコンテナ起動スクリプト
"""
import subprocess
import time
import sys

def run_command(cmd, description):
    """コマンドを実行して結果を表示"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"✅ {description} 完了")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"⚠️ {description} 警告")
            if result.stderr:
                print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ {description} タイムアウト")
        return False
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def main():
    print("=" * 60)
    print("Docker PostgreSQL 環境セットアップ")
    print("=" * 60)
    
    # 1. 既存コンテナの停止・削除
    run_command(
        "docker stop $(docker ps -aq --filter name=resonant) 2>/dev/null || true",
        "既存コンテナ停止"
    )
    
    run_command(
        "docker rm $(docker ps -aq --filter name=resonant) 2>/dev/null || true",
        "既存コンテナ削除"
    )
    
    # 2. PostgreSQLコンテナ起動
    print("\n🚀 PostgreSQLコンテナを起動します...")
    run_command(
        "cd /Users/zero/Projects/resonant-engine && docker compose up -d db",
        "PostgreSQL起動"
    )
    
    # 3. 起動待機
    print("\n⏳ PostgreSQL起動待機中（15秒）...")
    time.sleep(15)
    
    # 4. 状態確認
    run_command(
        "docker ps --filter name=db",
        "コンテナ状態確認"
    )
    
    # 5. ログ確認
    run_command(
        "docker logs $(docker ps -q --filter name=db) 2>&1 | tail -20",
        "PostgreSQLログ確認"
    )
    
    print("\n" + "=" * 60)
    print("✅ セットアップ完了")
    print("=" * 60)
    print("\n次のステップ:")
    print("  python3 dashboard/backend/init_db.py")

if __name__ == "__main__":
    main()
