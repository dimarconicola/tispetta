# Benefits Opportunity Engine

Monorepo for the Italy-first Benefits Opportunity Engine MVP.

## Workspace
- `apps/web`: Next.js web app for users and operators
- `services/api`: FastAPI application and domain logic
- `services/worker`: background worker and ingestion orchestration

## Local development
1. Copy `.env.example` to `.env` and adjust values if needed.
2. Start local infra: `pnpm infra:up`
3. Install frontend deps: `pnpm install`
4. Install Python deps:
   - `pip install -e services/api`
   - `pip install -e services/worker`
5. Seed the database: `pnpm seed`
6. Start all services: `pnpm dev`

### SQLite fallback
If Docker is not available, set `DATABASE_URL=sqlite:///./benefits_engine.db` in `.env` and run the API/seed commands against SQLite. The codebase keeps the Postgres/Redis/MinIO Compose stack ready, but the current repo is also verified against the SQLite fallback path.

## Main scripts
- `pnpm dev`
- `pnpm infra:up`
- `pnpm seed`
- `pnpm test`
