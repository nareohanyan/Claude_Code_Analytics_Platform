# Claude Code Analytics Platform

End-to-end analytics platform for Claude Code telemetry.
It ingests raw JSON/CSV telemetry, stores it in PostgreSQL, builds analytical aggregates, exposes them through a FastAPI service, and visualizes insights in a Streamlit dashboard.

## Assignment Scope

This repository implements:

- Data ingestion and normalization (ETL)
- SQL analytics layer over session/event behavior
- Interactive dashboard for stakeholders
- API access bonus (`/api/v1/...`)
- Predictive analytics bonus (forecasting + anomaly detection)

## Architecture Overview

Data flow:

1. Raw input files (`telemetry_logs.jsonl`, `employees.csv`)
2. ETL parser normalizes fields into relational schema
3. PostgreSQL stores `employees`, `events`, `sessions`
4. Analytics service computes KPIs, trends, adoption, reliability, model/tool metrics
5. FastAPI exposes analytics endpoints
6. Streamlit dashboard consumes API responses

Core layers:

- `src/claude_analytics/etl` - parsing and loading pipeline
- `src/claude_analytics/db` - SQLAlchemy models/session
- `alembic/` - schema migrations
- `src/claude_analytics/analytics` - analytics query/service layer
- `src/claude_analytics/api` - FastAPI routes for programmatic access
- `app/dashboard.py` - interactive UI

## Tech Stack

- Python 3.12
- PostgreSQL 16 (Docker)
- SQLAlchemy + Alembic
- FastAPI + Uvicorn
- Streamlit + Plotly + Pandas + NumPy

## Repository Structure

```text
.
|-- alembic/                         # DB migrations
|-- app/
|   `-- dashboard.py                 # Streamlit UI
|-- scripts/
|   |-- load_data.py                 # ETL CLI
|   `-- preview_analytics.py         # Analytics smoke preview
|-- src/claude_analytics/
|   |-- analytics/                   # Query/service + schemas
|   |-- api/                         # FastAPI app + routes
|   |-- dashboard/                   # API data adapter for UI
|   |-- db/                          # ORM models/session/base
|   |-- etl/                         # Parser + loader
|   |-- config.py                    # Environment-based config
|   `-- schema.py                    # SQL helpers
|-- docker-compose.yml               # Postgres + Adminer
|-- Makefile                         # Developer workflow commands
`-- requirements.txt
```

## Prerequisites

- Python 3.12+
- Docker Desktop (Windows) or Docker Engine (Linux/macOS)
- `make` available in shell

## Setup

1. Create and activate virtual environment.

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Git Bash
source .venv/Scripts/activate
```

2. Install dependencies.

```bash
make install
```

3. Configure environment.

```bash
# Linux/macOS/Git Bash
cp .env.example .env
# PowerShell
Copy-Item .env.example .env
```

4. Place dataset files under:

```text
claude_code_telemetry (1)/output/employees.csv
claude_code_telemetry (1)/output/telemetry_logs.jsonl
```

## Run The Platform

1. Start infrastructure.

```bash
make up
```

2. Apply migrations.

```bash
make migrate
```

3. Load dataset into PostgreSQL.

```bash
make load
```

4. Start API.

```bash
make api
```

5. Start dashboard (in another terminal).

```bash
make dashboard
```

## Access Points

- Dashboard: `http://127.0.0.1:8501`
- API docs (Swagger): `http://127.0.0.1:8000/docs`
- OpenAPI spec: `http://127.0.0.1:8000/openapi.json`
- Adminer: `http://localhost:8080`

Adminer default connection:

- Server: `postgres`
- Username: `claude`
- Password: `pass`
- Database: `claude_code_analytics`

## API Endpoints

Base path: `/api/v1`

- `GET /overview`
- `GET /adoption?dimension=practice|level|location|terminal|os`
- `GET /trend/daily`
- `GET /models`
- `GET /tools`
- `GET /errors?limit=10`
- `GET /usage/peak-hours`
- `GET /sessions/top?limit=10`
- `GET /dashboard`
- `GET /predictive/forecast?metric=total_cost_usd&horizon_days=7&backtest_days=7`

Predictive metrics:

- `total_cost_usd`
- `api_requests`
- `total_tokens`
- `api_errors`

## Predictive Analytics (Bonus)

Implemented approach:

- Daily time series extraction from telemetry
- Forecast model: linear trend + weekday seasonality
- Holdout backtest with `MAE` and `MAPE`
- Residual-based anomaly detection (`|z-score| >= 2`)

Outputs are available via API and rendered in a dedicated dashboard section:

- forecast curve (history/backtest/forward window)
- backtest quality metrics
- anomaly candidates table

## Makefile Commands

- `make install` - install dependencies and editable package
- `make up` / `make down` / `make restart` / `make ps` / `make logs`
- `make migrate` - apply Alembic migrations
- `make load` - run ETL load
- `make reload` - migrate + load
- `make reset-db` - recreate DB volume + migrate + load
- `make analytics-preview` - print analytics sample payload
- `make api` - run FastAPI
- `make dashboard` - run Streamlit UI
- `make verify` - compile-time sanity check

## Verification

Recommended local sanity checks:

```bash
make verify
make analytics-preview
curl.exe http://127.0.0.1:8000/health
curl.exe "http://127.0.0.1:8000/api/v1/overview"
```

## LLM Usage Log

A dedicated `LLM_USAGE_LOG.md` should be included for submission, with:

- AI tools used
- representative prompts
- validation steps for AI-generated output

If preferred, this can also be embedded as a section in this README.
