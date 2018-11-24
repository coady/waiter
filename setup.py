from setuptools import setup

setup(
    name='waiter',
    version='0.5',
    description='Delayed iteration for polling and retries.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Aric Coady',
    author_email='aric.coady@gmail.com',
    url='https://github.com/coady/waiter',
    license='Apache Software License',
    packages=['waiter'],
    extras_require={
        ':python_version>="3.6"': ['multimethod>=0.7'],
        'docs': ['nbsphinx', 'm2r', 'jupyter', 'aiohttp'],
    },
    python_requires='>=2.7',
    tests_require=['pytest-cov'],
    keywords='wait retry poll delay sleep timeout incremental exponential backoff async',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
