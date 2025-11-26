# System Architecture & Agents

This document outlines the architecture of the Personal Backend system, designed to ingest, store, and analyze chess match data.

## Core Components

### 1. FastAPI (`fastapi/`)
**Role**: The Central Nervous System & Data Access Layer.
- **Responsibility**:
    - Provides the REST API for the frontend.
    - Acts as the **single source of truth** for data access (reading/writing to Postgres).
    - Enforces idempotency and business logic.
    - Triggers background tasks via Celery.
- **Tech**: Python, FastAPI, SQLAlchemy, Pydantic.

### 2. Celery (`celery/`)
**Role**: The Muscle (Background Workers).
- **Architecture**: **Producer-Consumer Pattern**.
- **Services**:
    - **`celery_producer`**:
        - **Queue**: `api_queue` (Concurrency: 1).
        - **Job**: Fetches data from Lichess API.
        - **Constraint**: **Strictly serial execution** enforced by a **Global Redis Lock**.
        - **Guarantee**: Absolutely NO concurrent requests to Lichess, regardless of worker scale.
        - **Streaming**: Streams NDJSON responses and dispatches individual game tasks immediately.
    - **`celery_consumer`**:
        - **Queue**: `db_queue` (Concurrency: Scalable, e.g., 8).
        - **Job**: Processes raw game data and writes to Postgres via FastAPI.
        - **Benefit**: High throughput parallel processing.
- **Tech**: Python, Celery.

### 3. Postgres (`postgres/`)
**Role**: The Memory (Database).
- **Responsibility**:
    - Persistent storage for users, games, moves, and analysis results.
- **Tech**: PostgreSQL 17.

### 4. Redis (`redis`)
**Role**: The Nervous System (Message Broker).
- **Responsibility**:
    - Handles communication between Producer and Consumer services.
    - Stores Celery task queues (`api_queue`, `db_queue`).
- **Tech**: Redis.

## Data Flow

1.  **Ingestion (Producer-Consumer)**:
    - **Trigger**: `Celery Beat` triggers the `orchestrator` task every minute.
    - **Orchestration**: `orchestrator` determines which players to update and dispatches `fetch_player_games` tasks to the `api_queue`.
    - **Production**: `celery_producer` picks up `fetch_player_games`. It streams games from Lichess and pushes each game as a `process_game_data` task to the `db_queue`.
    - **Consumption**: `celery_consumer` picks up `process_game_data` tasks in parallel. It parses the data and calls `FastAPI` endpoints to save it.

2.  **Analysis**:
    - User requests analysis via Frontend -> `FastAPI`.
    - `FastAPI` pushes `analyze_game` task to Redis.
    - `Celery Worker` picks up task, runs Stockfish/analysis, and calls `FastAPI` to save results.

3.  **Consumption**:
    - Frontend queries `FastAPI` for game stats and analysis.
