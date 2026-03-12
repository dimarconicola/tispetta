.PHONY: infra-up infra-down install-python seed dev test

infra-up:
	docker compose up -d

infra-down:
	docker compose down

install-python:
	pip install -e services/api
	pip install -e services/worker

seed:
	cd services/api && PYTHONPATH=. python3 -m app.seeds.cli

dev:
	pnpm dev

test:
	pnpm test
