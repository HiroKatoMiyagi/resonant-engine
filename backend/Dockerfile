FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 🆕 独立モジュールをコピー（プロジェクトルートからの相対パス）
# Note: docker-compose.ymlのcontextが..（プロジェクトルート）であることを前提
COPY memory_store/ ./memory_store/
COPY memory_lifecycle/ ./memory_lifecycle/
COPY context_assembler/ ./context_assembler/
COPY retrieval/ ./retrieval/

# Install dependencies
# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 独立モジュールをインストール（setup.pyから）
RUN pip install -e ./memory_store && \
    pip install -e ./memory_lifecycle

# Copy application
COPY backend/app/ ./app/

# Run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
