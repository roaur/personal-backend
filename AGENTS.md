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
- **Responsibility**:
    - **Ingestion**: Periodically fetches new matches from external APIs (Lichess) via **Celery Beat** (replacing Airflow).
    - **Analysis**: Performs heavy computational tasks (e.g., engine analysis of games) in the background.
    - **Queue**: Consumes tasks from RabbitMQ.
- **Tech**: Python, Celery.

### 3. Postgres (`postgres/`)
**Role**: The Memory (Database).
- **Responsibility**:
    - Persistent storage for users, games, moves, and analysis results.
- **Tech**: PostgreSQL 17.

### 4. RabbitMQ (`rabbitmq`)
**Role**: The Nervous System (Message Broker).
- **Responsibility**:
    - Handles communication between FastAPI (producer) and Celery (consumer).
- **Tech**: RabbitMQ.

## Data Flow

1.  **Ingestion**:
    - `Celery Beat` triggers `pull_matches` task every minute.
    - `Celery Worker` executes `pull_matches`.
    - Worker calls Lichess API to get game data.
    - Worker calls `FastAPI` endpoints to save game data (ensuring all writes go through API).

2.  **Analysis**:
    - User requests analysis via Frontend -> `FastAPI`.
    - `FastAPI` pushes `analyze_game` task to RabbitMQ.
    - `Celery Worker` picks up task, runs Stockfish/analysis, and calls `FastAPI` to save results.

3.  **Consumption**:
    - Frontend queries `FastAPI` for game stats and analysis.
