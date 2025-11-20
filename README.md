# FishClaim Backend

FastAPI backend for FishClaim. Provides auth, waters/zones, catches, and claim routes backed by PostgreSQL/PostGIS. Dockerized for local dev and deployed via docker-compose.

## Tech stack
- FastAPI + Uvicorn
- SQLAlchemy
- PostgreSQL/PostGIS
- Docker + docker-compose

## Getting started (local Python)
1. `python -m venv .venv`
2. `source .venv/bin/activate` (Windows: `./.venv/Scripts/activate`)
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and set values (e.g. `DATABASE_URL=postgresql+psycopg2://user:password@fishclaim_db:5432/fishclaim`, `SECRET_KEY=...`).
5. Run the API: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

## Running with Docker
From the backend repo root (`/home/conor/fishclaim/backend`):
1. `cp .env.example .env` and update values (use `fishclaim_db` as the host if you are attaching to the existing Postgres/PostGIS container).
2. Ensure the Docker network `fishclaim_default` exists (created by the current stack). If missing, create it: `docker network create fishclaim_default`.
3. Build and start the backend: `docker compose up -d --build backend`
4. API will be on port `8080` by default (override with `BACKEND_PORT` in `.env`).

Docker build uses `Dockerfile` with `requirements.txt` and the `app/` directory.

## Deploy script (server)
- `./deploy.sh [branch]` (default branch is `main`) will `git pull`, build the backend image, and restart the backend container without touching the database container.

## Branching model
- `main`: stable / production
- `dev`: integration
- `feature/*`: feature branches

## Migrations
- SQL migrations live in `app/migrations/`. Apply them manually to your database (e.g. `psql -f app/migrations/001_add_role_refresh_tokens_and_claim_status.sql`).
- If you add new schema changes, create a new numbered file in that folder and document how to apply it.

## Working on backend + frontend together
- Start from `dev` in both repos; create the same feature branch name (e.g. `feature/auth-session-hardening`).
- Develop locally: run the FastAPI server; in the UI repo set `VITE_API_BASE_URL` to your local API (e.g. `http://localhost:8080/api`).
- Keep commits small and focused. Separate backend and frontend commits are fine as long as the branch names match.
- Run checks before push (`pytest` here; `npm run lint`/`npm test` in the UI if available).
- Push both branches to origin when the end-to-end slice works; open PRs targeting `dev`.
- Promote `dev` → `main` via PRs only; avoid direct pushes to `main`.

## Notes
- Secrets should never be committed. Keep real values in `.env` (gitignored) using `.env.example` as a template.
- If you add new config keys, update `.env.example` and this README.
