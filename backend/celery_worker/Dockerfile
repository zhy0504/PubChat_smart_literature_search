FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY backend/celery_worker/requirements.txt /app/requirements.txt
COPY common_utils/requirements.txt /app/common_requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt -r /app/common_requirements.txt

COPY common_utils /app/common_utils
COPY backend/celery_worker /app/celery_worker

RUN mkdir -p /app/celery_worker/search_code/search_result /app/celery_worker/search_code/logs

ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

CMD ["celery", "-A", "celery_worker.celery_worker.celery_app", "worker", "--loglevel=info", "-Q", "search_queue", "--concurrency=4"]
