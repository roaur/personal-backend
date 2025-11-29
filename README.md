# Personal Backend: Chess Data Pipeline

A robust, scalable data engineering platform designed to ingest, store, and analyze chess match data from Lichess.

## 🚀 Overview

This project implements a **Producer-Consumer** architecture to efficiently fetch game data while strictly adhering to external API rate limits. It uses **FastAPI** for the backend interface and **Celery** with **Redis** for asynchronous task processing.

### Key Features
- **Strict Rate-Limiting**: Uses a **Global Redis Lock** to ensure **no concurrent requests are made** to the Lichess API.
- **Parallel Processing**: Scalable consumer workers process and store games in parallel.
- **Plugin-Based Analysis**: Modular analysis system allowing easy addition of new metrics (e.g., "Largest Swing").
- **Graph Traversal**: Automatically discovers and fetches games for opponents to build a network of players.
- **Resumable & Idempotent**: Smart cursors ensure data collection resumes exactly where it left off.

## 🏗️ Architecture

The system is split into specialized workers to handle different types of workloads efficiently.

### 1. Ingestion (Fetching)
- **Producer (`celery_producer`)**:
  - **Single Concurrency**: Runs serially to respect Lichess API limits.
  - **Streaming**: Streams games via NDJSON and dispatches them immediately.
- **Consumer (`celery_consumer`)**:
  - **High Concurrency**: Processes raw game data in parallel and writes to the DB.

### 2. Analysis (Plugins)
- **Scheduler (`analysis_producer`)**:
  - Finds games that need analysis and enqueues them.
- **Worker (`analysis_consumer`)**:
  - Runs CPU-intensive analysis tasks using **Stockfish**.
  - **Plugin System**: Analysis logic is modular. New plugins can be added to `celery/analysis/plugins/` to calculate different metrics without changing the core worker.

```mermaid
graph LR
    Beat[Celery Beat] -->|Trigger| Orch[Orchestrator]
    Orch -->|Dispatch| Prod[Producer]
    Prod -->|Stream| Q1[(Redis: api_queue)]
    Q1 -->|Fetch| Lichess[Lichess API]
    Lichess -->|NDJSON| Prod
    Prod -->|Enqueue| Q2[(Redis: db_queue)]
    Q2 -->|Consume| Cons[Consumer]
    Cons -->|Write| API[FastAPI]
    
    Beat -->|Trigger| AnSched[Analysis Scheduler]
    AnSched -->|Enqueue| Q3[(Redis: analysis_queue)]
    Q3 -->|Consume| AnWork[Analysis Worker]
    AnWork -->|Run Plugins| Stockfish
    AnWork -->|Save Metrics| API
```

## 📦 Services

| Service | Role | Description |
|---------|------|-------------|
| `fastapi` | API / Data Layer | Central REST API and database interface. |
| `celery_producer` | Ingestion | Fetches data from Lichess. **Global Lock ensures serial execution**. |
| `celery_consumer` | Processing | Processes raw data and writes to DB. **Concurrency: 8**. |
| `analysis_producer`| Scheduling | Finds games needing analysis. |
| `analysis_consumer`| Analysis | Runs Stockfish analysis plugins. **Concurrency: 4**. |
| `celery_beat` | Scheduler | Triggers periodic tasks. |
| `redis` | Broker | Message broker for Celery queues. |
| `postgres` | Database | Persistent storage. |

## ⚡ Quick Start

### Prerequisites
- Docker & Docker Compose
- Lichess API Token

### 1. Clone & Configure
```bash
git clone <repository-url>
cd personal-backend
# Create .env file (see .env.example or docs)
```

### 2. Run with Docker
```bash
docker-compose up --build -d
```

### 3. Verify
```bash
docker-compose logs -f celery_producer analysis_consumer
```

## 🧪 Development

### Local Setup (Python)
```bash
# Install dependencies
cd celery
pip install -r requirements.txt

# Run Tests (Dockerized)
make test
```

### CI/CD & Release Management
- **GitHub Actions**: Tests run on every PR.
- **Release Please**: Automates versioning, changelogs, and GitHub Releases.
- **Conventional Commits**: We strictly follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. This is **required** for Release Please to work correctly.
  - `feat:` for new features (triggers minor version bump)
  - `fix:` for bug fixes (triggers patch version bump)
  - `chore:`, `docs:`, `refactor:` for other changes (no version bump unless specified)

## 📂 Project Structure

```
.
├── AGENTS.md           # Detailed Architecture Documentation
├── celery/             # Celery Workers
│   ├── celery_app.py   # App Entry Point & Schedule
│   ├── tasks/          # Task Modules
│   │   ├── fetching.py # Ingestion Tasks
│   │   └── analysis.py # Analysis Tasks
│   └── analysis/       # Analysis Logic
│       └── plugins/    # Pluggable Analysis Metrics
├── fastapi/            # Backend API
└── docker-compose.yml  # Infrastructure Definition
```
