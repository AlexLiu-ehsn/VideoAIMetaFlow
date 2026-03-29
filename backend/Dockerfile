FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Python 依賴
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# 複製應用程式
COPY . .

# 建立 storage 目錄
RUN mkdir -p storage/videos storage/thumbnails

EXPOSE 8000

# 啟動前執行 DB migration，再啟動服務
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
