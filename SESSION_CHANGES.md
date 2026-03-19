# Tispetta – Session Changes Log

> Covers all work performed across the multi-session pairing.
> Branch: `feature/session-improvements`
> Date: 2026-03-16

---

## Overview

Four areas of work were completed: **catalog data enrichment**, **frontend UX improvements**, **notification pipeline** (worker + admin + email), and **profile-form correctness**. All changes are code-only – no infrastructure credentials, migrations, or new environment variables were required.

---

## 1. Catalog Seeds (`services/api/app/seeds/catalog.py`)

### Additions

**60 total seeds** (previously 56), covering `persona_fisica`, `sme`, `startup`, and `freelancer` profiles.

New seeds added:

| Title | Ente | Target | Category |
|---|---|---|---|
| Fringe Benefits Dipendenti con Figli 2024 | INPS | persona_fisica | benefit |
| Detrazione Spese Istruzione Universitaria | AdE | persona_fisica | benefit |
| Patent Box — Agevolazione Fiscale su Redditi da IP | AdE | sme + startup | tax |
| Sabatini Green — Beni Strumentali Ecologici | MIMIT | sme + startup | sustainability |

### Breakdown by profile type after all sessions

| Profile type | Seeds |
|---|---|
| persona_fisica | 22 |
| sme | 32 |
| startup | 32 |
| freelancer | 10 |

### Rule quality: `extra_required`

Seeds that were purely profile-type gated (no real-world conditions) received `extra_required` fields to make rules more specific and reduce false positives. Examples:
- `Fringe Benefits`: requires `employment_type=dipendente` + `figli_a_carico_count NOT 0`
- `Detrazione Istruzione`: requires `figli_a_carico_count NOT 0`
- `Patent Box`: tagged as `innovation` booster
- `Sabatini Green`: tagged as `sustainability` booster

---

## 2. Profile Form (`apps/web/components/profile-form.tsx`)

### Bug 1 – `userType` never resolved to `'startup'`

`userType` was computed with `??` (nullish coalesce) which does not coalesce empty strings. Changed to `||` so that an empty-string profile type correctly falls back to `'startup'`.

```tsx
// before
const userType = profile?.profile_type ?? 'startup';

// after
const userType = profile?.profile_type || 'startup';
```

### Bug 2 – "Attivita o impresa" button never set `profile_type`

The "Attivita o impresa" gate button in the onboarding flow called `setActiveGate('business')` but never called `setValue('profile_type', 'startup')`. This meant the audience filter for startup/SME questions would not activate after clicking. Fixed by adding the missing `setValue` call.

---

## 3. Dashboard (`apps/web/app/page.tsx`)

### Profile completeness nudge

When a user's `profile_completeness_score` is below 70, a banner nudge is rendered below the hero section:

```
Profilo al {score}% — completa le domande mancanti per sbloccare piu match.
[Completa profilo →]
```

Links to `/onboarding`.

### "Vedi tutte" links on section headers

All three match sections now have a "Vedi tutte" label that navigates to the search page with a pre-applied filter:

| Section | Link |
|---|---|
| Confermate | `/search?matched_status=confirmed` |
| Probabili | `/search?matched_status=likely` |
| Scadenze | `/search?sort=deadline` |

---

## 4. Search Page (`apps/web/app/search/page.tsx`)

### `matched_status` URL param

The search page now reads `matched_status` from URL params and passes it as a filter to `getOpportunities`. This makes the "Vedi tutte" links on the dashboard functional.

### `sort=deadline` URL param

When `sort=deadline` is present, results are filtered to those with a `deadline_date` and sorted ascending by date (nearest deadline first). Applied client-side after the API fetch.

### Active filter label

The results eyebrow label reflects the active filter state so users know they are in a filtered view.

---

## 5. Opportunity Detail (`apps/web/app/opportunities/[slug]/page.tsx`)

### Actionable missing-data panel

Replaced the flat `what_is_missing` text banner with a structured panel that:
- Shows an orange left-border
- Labels the section with an eyebrow "Dati mancanti"
- Lists each missing field as a bullet
- Includes a CTA button "Completa il profilo" → `/onboarding`

Before: a generic yellow text block.
After: scoped panel with clear action path.

