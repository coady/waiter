all: check
	make -C docs html SPHINXOPTS=-W

check:
	python3 setup.py $@ -ms
	black --check -q .
	flake8
	pytest-2.7
	pytest --cov --cov-fail-under=100
