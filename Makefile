check:
	uv run pytest -s --cov

lint:
	uvx ruff check
	uvx ruff format --check
	uvx ty check waiter

html:
	uv run --group docs -w . mkdocs build
