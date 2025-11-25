# FastAPI Service

## Overview
This container runs the backend API for the Personal Backend project. It is built using [FastAPI](https://fastapi.tiangolo.com/), a modern, fast (high-performance) web framework for building APIs with Python 3.6+ based on standard Python type hints.

## Coding Style
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **ORM**: SQLAlchemy (Async)
- **Migrations**: Alembic
- **Style Guide**: PEP 8. Type hinting is strictly enforced for Pydantic models and function signatures.

## Directory Structure
- `app/`: Main application source code.
  - `main.py`: Application entry point and route registration.
  - `models.py`: SQLAlchemy database models.
  - `schemas.py`: Pydantic models for request/response validation.
  - `crud.py`: CRUD operations for database interactions.
  - `database.py`: Database connection and session management.
  - `utils.py`: Utility functions.
  - `data_transformers.py`: Logic for transforming data (e.g., PGN parsing).
- `migrations/`: Alembic migration scripts.
- `Dockerfile`: Docker build instructions.
- `requirements.txt`: Python dependencies.

## Environment Variables
The following environment variables are required for the service to function correctly:

| Variable | Description |
|----------|-------------|
| `POSTGRES_USER` | Database username |
| `POSTGRES_PASSWORD` | Database password |
| `POSTGRES_DB` | Database name |
| `POSTGRES_HOST` | Hostname of the Postgres service (usually `postgres` in Docker Compose) |
| `SQLALCHEMY_DATABASE_URL` | Full connection string for SQLAlchemy (e.g., `postgresql+psycopg://user:pass@host/db`) |

## Database Migrations

### Creating a New Migration
1.  **Modify Models**: Make your changes to the SQLAlchemy models in `app/models.py`.
2.  **Generate Script**: Run the following command to generate a new migration script based on your changes:
    ```bash
    docker compose exec fastapi alembic revision --autogenerate -m "your_migration_message"
    ```
    This will create a new file in `migrations/versions/` using the configured timestamp format (e.g., `YYYY_MM_DD_HHMM_slug.py`).
3.  **Review**: Always review the generated file to ensure it correctly captures your intended schema changes.

### Applying Migrations
To apply all pending migrations to the database:
```bash
docker compose exec fastapi alembic upgrade head
```

## Maintenance Tips
- **Dependencies**: Add new packages to `requirements.txt` and rebuild the container.
- **Reload**: The service is typically run with `--reload` in development for hot reloading.