---

## 6. Saved Page (`apps/web/app/saved/page.tsx`)

Complete rewrite from a flat list to a status-grouped view:

- Groups: `confirmed` → `likely` → `unclear` → `not_eligible` → `unmatched`
- Within each group, items are sorted by `deadline_date` ascending (nulls last)
- Section headers include a count badge
- Empty state when no saved items, with CTA to search
- Removes items with `match_status = 'unmatched'` from the primary view (shown in a collapsed section)

---

## 7. Notification Service (`services/api/app/services/notifications.py`)

New shared service module that contains the core notification logic. Created to avoid a circular import: the API routes cannot import from the worker package, and the worker should not import from the API routes. Both depend on this shared service.

### `run_deadline_reminders(db: Session) -> int`

- Queries users with `email_enabled=True` and `deadline_reminders=True`
- Fetches their `confirmed` or `likely` matches with `deadline_date` within the next 30 days
- Groups multiple expiring opportunities into a single email per user
- Returns the count of emails dispatched

### `run_weekly_digest(db: Session) -> int`

- Queries users with `email_enabled=True` and `weekly_profile_nudges=True`
- Fetches top-5 matches per user by `match_score DESC`
- Skips users with no qualifying matches
- Appends a profile-completeness nudge when `profile_completeness_score < 60`
- Returns the count of emails dispatched

---

## 8. Worker (`services/worker/`)

### `worker/jobs/pipeline.py`

**`enqueue_notifications` fix – respects `email_enabled`**

The function previously dispatched notifications regardless of user preference. Now it checks `NotificationPreference.email_enabled` for the event's `user_id` before creating a `Notification` row. It also sets `notification.sent_at = datetime.now(UTC)` on successful delivery (previously left null).

**`send_deadline_reminders` and `send_weekly_digest` actors**

Two Dramatiq actors added that delegate to the shared notification service:

```python
@dramatiq.actor
def send_deadline_reminders(_: str = 'run') -> None:
    with SessionLocal() as db:
        dispatched = run_deadline_reminders(db)
        logger.info('Deadline reminder job complete: %d emails sent', dispatched)

@dramatiq.actor
def send_weekly_digest(_: str = 'run') -> None:
    with SessionLocal() as db:
        dispatched = run_weekly_digest(db)
        logger.info('Weekly digest job complete: %d emails sent', dispatched)
```

### `worker/config.py`

Two new scheduling intervals:

```python
worker_deadline_reminder_interval_seconds: int = 60 * 60 * 24      # daily
worker_weekly_digest_interval_seconds: int = 60 * 60 * 24 * 7     # weekly
```

### `worker/main.py`

Both notification jobs are scheduled in the main worker loop using the existing `_is_due()` helper. The `last_run` variables are initialized to `None` so the first execution fires immediately on startup:

```python
deadline_reminder_last_run: datetime | None = None
digest_last_run: datetime | None = None

# in loop:
if _is_due(deadline_reminder_last_run, now, settings.worker_deadline_reminder_interval_seconds):
    send_deadline_reminders.fn()
    deadline_reminder_last_run = now

if _is_due(digest_last_run, now, settings.worker_weekly_digest_interval_seconds):
    send_weekly_digest.fn()
    digest_last_run = now
```

---

## 9. Admin API (`services/api/app/api/routes/admin.py`)

Two admin-only endpoints added for manual triggering and testing of notification jobs:

```
POST /v1/admin/notifications/run-reminders
POST /v1/admin/notifications/run-digest
```

Both require `admin` role (via `get_admin_user` dependency), accept no request body, and return `ApiMessage` with a dispatched-count string. Both delegate to the shared notification service.

---

## 10. Email HTML Templates (`services/api/app/services/auth.py`)

### Magic link email

Added `_magic_link_html(url: str) -> str` — generates a minimal inline-styled HTML email:

- Heading "Accedi a Tispetta"
- Subtitle paragraph
- Black CTA button "Accedi ora" linking directly to the magic URL
- Expiry note (30 minutes)
- Plain copy-paste URL at the bottom as fallback

Both delivery paths updated:
- **Resend**: `html` field added alongside `text` in the JSON payload
- **SMTP**: `message.add_alternative(html, subtype='html')` added after `set_content` plain text

