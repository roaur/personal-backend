# Celery Worker Service

## Overview
This container runs the Celery worker and beat services for handling background tasks and scheduled jobs. It is responsible for processing asynchronous tasks such as fetching games from Lichess.

## Coding Style
- **Language**: Python 3.11+
- **Framework**: Celery
- **Broker**: RabbitMQ
- **Backend**: RPC (or configured backend)

## Directory Structure
- `tasks.py`: Defines the Celery tasks (e.g., `pull_matches`).
- `utils/`: Utility modules.
  - `config.py`: Configuration loading and setup.
- `Dockerfile`: Docker build instructions.
- `requirements.txt`: Python dependencies.
- `celerybeat-schedule`: (Generated) Stores the schedule for periodic tasks.

## Environment Variables
The following environment variables are required:

| Variable | Description |
|----------|-------------|
| `CELERY_BROKER_URL` | Connection string for the message broker (RabbitMQ) |
| `FASTAPI_ROUTE` | URL of the FastAPI service (for callbacks or API calls) |
| `LICHESS_USERNAME` | Username for Lichess API authentication |
| `LICHESS_TOKEN` | Personal Access Token for Lichess API |

## Maintenance Tips
- **Adding Tasks**: Define new tasks in `tasks.py` and decorate them with `@app.task`.
- **Periodic Tasks**: Configure periodic tasks in the Celery Beat schedule (usually in `tasks.py` or config).
- **Debugging**: Logs are output to stdout/stderr. Use `docker logs <container_id>` to view them.
