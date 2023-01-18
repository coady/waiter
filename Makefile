check:
	python3 -m pytest -s --cov

lint:
	black --check .
	flake8 --ignore E203,E501,F811 waiter tests
	mypy -p waiter

html:
	PYTHONPATH=$(PWD) python3 -m mkdocs build
