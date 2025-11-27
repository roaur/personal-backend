FROM python:3.11-slim

WORKDIR /app

COPY worker/requirements.txt .
COPY worker/analysis/requirements.txt analysis_requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r analysis_requirements.txt

COPY worker/ worker/
COPY shared/ shared/

# Default command (can be overridden in docker-compose)
ENV PYTHONPATH=/app
CMD ["celery", "-A", "worker.tasks", "worker", "--loglevel=info"]
