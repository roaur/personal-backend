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
- **Architecture**: **Producer-Consumer Pattern** with specialized queues.
- **Services**:
    - **`celery_producer`** (Ingestion Producer):
        - **Queue**: `api_queue` (Concurrency: 1).
        - **Job**: Fetches data from Lichess API.
        - **Constraint**: **Strictly serial execution** enforced by a **Global Redis Lock**.
        - **Streaming**: Streams NDJSON responses and dispatches individual game tasks immediately.
    - **`celery_consumer`** (Ingestion Consumer):
        - **Queue**: `db_queue` (Concurrency: Scalable, e.g., 8).
        - **Job**: Processes raw game data and writes to Postgres via FastAPI.
    - **`analysis_producer`** (Analysis Scheduler):
        - **Queue**: `analysis_scheduling_queue`.
        - **Job**: Periodically queries the API for games that need analysis and enqueues them.
    - **`analysis_consumer`** (Analysis Worker):
        - **Queue**: `analysis_queue` (Concurrency: 4).
        - **Job**: Runs CPU-intensive analysis using Stockfish.
        - **Plugin System**: Uses a plugin architecture (`celery/analysis/plugins/`) to run multiple analysis modules (e.g., `LargestSwingPlugin`) on each game.

### 3. Postgres (`postgres/`)
**Role**: The Memory (Database).
- **Responsibility**:
    - Persistent storage for users, games, moves, and analysis results.
- **Tech**: PostgreSQL 17.

### 4. Redis (`redis`)
**Role**: The Nervous System (Message Broker).
- **Responsibility**:
    - Handles communication between Producer and Consumer services.
    - Stores Celery task queues.
- **Tech**: Redis.
    
### 5. PgBouncer (`pgbouncer`)
**Role**: The Gatekeeper (Connection Pooler).
- **Responsibility**:
    - Manages a pool of persistent connections to Postgres.
    - Multiplexes thousands of client connections onto a few DB connections.

## Data Flow

1.  **Ingestion (Producer-Consumer)**:
    - **Trigger**: `Celery Beat` triggers the `orchestrator` task every minute.
    - **Orchestration**: `orchestrator` determines which players to update and dispatches `fetch_player_games` tasks to the `api_queue`.
    - **Production**: `celery_producer` picks up `fetch_player_games`. It streams games from Lichess and pushes each game as a `process_game_data` task to the `db_queue`.
    - **Consumption**: `celery_consumer` picks up `process_game_data` tasks in parallel. It parses the data and calls `FastAPI` endpoints to save it.

2.  **Analysis (Plugin-Based)**:
    - **Scheduling**: `analysis_producer` runs `enqueue_analysis_tasks` periodically. It asks the API for games that are missing metrics for active plugins.
    - **Execution**: `analysis_consumer` picks up `analyze_game` tasks.
    - **Plugins**: The worker loads registered plugins (e.g., `LargestSwingPlugin`).
    - **Processing**: It downloads the PGN, runs Stockfish via the plugin logic, and posts the results back to the API.

3.  **Consumption**:
    - Frontend queries `FastAPI` for game stats and analysis.

## Release Management

This project uses **Release Please** to automate the release process.

- **Conventional Commits**: All commits must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.
- **Automated PRs**: Release Please automatically creates a "Release PR" that updates the `CHANGELOG.md` and version files based on the commits since the last release.
- **Tagging & Publishing**: Merging the Release PR automatically tags the commit and publishes a GitHub Release.
