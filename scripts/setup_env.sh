#!/bin/bash
# ==========================================================
# Resonant Engine v3.2 - Environment Setup Script
# Author: Hiroaki Kato
# ==========================================================

ROOT_DIR="/Users/zero/Projects/resonant-engine"
VENV_PATH="$ROOT_DIR/venv"

MODE=$1

if [ "$MODE" == "--rebuild" ]; then
  echo "♻️ Rebuilding Resonant Engine environment..."
  rm -rf "$VENV_PATH"
elif [ "$MODE" == "--status" ]; then
  echo "📊 Checking Resonant Engine environment status..."
  if [ -d "$VENV_PATH" ]; then
    source venv/bin/activate
    echo "🐍 Python version: $(python3 --version)"
    echo "📦 Installed packages:"
    pip list
  else
    echo "⚠️ Virtual environment not found. Run ./scripts/setup_env.sh first."
  fi
  exit 0
fi

echo "🌀 Setting up Resonant Engine environment..."
cd "$ROOT_DIR" || exit 1

# 1️⃣ Create virtual environment if not exists
if [ ! -d "$VENV_PATH" ]; then
  echo "🔧 Creating virtual environment..."
  python3 -m venv venv
else
  echo "✅ Virtual environment already exists."
fi

# 2️⃣ Activate virtual environment
source venv/bin/activate

# 3️⃣ Upgrade pip
pip install --upgrade pip

# 4️⃣ Install dependencies
pip install flask requests python-dotenv notion-client pyyaml jsonlines

# 5️⃣ Verify .env presence
if [ ! -f ".env" ]; then
  echo "⚠️  .env file not found! Please copy and fill it before running this script."
  exit 1
else
  echo "✅ .env file detected."
fi

# 6️⃣ Export env vars (Safe)
set -a
while IFS='=' read -r key value; do
  # スキップ条件: コメント行(#)・空行
  [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
  export "$key"="$value"
done < .env
set +a
echo "🌿 Environment variables loaded (safe mode)."

# 7️⃣ Verify Resonant Root
echo "📁 RESONANT_ROOT = $RESONANT_ROOT"
echo "🔑 GitHub Token = ${GITHUB_TOKEN:0:8}********"
echo "🧠 Notion Key   = ${NOTION_API_KEY:0:8}********"

echo "✅ Setup complete. Ready for Resonant Engine operations."
if [ "$MODE" == "--rebuild" ]; then
  echo "♻️ Rebuild complete. Environment fully refreshed."
fi