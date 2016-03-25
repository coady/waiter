check:
	python setup.py $@ -mrs
	flake8
	py.test-2.7 --cov
	py.test-3.5 --cov --cov-append --cov-fail-under=100

clean:
	hg st -in | xargs rm
	rm -rf dist waiter.egg-info

dist:
	python setup.py sdist
	rst2html.py README.rst $@/README.html
