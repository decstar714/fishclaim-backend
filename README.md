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
4. Copy `.env.example` to `.env` and set values (e.g. `DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/fishclaim`, `SECRET_KEY=...`).
5. Run the API: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

## Running with Docker
From the project root that contains `docker-compose.yml` (currently `/home/conor/fishclaim`):
1. Ensure `.env` is set (copy `.env.example` in `backend/` if needed).
2. Build and start: `docker-compose up -d --build`
3. API will be on port 8080 per compose file.

Docker build uses `backend/Dockerfile` with `requirements.txt` and the `app/` directory.

## Branching model
- `main`: stable / production
- `dev`: integration
- `feature/*`: feature branches

## Notes
- Secrets should never be committed. Keep real values in `.env` (gitignored) using `.env.example` as a template.
- If you add new config keys, update `.env.example` and this README.
