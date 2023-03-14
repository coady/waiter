check:
	python -m pytest -s --cov

lint:
	black --check .
	ruff .
	mypy -p waiter

html:
	PYTHONPATH=$(PWD) python -m mkdocs build
