from setuptools import setup

setup(
    name='waiter',
    version='0.0',
    description='Delayed iteration for polling and retries.',
    long_description=open('README.rst').read(),
    author='Aric Coady',
    author_email='aric.coady@gmail.com',
    url='https://bitbucket.org/coady/waiter',
    license='Apache Software License',
    py_modules=['waiter'],
    tests_require=['pytest-cov'],
    keywords=['wait', 'retry', 'poll', 'delay', 'sleep', 'backoff'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
