# UX Flow Inventory

This file is the canonical source of truth for user-facing release gates.

## Gate Levels

- `pre-merge`: must pass before merging to `main`
- `release`: must pass before every major release
- `nightly`: runs on a schedule to detect drift and freshness issues

## Flows

### AUTH-01
- Area: Auth
- Goal: A new user can request a magic link from `/start` and enter the product successfully.
- Preconditions: local/test environment exposes `preview_url`
- Assertions:
  - request succeeds
  - preview link is visible in test/dev
  - callback creates a valid session
  - user lands in onboarding or intended redirect
- Automation:
  - Playwright critical flow
- Gates:
  - `pre-merge`, `release`

### AUTH-02
- Area: Auth
- Goal: An existing user can log in from `/auth/sign-in`.
- Preconditions: seeded or pre-created user
- Assertions:
  - direct sign-in flow works
  - protected routes become accessible
  - redirect target is preserved if provided
- Automation:
  - Playwright
- Gates:
  - `release`

### AUTH-03
- Area: Auth
- Goal: Logout clears the session and protected routes stop working.
- Preconditions: authenticated user
- Assertions:
  - sign-out endpoint clears cookie
  - user is redirected to sign-in
  - protected routes redirect after logout
- Automation:
  - Playwright critical flow
- Gates:
  - `pre-merge`, `release`

### PROF-01
- Area: Profile
- Goal: Persona fisica onboarding works from gate to first results.
- Preconditions: fresh user session
- Assertions:
  - gate is shown
  - core questions remain bounded
  - save succeeds
  - results appear immediately after core completion
- Automation:
  - Playwright critical flow
- Gates:
  - `pre-merge`, `release`

### PROF-02
- Area: Profile
- Goal: Attivita/impresa onboarding works from gate to first results.
- Preconditions: fresh user session
- Assertions:
  - gate is shown
  - impresa core path is selectable
  - core fields can be completed
  - results appear immediately after save
- Automation:
  - Playwright critical flow
- Gates:
  - `pre-merge`, `release`

### PROF-03
- Area: Profile
- Goal: Editing a profile preserves values and keeps the user in context.
- Preconditions: authenticated user with existing values
- Assertions:
  - saved values reload
  - edits persist
  - user is not kicked to an unrelated route
- Automation:
  - API contract + future Playwright extension
- Gates:
  - `release`

### PROF-04
- Area: Profile
- Goal: Sensitive and conditional questions appear only when justified.
- Preconditions: question orchestration payload
- Assertions:
  - sensitive questions are gated
  - why-needed copy exists
  - required core questions stay at or below 8
- Automation:
  - pytest contract tests
- Gates:
  - `pre-merge`, `release`

### MATCH-01
- Area: Matching
- Goal: Ranked opportunities expose deterministic explanations and ordering signals.
- Preconditions: seeded catalog and fixture profiles
- Assertions:
  - status ordering is deterministic
  - blocking/refinement gaps are explicit
  - card/detail explanation fields are populated
- Automation:
  - pytest contract tests
- Gates:
  - `pre-merge`, `release`

### MATCH-02
- Area: Matching
- Goal: Answering one additional question can upgrade or clarify real matches.
- Preconditions: seeded catalog and fixture profiles
- Assertions:
  - at least one opportunity changes status or loses a blocking gap when expected
  - next-best questions remain coherent with the new profile state
- Automation:
  - pytest contract tests + Playwright core path
- Gates:
  - `pre-merge`, `release`

### EXP-01
- Area: Free exploration
- Goal: Anonymous users can explore the catalog through search, filtering, and sorting.
- Preconditions: seeded catalog
- Assertions:
  - search works
  - category filters work
  - detail routes are reachable without auth
- Automation:
  - Playwright critical flow
- Gates:
  - `pre-merge`, `release`

### EXP-02
- Area: Free exploration
- Goal: Authenticated users can save and review opportunities.
- Preconditions: authenticated user
- Assertions:
  - save toggles state
  - saved page shows the saved record
  - saved item remains linked to its detail page
- Automation:
  - Playwright critical flow
- Gates:
  - `pre-merge`, `release`

### DET-01
- Area: Detail
- Goal: Opportunity detail pages expose user-facing decision support, not only raw text.
- Preconditions: seeded catalog
- Assertions:
  - title, status, value, deadline, and sources render
  - next actions are visible
  - official links are present
- Automation:
  - Playwright critical flow
- Gates:
  - `pre-merge`, `release`

### DET-02
- Area: Detail
- Goal: Official links remain syntactically valid and mostly reachable.
- Preconditions: published opportunities with `official_links`
- Assertions:
  - links are well-formed
  - nightly sample success rate stays healthy
- Automation:
  - link health script
- Gates:
  - `nightly`, `release`

### DATA-01
- Area: Data quality
- Goal: Published opportunities are internally coherent.
- Preconditions: seeded or production-like DB
- Assertions:
  - no duplicate slugs
  - required fields are present
  - current version exists
  - official links exist
  - explanation payloads are materializable
- Automation:
  - data integrity script
- Gates:
  - `pre-merge`, `nightly`, `release`

### DATA-02
- Area: Freshness
- Goal: The catalog does not silently go stale.
- Preconditions: populated DB
- Assertions:
  - stale percentages remain under threshold
  - no opportunity exceeds the hard stale threshold
- Automation:
  - freshness script
- Gates:
  - `nightly`, `release`

### QUAL-01
- Area: General quality
- Goal: Core pages remain reachable and structurally sound across the main journey.
- Preconditions: web + API boot locally or in CI
- Assertions:
  - no critical route is broken
  - user can move across auth, onboarding, search, detail, and saved
- Automation:
  - Playwright critical flow
- Gates:
  - `pre-merge`, `release`
