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

## Production deployment

### Recommended platform split
- `apps/web` -> Vercel
- `services/api` -> Railway service using `services/api/railway.toml`
- `services/worker` -> Railway service using `services/worker/railway.toml`
- Postgres -> Railway Postgres or Neon
- Email -> Resend
- Snapshot storage -> Railway volume with `SNAPSHOT_STORAGE_BACKEND=local` or S3-compatible storage with `SNAPSHOT_STORAGE_BACKEND=s3`

### Domain model
Use sibling subdomains so the shared session cookie can cover both hosts.
- `app.yourdomain.com` -> web
- `api.yourdomain.com` -> API

Set these production env vars on both the web app and API:
- `SESSION_COOKIE_DOMAIN=.yourdomain.com`
- `SESSION_COOKIE_SECURE=true`
- `SESSION_COOKIE_SAME_SITE=lax`
- `SESSION_COOKIE_NAME=boe_session`

Set these on the API:
- `ENVIRONMENT=production`
- `APP_BASE_URL=https://app.yourdomain.com`
- `CORS_ALLOWED_ORIGINS=https://app.yourdomain.com`
- `AUTO_CREATE_SCHEMA=false`
- `AUTO_SEED_ON_STARTUP=false`

Set these on the web app:
- `NEXT_PUBLIC_APP_URL=https://app.yourdomain.com`
- `NEXT_PUBLIC_API_URL=https://api.yourdomain.com`
- `INTERNAL_API_URL=https://api.yourdomain.com`
- `NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION=<google-search-console-token>`
- `NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX`
- `NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION_APP=<optional app-host token>`
- `NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION_APEX=<optional apex-host token>`
- `NEXT_PUBLIC_GA_MEASUREMENT_ID_APP=<optional app-host GA4 stream>`
- `NEXT_PUBLIC_GA_MEASUREMENT_ID_APEX=<optional apex-host GA4 stream>`

### Search Console and analytics
The web app supports Google Search Console ownership and GA4 without further code changes.

Set these on Vercel:
- `NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION=<google-search-console-token>`
- `NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX`
- optionally split them by host with:
  - `NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION_APP=<app token>`
  - `NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION_APEX=<apex token>`
  - `NEXT_PUBLIC_GA_MEASUREMENT_ID_APP=<app GA4 stream>`
  - `NEXT_PUBLIC_GA_MEASUREMENT_ID_APEX=<apex GA4 stream>`

That will:
- emit the Google verification meta tag from the correct host shell
- load the GA4 client script with host-specific stream IDs when provided

Recommended production setup:
- add both `https://tispetta.eu` and `https://app.tispetta.eu` as Google Search Console properties
- keep `tispetta.eu` as a domain property because it owns the redirects and future marketing landing
- keep `app.tispetta.eu` as a URL-prefix property for app-specific indexing checks

### Database bootstrap
The API bootstrap command for Railway predeploy is:
- `cd services/api && python -m app.predeploy`

That command now runs `alembic upgrade head` programmatically before any optional seed step. After the first bootstrap, keep `AUTO_CREATE_SCHEMA=false` in production so runtime startup does not mutate schema.

Local migration command:
- `cd services/api && alembic upgrade head`

### Email delivery
Magic-link delivery supports:
- Resend API when `RESEND_API_KEY` is configured
- SMTP fallback when `SMTP_HOST` and related settings are configured

For Resend SMTP, use:
- `SMTP_HOST=smtp.resend.com`
- `SMTP_PORT=465`
- `SMTP_USERNAME=resend`
- `SMTP_PASSWORD=<resend-api-key>`
- `SMTP_USE_SSL=true`

Minimum live email setup on Railway:
- `ENVIRONMENT=production`
- `RESEND_API_KEY=<resend-api-key>`
- `RESEND_FROM_EMAIL=login@updates.yourdomain.com`

Without those values, the API falls back to preview-link behavior or SMTP fallback depending on the environment.

### Recurring corpus refresh
The Railway worker runs an internal scheduler and no longer relies on one-shot startup dispatch.

Set these on the worker:
- `WORKER_POLL_INTERVAL_SECONDS=5`
- `WORKER_ENDPOINT_REFRESH_INTERVAL_SECONDS=21600`
- `WORKER_FAMILY_REFRESH_INTERVAL_SECONDS=21600`
- `WORKER_SURVEY_REFRESH_INTERVAL_SECONDS=86400`

That gives you:
- source endpoint refresh every 6 hours
- measure-family bootstrap refresh every 6 hours
- survey coverage recomputation every 24 hours

## Main scripts
- `pnpm dev`
- `pnpm infra:up`
- `pnpm seed`
- `pnpm test`
