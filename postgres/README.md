# Postgres Database Service

## Overview
This container runs the PostgreSQL database for the project. It stores all application data, including users, games, and other entities.

## Directory Structure
- `initdb/`: SQL scripts or shell scripts in this directory are automatically executed when the container is started for the first time. Use this for initial schema creation or data seeding if not using Alembic.
- `docker-compose.yml`: (Optional) Local compose file if running standalone (usually managed by root `docker-compose.yml`).

## Environment Variables
These variables are set in the root `docker-compose.yml` and `.env` file:

| Variable | Description |
|----------|-------------|
| `POSTGRES_USER` | Superuser username |
| `POSTGRES_PASSWORD` | Superuser password |
| `POSTGRES_DB` | Default database name |

## Maintenance Tips
- **Data Persistence**: Data is persisted in the `postgres_data` Docker volume.
- **Backups**: Use `pg_dump` to create backups of the database.
- **Access**: You can connect to the database using any Postgres client (e.g., DBeaver, `psql`) on port 5432 (mapped to host).
