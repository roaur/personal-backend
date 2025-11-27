# Personal Backend: Chess Data Pipeline

A robust, scalable data engineering platform designed to ingest, store, and analyze chess match data from Lichess.

## 🚀 Overview

This project implements a **Producer-Consumer** architecture to efficiently fetch game data while strictly adhering to external API rate limits. It uses **FastAPI** for the backend interface and **Celery** with **Redis** for asynchronous task processing.

### Key Features
- **Strict Rate-Limiting**: Uses a **Global Redis Lock** to ensure **no concurrent requests are made** to the Lichess API, strictly adhering to API spec.
- **Parallel Processing**: Scalable consumer workers process and store games in parallel.
- **Streaming**: Uses NDJSON streaming to process games immediately as they are downloaded.
- **Graph Traversal**: Automatically discovers and fetches games for opponents to build a network of players.
- **Complete History**: Automatically paginates to fetch **all games** for every player, not just the recent ones.
- **Resumable**: Smart cursors ensure data collection resumes exactly where it left off after restarts or failures.
- **Idempotency**: "Upsert" logic ensures data consistency even if tasks are retried.

## 🛠️ Tech Stack

- **Language**: Python 3.11+
- **API Framework**: FastAPI
- **Task Queue**: Celery
- **Broker**: Redis
- **Database**: PostgreSQL 17
- **Containerization**: Docker & Docker Compose

## 🏗️ Architecture

See [AGENTS.md](AGENTS.md) for a detailed breakdown of the system agents and data flow.

```mermaid
graph LR
    Beat[Celery Beat] -->|Trigger| Orch[Orchestrator]
    Orch -->|Dispatch| Prod[Producer (Concurrency 1)]
    Prod -->|Stream Games| Q1[(Redis: api_queue)]
    Q1 -->|Fetch| Lichess[Lichess API]
    Lichess -->|NDJSON| Prod
    Prod -->|Enqueue Game| Q2[(Redis: db_queue)]
    Q2 -->|Consume| Cons[Consumer (Concurrency 8)]
    Cons -->|Write| API[FastAPI]
    API -->|Persist| PGB[PgBouncer]
    PGB -->|Pool| DB[(PostgreSQL)]
```

## 📦 Services

| Service | Role | Description |
|---------|------|-------------|
| `fastapi` | API / Data Layer | Central REST API and database interface. |
| `celery_producer` | Ingestion | Fetches data from Lichess. **Global Lock ensures serial execution**. |
| `celery_consumer` | Processing | Processes raw data and writes to DB. **Concurrency: 8**. |
| `celery_beat` | Scheduler | Triggers the orchestrator every minute. |
| `redis` | Broker | Message broker for Celery queues. |
| `pgbouncer` | Connection Pool | Multiplexes DB connections for high performance. |
| `postgres` | Database | Persistent storage (Optimized config). |

## ⚡ Quick Start

### Prerequisites
- Docker & Docker Compose
- Lichess API Token (for higher rate limits, though anonymous works with lower limits)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd personal-backend
```

### 2. Configure Environment
Create a `.env` file in the root directory:
```bash
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgrespw
POSTGRES_DB=chess
LICHESS_USERNAME=your_lichess_username
LICHESS_TOKEN=your_lichess_token
CELERY_BROKER_URL=redis://redis:6379/0
FASTAPI_ROUTE=fastapi:8000
```

### 3. Run with Docker
```bash
docker-compose up --build -d
```

### 4. Verify
Check the logs to see the ingestion in action:
```bash
docker-compose logs -f celery_producer celery_consumer
```

## 🧪 Development

### Local Setup (Python)
We use `pyenv` and `virtualenv` for local development.

```bash
# Install dependencies
cd celery
pip install -r requirements.txt

# Run Tests (Dockerized)
make test

# Run Tests (Local Python Environment)
pytest celery/tests/
```

### CI/CD
- **GitHub Actions**: Tests are automatically run on every Pull Request to `master`.
- **Release Please**: Automates versioning and changelogs based on Conventional Commits.
- **Pre-commit**: Enforces commit message standards locally.

### Database Migrations
Migrations are handled by **Alembic** (within FastAPI).
```bash
docker-compose exec fastapi alembic upgrade head
```

## 📂 Project Structure

```
.
├── AGENTS.md           # Detailed Architecture Documentation
├── celery/             # Celery Workers (Producer & Consumer)
│   ├── tasks.py        # Task Definitions
│   └── utils/          # Lichess & API Utilities
├── fastapi/            # Backend API
│   ├── app/            # Application Code (Models, CRUD, Schemas)
│   └── migrations/     # Database Migrations
├── postgres/           # Database Initialization Scripts
└── docker-compose.yml  # Infrastructure Definition
```
