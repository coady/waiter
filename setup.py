from setuptools import setup

setup(
    name='waiter',
    version='1.1',
    description='Delayed iteration for polling and retries.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Aric Coady',
    author_email='aric.coady@gmail.com',
    url='https://github.com/coady/waiter',
    project_urls={'Documentation': 'https://waiter.readthedocs.io'},
    license='Apache Software License',
    py_modules=['waiter'],
    install_requires=['multimethod>=1.0'],
    extras_require={'docs': ['recommonmark', 'nbsphinx', 'jupyter', 'httpx']},
    python_requires='>=3.6',
    tests_require=['pytest-cov'],
    keywords='wait retry poll delay sleep timeout incremental exponential backoff async',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
