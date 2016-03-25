About waiter
=========================
.. image:: https://img.shields.io/pypi/v/waiter.svg
   :target: https://pypi.python.org/pypi/waiter/
.. image:: https://img.shields.io/pypi/pyversions/waiter.svg
.. image:: https://img.shields.io/pypi/status/waiter.svg
.. image:: https://img.shields.io/travis/coady/waiter.svg
   :target: https://travis-ci.org/coady/waiter
.. image:: https://img.shields.io/codecov/c/github/coady/waiter.svg
   :target: https://codecov.io/github/coady/waiter

Does python need yet another retry / poll library?
It needs at least one that isn't coupled to decorators and functions.
Decorators prevent the caller from customizing delay options.
And even organizing the code around functions prevents custom handling of failures.

Waiter is built around iterators instead, because the foundation of retrying / polling is a slowly executing loop.
The resulting interface is both easier to use and more flexible,
decoupling the delay algorithms from the application logic.

Usage
=========================
Supply a number of seconds to repeat endlessly, or any iterable of seconds.

.. code-block:: python

   from waiter import wait
   wait(1)              # 1, 1, 1, 1, ...
   wait([1] * 3)        # 1, 1, 1
   wait([0.5, 0.5, 60]) # circuit breaker

So any delay algorithm is easily created,
but constructors for common algorithms are also provided.

.. code-block:: python

   wait(1) + 1       # incremental backoff 1, 2, 3, 4, ...
   w = wait(1) * 2   # exponential backoff 1, 2, 4, 8, ...
   w[:3]             # limit attempt count 1, 2, 4
   w <= 5            # set maximum delay   1, 2, 4, 5, 5, 5, ...
   w.random(-1, 1)   # add random jitter

Then simply use the wait object like any iterator, yielding the amount of elapsed time.
Timeouts also supported of course.

.. code-block:: python

   for elapsed in wait(delays):  # first iteration is immediate
      try:                       # then each subsequent iteration sleeps as necessary
         ...
         break
      except ...:
         continue

   for _ in wait(delays, timeout=n) # standard convention for ignoring a loop variable
      ...                           # won't sleep past the timeout
      if ...:
         break

   any(... for _ in wait(delays))   # perfect for tests too

Yes, functional versions are provided too, because they're trivial to implement.

.. code-block:: python

    wait.retry(exception, func, *args, **kwargs)
    wait.poll(predicate, func, *args, **kwargs)

But in the real world:

 * the function might not exist or be succinctly written as a lambda
 * the predicate might not exist or be succinctly written as a lambda
 * logging may be required
 * there may be complex handling of different exceptions or results

So consider the block form, just as decorators don't render ``with`` blocks superfluous.

Installation
=========================
Standard installation from pypi or local download. ::

   $ pip install waiter
   $ python setup.py install

Dependencies
=========================
   * Python 2.7, 3.3+

Tests
=========================
100% branch coverage. ::

   $ py.test [--cov]
