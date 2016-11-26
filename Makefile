check:
	python setup.py $@ -mrs
	flake8
	py.test-2.7 --cov
	py.test-3.5 --cov --cov-append --cov-fail-under=100

clean:
	hg st -in | xargs rm
	rm -rf build dist waiter.egg-info

dist:
	python setup.py sdist bdist_wheel
	rst2html.py README.rst $@/README.html
