# Chat AI

A FastAPI-based AI chat application backed by MySQL, using Google's Gemini API to
generate assistant responses. Supports both guest (unauthenticated, non-persistent)
chats and full user accounts with saved conversation history.

## Table of Contents

- [Purpose](#purpose)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Running Locally in a Virtual Environment](#running-locally-in-a-virtual-environment)
- [Running Locally with Docker Compose](#running-locally-with-docker-compose)
- [Database Migrations (Alembic)](#database-migrations-alembic)
- [Environment Variables](#environment-variables)
- [Testing](#testing)
- [Deployment Pipeline](#deployment-pipeline)
- [Deploying to Heroku](#deploying-to-heroku)
- [CI/CD (GitHub Actions)](#cicd-github-actions)

## Purpose

Chat AI is a self-contained chat assistant: a FastAPI backend serves both the REST
API and the static frontend (HTML/CSS/JS), backed by a MySQL database for user
accounts and conversation history, with Gemini providing the actual AI responses.

Core features:
- **User accounts** — signup, login, JWT-based access/refresh token authentication.
- **Guest chat** — anyone can chat without an account; guest messages are not saved.
- **Persistent conversations** — logged-in users get saved, threaded conversation
  history with rename/delete support.
- **AI responses** — powered by Google's Gemini API, with structured JSON responses
  and Markdown-formatted content.

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| Database | MySQL 8.0 |
| DB driver | PyMySQL |
| Auth | JWT (PyJWT), Argon2/Passlib password hashing |
| AI provider | Google Gemini (`google-genai`) |
| WSGI/ASGI server | Gunicorn + Uvicorn workers |
| Hosting | Heroku (Eco/Basic dynos) |
| Local dev | Docker Compose |
| CI/CD | GitHub Actions |

## Project Structure

```
Chat-AI/
├── main.py                      # FastAPI app entrypoint, route registration, CORS, exception handlers
├── backend/
│   ├── core/
│   │   └── config.py             # Pydantic settings, reads env vars / .env
│   ├── db/
│   │   └── database.py           # SQLAlchemy engine, session, DB URL normalization
│   ├── models/
│   │   └── model.py               # SQLAlchemy ORM models (User, Conversation, Message)
│   ├── routes/
│   │   ├── auth.py                # Login, token refresh, token validation
│   │   ├── user.py                # Signup, profile, password change
│   │   └── chat.py                # Send message, list/get/delete/rename conversations
│   ├── schemas/
│   │   ├── base.py                # Shared API response schemas
│   │   ├── auth.py                # Auth request/response Pydantic models
│   │   └── chat.py                # Chat request/response Pydantic models
│   └── utils/
│       ├── auth.py                # Password hashing, JWT encode/decode, current-user dependency
│       └── gemini.py               # Gemini client initialization
├── frontend/
│   ├── static/
│   │   ├── CSS/                   # Stylesheets
│   │   ├── JS/                    # Frontend JavaScript (constants.js, api-call.js, etc.)
│   │   └── Images/                # Icons and static images
│   └── templates/                 # Jinja2 HTML templates
├── alembic/
│   ├── env.py                     # Alembic environment config (uses same DB URL as the app)
│   └── versions/                  # Migration files — tracked in git, required in every environment
├── alembic.ini
├── tests/
│   ├── conftest.py                # Pytest fixtures: in-memory SQLite DB, TestClient
│   ├── test_health.py
│   ├── test_auth.py
│   └── test_chat.py
├── .github/
│   └── workflows/
│       └── deploy.yml             # CI/CD: test on PRs, deploy develop→staging, main→production
├── docker-compose.yml             # Local dev: FastAPI + MySQL containers
├── Dockerfile
├── .dockerignore
├── Procfile                       # Heroku process types (release + web)
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Adds pytest/httpx for testing (not installed on Heroku)
├── runtime.txt                    # Pinned Python version for Heroku's buildpack
├── .env.example                   # Template for local environment variables
└── .gitignore
```

## Running Locally in a Virtual Environment

**Prerequisites:** Python 3.14.x, a local MySQL 8.0 server running.

```bash
# 1. Clone and enter the project
git clone https://github.com/patrickamowe/Chat-AI.git
cd Chat-AI

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # on Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# 4. Configure environment variables
cp .env.example .env
# edit .env: set DATABASE_URL, JWT_ACCESS_SECRET, JWT_REFRESH_SECRET, GEMINI_API_KEY

# 5. Create the database (if it doesn't exist yet)
mysql -u root -p -e "CREATE DATABASE chat_ai_db;"

# 6. Apply migrations
alembic upgrade head

# 7. Run the app
uvicorn main:app --reload
```

The app will be available at `http://127.0.0.1:8000`.

## Running Locally with Docker Compose

**Prerequisites:** Docker and Docker Compose installed. No local MySQL install needed —
Compose runs a MySQL container for you.

```bash
docker-compose up --build
```

This starts two services:
- `db` — MySQL 8.0, with a persisted volume so data survives restarts.
- `web` — the FastAPI app, hot-reloading via `--reload`, connected to `db` over the
  Compose network (not `localhost`).

The app will be available at `http://127.0.0.1:8000`. Environment variables not
overridden in `docker-compose.yml` are still loaded from your local `.env` file via
`env_file`.

Run migrations inside the running container if needed:

```bash
docker-compose exec web alembic upgrade head
```

Stop and remove containers:

```bash
docker-compose down
```

Add `-v` to also remove the MySQL data volume (full reset):

```bash
docker-compose down -v
```

## Database Migrations (Alembic)

Migration files in `alembic/versions/` are **not local-only artifacts** — they are the
source of truth for the database schema in every environment (local, staging,
production) and are committed to git.

Common commands:

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration after changing a model in backend/models/model.py
alembic revision --autogenerate -m "describe the change"

# Check current migration state
alembic current

# View full migration history
alembic history --verbose

# Roll back one migration
alembic downgrade -1
```

On Heroku, migrations run automatically via the `release` process in the `Procfile`
before each new deploy's web dyno starts serving traffic (see
[Deploying to Heroku](#deploying-to-heroku)).

## Environment Variables

See `.env.example` for the full list. Key variables:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy connection string. Accepts `mysql://` (auto-normalized to `mysql+pymysql://`) or `mysql+pymysql://` directly. |
| `ENVIRONMENT` | `development`, `staging`, or `production` — gates a startup check that refuses to boot in production with placeholder secrets. |
| `JWT_ACCESS_SECRET` / `JWT_REFRESH_SECRET` | Signing secrets for access/refresh tokens. Generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Use distinct values per environment. |
| `JWT_ALGORITHM` | JWT signing algorithm (`HS256`). |
| `GEMINI_API_KEY` | API key for Google's Gemini API. |

## Testing

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest -v
```

Tests use an in-memory SQLite database (via a fixture in `tests/conftest.py`) and mock
the Gemini API call, so they don't require a real MySQL instance or a real Gemini key
to run.

## Deployment Pipeline

```
Local (.venv or Docker Compose)
        │
        ▼
   feature branch → PR → develop        (CI runs tests on every PR)
        │
        ▼
   push to develop → GitHub Actions → Heroku Staging (chat-ai-stag)
        │
        ▼
   develop → PR → main
        │
        ▼
   push to main → GitHub Actions → Heroku Production (chat-ai-prod)
```

- **Staging** and **Production** are separate Heroku apps, each with their own JawsDB
  MySQL add-on and their own distinct JWT secrets.
- Both run on Eco dynos (`heroku ps:type web=eco`), the lowest-cost paid tier.
- Everything database- and app-config-related (`database.py`, `Procfile`, `requirements.txt`)
  is written to be platform-agnostic, so the same setup can be adapted to Render or
  another host with minimal changes — only the deploy step in `deploy.yml` is
  Heroku-specific.

## Deploying to Heroku

### One-time setup per app (staging and production)

```bash
# Create the app (if not already created via Heroku Pipelines dashboard)
heroku apps:create chat-ai-stag
heroku apps:create chat-ai-prod

# Add a MySQL add-on
heroku addons:create jawsdb:kitefin -a chat-ai-stag
heroku addons:create jawsdb:kitefin -a chat-ai-prod

# Point DATABASE_URL at the add-on's connection string
heroku config:set DATABASE_URL="$(heroku config:get JAWSDB_URL -a chat-ai-stag)" -a chat-ai-stag
heroku config:set DATABASE_URL="$(heroku config:get JAWSDB_URL -a chat-ai-prod)" -a chat-ai-prod

# Set required secrets (generate distinct values per app)
heroku config:set \
  ENVIRONMENT=staging \
  JWT_ALGORITHM=HS256 \
  JWT_ACCESS_SECRET="<generated>" \
  JWT_REFRESH_SECRET="<generated>" \
  GEMINI_API_KEY="<your key>" \
  -a chat-ai-stag

# (repeat for chat-ai-prod with ENVIRONMENT=production and different secrets)

# Use the cheapest dyno tier
heroku ps:type web=eco -a chat-ai-stag
heroku ps:type web=eco -a chat-ai-prod
```

### Manual deploy

```bash
heroku git:remote -a chat-ai-stag -r heroku-staging
git push heroku-staging develop:main

heroku git:remote -a chat-ai-prod -r heroku-prod
git push heroku-prod main:main
```

Heroku's release phase (defined in `Procfile`) runs `alembic upgrade head`
automatically before the new `web` dyno starts. If migrations fail, the deploy is
aborted and the previous release keeps serving traffic.

### Verifying a deploy

```bash
heroku logs --tail --app chat-ai-stag
heroku run "python -c \"from backend.db.database import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())\"" --app chat-ai-stag
```

## CI/CD (GitHub Actions)

Defined in `.github/workflows/deploy.yml`. Three jobs:

1. **`test`** — runs on every pull request and push to `main`/`develop`. Spins up a
   MySQL service container, applies Alembic migrations, and runs the full pytest
   suite.
2. **`deploy-staging`** — runs only on a push to `develop`, after `test` passes.
   Installs the Heroku CLI and pushes the checked-out commit to `chat-ai-stag`.
3. **`deploy-production`** — runs only on a push to `main`, after `test` passes.
   Same process, targeting `chat-ai-prod`.

### Required GitHub repository secrets

| Secret | Value |
|---|---|
| `HEROKU_API_KEY` | From `heroku authorizations:create` |
| `HEROKU_EMAIL` | Your Heroku account email |
| `HEROKU_STAGING_APP_NAME` | `chat-ai-stag` |
| `HEROKU_PRODUCTION_APP_NAME` | `chat-ai-prod` |

Configure these under **GitHub repo → Settings → Secrets and variables → Actions**.