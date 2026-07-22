.PHONY: dev test lint fmt typecheck

dev:
	docker compose up -d
	uv run uvicorn askp.app:create_app --factory --reload --host 127.0.0.1 --port 8000

test:
	uv run pytest --cov

lint:
	uv run ruff check .
	uv run ruff format --check .

fmt:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run mypy --strict src tests
