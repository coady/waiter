check:
	python3 -m pytest -s --cov

lint:
	black --check .
	flake8 --exclude .venv --ignore E203,E501,F811
	mypy -p waiter

html:
	PYTHONPATH=$(PWD) python3 -m mkdocs build
