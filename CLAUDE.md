# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Python (Flask app):**
```bash
pip install -r requirements.txt
flask run                          # dev server (uses .flaskenv: FLASK_APP=run.py, FLASK_CONFIG=DevelopmentConfig)
pytest tests/unit/                 # run all unit tests
pytest tests/unit/test_c7query.py  # run a single test file
```

**Node / Playwright (E2E tests):**
```bash
npm ci
npx playwright install --with-deps  # first-time browser install
npx playwright test                 # run all E2E tests (tests/e2e/)
npx playwright test --project=chromium  # run against a single browser
```

**Database migrations (Alembic):**
```bash
alembic upgrade head
alembic revision --autogenerate -m "description"
```

## Architecture

Flask 3 app that generates business contracts (NDA, MSA, Statement of Services) for Change Specialists. Documents are generated from DOCX templates in `samples/`, populated with data from external APIs and local DB, then uploaded to SharePoint and optionally sent to DocuSign.

**Data sources:**
- **Colleague 7 (C7)** — HR/recruitment system; candidates, companies, contacts, contracts (`app/c7query.py`)
- **Companies House** — UK company validation and director verification (`app/chquery.py`)
- **NAME API** — Director name matching; key constructed as `f"{NAMEAPI_KEYPREFIX}-{NAMEAPI_KEYSUFFIX}"`
- **Azure SQL Server** (serverless) — Service standards, arrangements, contracts; single source of truth augmenting C7 (`app/dbquery.py`, `app/models.py`)

**Request flow:** Routes in `app/views.py` → business logic modules (`c7query.py`, `chquery.py`, `dbquery.py`) → DB/API helpers in `app/helper.py` → Azure SQL / external APIs

Flask sessions carry multi-step workflow state: `sid` (service ID), `sessionContract`, `serviceStandards`, `candidateName`.

## Database Access Pattern (Required)

Never call `db.session.*` directly in views or query modules. All DB access must go through helpers in `app/helper.py`:

- **Reads:** `db_query_scalars(stmt)`, `db_query_scalar(stmt)`, `db_query_one_or_none(stmt)`, `db_get_by_pk(Model, key)`
- **Writes:** `db_add(instance)`, `db_delete(instance)`, `db_commit(operation_name=...)`

Always pass `operation_name=` for logging context. These helpers enforce the single connection-check path, retry/backoff for transient failures, and consistent rollback.

## Azure SQL Serverless Wake-Up

The database pauses when idle. `app/__init__.py` detects errors 40613/08001 on startup and spawns a background thread that retries every 10 seconds (up to 30 attempts). Users are redirected to `/waiting` until `db_connected=True`. `/db-status` and `/db-check` endpoints expose connection state as JSON.

## Secrets & Config

Runtime secrets come from environment variables (`.env` in dev, App Service config in prod) with Azure Key Vault as fallback (`app/keyvault.py`). Key Vault secret names use hyphens (e.g., `SQL-USERNAME`) while env vars use underscores (`SQL_USERNAME`). The three Flask configs are in `config.py`: `DevelopmentConfig`, `ProductionConfig`, `TestingConfig`.

## Deployment

Two GitHub Actions workflows:
- **`azure-webapps-python.yml`** — auto-deploys to `cs-deploytest` on push to `main`
- **`deploy-production.yml`** — manually triggered; deploys to `cs-document-generator`

The build pre-packages pip dependencies into `.python_packages/lib/site-packages`; `run.py` prepends this path to `sys.path` at startup so the Azure App Service runtime finds them.
