FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 🆕 独立モジュールをコピー（プロジェクトルートからの相対パス）
# Note: docker-compose.ymlのcontextが..（プロジェクトルート）であることを前提
COPY bridge/ ./bridge/
COPY memory_store/ ./memory_store/
COPY memory_lifecycle/ ./memory_lifecycle/
COPY context_assembler/ ./context_assembler/
COPY retrieval/ ./retrieval/

# Install dependencies
# まず基本的な依存関係をインストール
COPY backend/requirements.txt .
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    asyncpg==0.29.0 \
    pydantic==2.5.2 \
    pydantic-settings==2.1.0 \
    python-dotenv==1.0.0 \
    httpx==0.25.2 \
    pytest==7.4.3 \
    pytest-asyncio==0.21.1

# 独立モジュールをインストール（setup.pyから）
RUN pip install -e ./bridge && \
    pip install -e ./memory_store && \
    pip install -e ./memory_lifecycle

# Copy application
COPY backend/app/ ./app/

# Run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
