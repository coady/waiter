check:
	python3 -m pytest --cov

lint:
	black --check .
	flake8
	mypy -p waiter

html:
	PYTHONPATH=$(PWD) python3 -m mkdocs build
