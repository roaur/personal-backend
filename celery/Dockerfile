FROM python:3.12-slim

WORKDIR /app

COPY celery/requirements.txt .
RUN apt-get update && apt-get install -y stockfish 
RUN ln -s /usr/games/stockfish /usr/local/bin/stockfish
RUN rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

COPY celery /app
COPY common /app/common

# Default command (can be overridden in docker-compose)
CMD ["celery", "-A", "tasks", "worker", "--loglevel=info"]
