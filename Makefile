check:
	pytest --cov

lint:
	python3 setup.py check -ms
	black --check .
	flake8
	mypy -p waiter

html:
	PYTHONPATH=$(PWD):$(PYTHONPATH) mkdocs build
