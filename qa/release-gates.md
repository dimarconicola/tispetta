# Release Gates

## Pre-merge gate

This gate must pass before merging to `main`.

Commands:

```bash
pnpm lint
pnpm typecheck
pnpm test
python3 qa/scripts/check_data_integrity.py --reseed
python3 qa/scripts/check_data_freshness.py --reseed
pnpm test:e2e:critical
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

Commands:

```bash
pnpm lint
pnpm typecheck
pnpm test
python3 qa/scripts/check_data_integrity.py --reseed
python3 qa/scripts/check_data_freshness.py --reseed
pnpm test:e2e:critical
python3 qa/scripts/check_link_health.py --reseed --sample-size 25
```

Additional manual review:

- spot-check `app.tispetta.eu`
- confirm footer web/api version alignment
- confirm at least one auth flow against deployed environment

## Nightly data gate

This gate detects catalog drift and freshness regressions.

Commands:

```bash
python3 qa/scripts/check_data_integrity.py --reseed
python3 qa/scripts/check_data_freshness.py --reseed
python3 qa/scripts/check_link_health.py --reseed --sample-size 25
```

Recommended alert thresholds:

- duplicate published slugs: `0`
- published opportunities missing required fields: `0`
- stale over 14 days: `<= 10%`
- stale over 30 days: `0`
- official link health success rate: `>= 95%`
