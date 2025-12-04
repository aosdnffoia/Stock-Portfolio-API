# Portfolio API

FastAPI backend for authentication, market-data ETL, and deterministic portfolio retrieval backed by Postgres.

## One-command run

Prereq: Docker + Docker Compose.

```bash
docker compose up --build
```

What happens: Postgres starts, Alembic migrations run, demo user seeds, API serves on http://localhost:8000.

## Environment

Configure in one place: `.env` (see `.env.example`). Key vars:
- `DATABASE_URL` (asyncpg URL, default points to docker db)
- JWT: `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- ETL: `TICKER_SYMBOLS` (comma list), `ETL_ON_STARTUP` (true/false), `ETL_SCHEDULE_ENABLED`, `ETL_SCHEDULE_HOUR`
- Demo user: `DEMO_USER_EMAIL`, `DEMO_USER_PASSWORD`

## ETL
- Source: yfinance (no key required by default).
- Runs once on startup (default `ETL_ON_STARTUP=true`); scheduling hook is present—set `ETL_SCHEDULE_ENABLED=true` and `ETL_SCHEDULE_HOUR`.
- Tables: `tickers`, `prices`; latest prices drive portfolios.

## Auth
- Demo login: email/password from `.env.example` (default `demo@example.com` / `demo123`).
- Endpoints:
  - `POST /auth/login` `{ "email": "...", "password": "..." }`
  - `POST /auth/social?provider=google|facebook` (mock, returns token)
  - `GET /auth/me` (Bearer token required)

## Portfolio
- `GET /portfolio` (Bearer token) returns holdings with latest prices, total value. Portfolios are deterministic per user and differ across users.

## Health & logging
- `GET /healthz` verifies DB connectivity.
- Logs are JSON-formatted with request IDs; `X-Request-ID` is echoed if provided.

## Curl examples
```bash
# health
curl http://localhost:8000/healthz

# login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"demo123"}' | jq -r .access_token)

# portfolio
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/portfolio
```

## Project Structure
```
app/
  auth/          # authentication routes/utils/schemas
  etl/           # market data models + ETL service
  portfolio/     # portfolio models, service, routes
  core/          # logging, security
  main.py        # FastAPI app + middleware
alembic/versions # migrations
scripts/         # docker entrypoint, seed script
tests/           # pytest suite
```

## Testing
Local (with coverage):
```bash
mkdir -p .tmp
export TMPDIR=$PWD/.tmp TMP=$PWD/.tmp TEMP=$PWD/.tmp
unset PYTEST_DISABLE_PLUGIN_AUTOLOAD
.venv/bin/pytest --basetemp $PWD/.tmp --capture=no
```
Coverage target: ≥70% (see htmlcov/ or console output).

## Troubleshooting
- If pytest complains about temp dirs, ensure `TMPDIR/TMP/TEMP` point to a writable path (see above).
- Ensure migrations run (entrypoint handles this for Docker); otherwise run `alembic upgrade head` manually. 
