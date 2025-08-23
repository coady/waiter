check:
	uv run pytest -s --cov

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy -p waiter

html:
	uv run --with waiter mkdocs build
