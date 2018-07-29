check:
	python3 setup.py $@ -ms
	flake8
	pytest-2.7
	pytest --cov --cov-fail-under=100

clean:
	hg st -in | xargs rm
	rm -rf build dist waiter.egg-info

dist:
	python3 setup.py sdist bdist_wheel
