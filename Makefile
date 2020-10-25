all: check
	PYTHONPATH=$(PWD):$(PYTHONPATH) mkdocs build

check:
	python3 setup.py $@ -ms
	black --check -q .
	flake8
	mypy -p waiter
	pytest --cov --cov-fail-under=100
