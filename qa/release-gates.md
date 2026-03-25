# Release Gates

## Pre-merge gate

This gate must pass before merging to `main`.

Command:

```bash
pnpm test:pr-gate
```

Merge-blocking failures:

- auth flow broken
- onboarding core path broken
- results not shown after core save
- save/unsave broken
- detail page broken
- duplicate published slugs
- missing explanation payload for ranked items
- lint/typecheck/test failure

## Major release gate

This gate must pass before every major release.

Command:

```bash
pnpm test:release-gate
```

Additional manual review:

- spot-check `app.tispetta.eu`
- confirm footer web/api version alignment
- confirm at least one auth flow against deployed environment

## Nightly data gate

This gate detects catalog drift and freshness regressions.

Command:

```bash
pnpm test:nightly-data
```

Recommended alert thresholds:

- duplicate published slugs: `0`
- published opportunities missing required fields: `0`
- stale over 14 days: `<= 10%`
- stale over 30 days: `0`
- official link health success rate: `>= 95%`
