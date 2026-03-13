FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY services/api/ /app/services/api/

RUN python -m pip install --upgrade pip && \
    python -m pip install /app/services/api

CMD ["sh", "-c", "cd /app/services/api && python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
