check:
	python -m pytest -s --cov

lint:
	ruff .
	ruff format --check .
	mypy -p waiter

html:
	PYTHONPATH=$(PWD) python -m mkdocs build
