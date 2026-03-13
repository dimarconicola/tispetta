FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY services/api/ /app/services/api/
COPY services/worker/ /app/services/worker/

RUN python -m pip install --upgrade pip && \
    python -m pip install /app/services/api /app/services/worker

CMD ["python", "-m", "worker.main"]
