FROM python:3.11-slim

# System deps (optional but useful)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV CHROMA_DIR=/app/data/chroma_store

# Install deps
COPY requirements-backend.txt .
RUN pip install --no-cache-dir -r requirements-backend.txt

# Copy backend code (and anything else you need under /app)
COPY backend ./backend

# Ensure the persistent Chroma and logs directories exist and are writable
RUN mkdir -p /app/data/chroma_store /app/logs && chmod -R 777 /app/data /app/logs || true

ENV LOG_DIR=/app/logs

EXPOSE 8000

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