Plain-text fallback is preserved for email clients that do not render HTML.

---

## 11. Admin Notification UI

### `apps/web/components/notification-runner.tsx` (new)

Client component following the `BootstrapRunner` pattern. Two independent action buttons:

| Button | Endpoint |
|---|---|
| Invia promemoria scadenze | `POST /api/proxy/v1/admin/notifications/run-reminders` |
| Invia digest settimanale | `POST /api/proxy/v1/admin/notifications/run-digest` |

Each button has its own `useTransition` state and displays the API response message (or an error string) below.

### `apps/web/app/admin/notifications/page.tsx` (new)

Admin-gated page at `/admin/notifications`. Requires `admin` role; redirects to `/` otherwise. Renders `AdminConsoleNav` and `NotificationRunner`.

### `apps/web/components/admin-console-nav.tsx`

Added "Notifiche" entry to the LINKS array:

```tsx
{ href: '/admin/notifications', label: 'Notifiche' }
```

---

## 12. `apps/web/app/start/page.tsx`

Minor copy/flow adjustments to the marketing entry page as part of the guided entry flow landed in a prior session.

---

## 13. `apps/web/vercel.json`

Redirect and rewrite rules updated. Apex domain redirects to `www` and the `/auth/callback` path is correctly proxied to the API service.

---

## File Index

### New files

| File | Purpose |
|---|---|
| `services/api/app/services/notifications.py` | Shared notification service (deadline reminders + weekly digest) |
| `apps/web/components/notification-runner.tsx` | Admin UI component for triggering notification jobs |
| `apps/web/app/admin/notifications/page.tsx` | Admin page at `/admin/notifications` |

### Modified files

| File | Summary of change |
|---|---|
| `services/api/app/seeds/catalog.py` | +4 seeds, 60 total; `extra_required` conditions on targeted seeds |
| `services/api/app/api/routes/admin.py` | Added `run-reminders` and `run-digest` admin endpoints |
| `services/api/app/bootstrap_manifest.py` | Aligned to catalog seed changes |
| `services/api/app/services/auth.py` | HTML magic link email; `_magic_link_html` helper |
| `services/worker/worker/jobs/pipeline.py` | Fixed `enqueue_notifications`; added `send_deadline_reminders` + `send_weekly_digest` actors; cleaned unused imports |
| `services/worker/worker/config.py` | Added two notification interval settings |
| `services/worker/worker/main.py` | Scheduled both notification jobs in the main loop |
| `apps/web/app/page.tsx` | Completeness nudge; "Vedi tutte" links on all sections |
| `apps/web/app/search/page.tsx` | `matched_status` and `sort=deadline` URL params |
| `apps/web/app/opportunities/[slug]/page.tsx` | Actionable missing-data panel with CTA |
| `apps/web/app/saved/page.tsx` | Full rewrite: status groups, deadline sort, count badges |
| `apps/web/app/start/page.tsx` | Guided entry flow copy |
| `apps/web/components/profile-form.tsx` | Fixed `userType` fallback; added missing `setValue('profile_type')` on business gate |
| `apps/web/components/admin-console-nav.tsx` | Added "Notifiche" nav link |
| `apps/web/vercel.json` | Redirect/rewrite rules |

---

## Architecture Notes

### Notification service extraction

The notification query logic was deliberately placed in `app/services/notifications.py` (the API package) rather than inline in `worker/jobs/pipeline.py`. This prevents a circular dependency: the API admin endpoints (`admin.py`) need to call the same logic, and the API cannot import from the worker package. Both sides import from the shared service.

### Worker scheduling model

Notification jobs use in-memory `last_run: datetime | None` variables and the `_is_due(last_run, now, interval)` helper already established in `worker/main.py`. Setting `last_run = None` on startup means both jobs fire on the first loop iteration, which is the desired behavior for a fresh deploy. The worker process is assumed to be long-lived and single-instance for scheduling purposes.

### Email delivery

All transactional email paths follow the same fallback chain: Resend (if `RESEND_API_KEY` is set) → SMTP → silent failure in non-production environments. HTML and plain-text are always sent as a multipart pair so the message renders correctly in all clients.
