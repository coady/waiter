[![image](https://img.shields.io/pypi/v/waiter.svg)](https://pypi.org/project/waiter/)
![image](https://img.shields.io/pypi/pyversions/waiter.svg)
[![image](https://pepy.tech/badge/waiter)](https://pepy.tech/project/waiter)
![image](https://img.shields.io/pypi/status/waiter.svg)
[![image](https://github.com/coady/waiter/workflows/build/badge.svg)](https://github.com/coady/waiter/actions)
[![image](https://codecov.io/gh/coady/waiter/branch/main/graph/badge.svg)](https://codecov.io/gh/coady/waiter/)
[![image](https://github.com/coady/waiter/workflows/codeql/badge.svg)](https://github.com/coady/waiter/security/code-scanning)
[![image](https://img.shields.io/badge/code%20style-black-000000.svg)](https://pypi.org/project/black/)
[![image](http://mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

Does Python need yet another retry / poll library? It needs at least one that isn't coupled to decorators and functions. Decorators prevent the caller from customizing delay options, and organizing the code around functions hinders any custom handling of failures.

Waiter is built around iteration instead, because the foundation of retrying / polling is a slowly executing loop. The resulting interface is both easier to use and more flexible, decoupling the delay algorithms from the application logic.

## Usage
### creation
Supply a number of seconds to repeat endlessly, or any iterable of seconds.

```python
from waiter import wait

wait(1)                 # 1, 1, 1, 1, ...
wait([1] * 3)           # 1, 1, 1
wait([0.5, 0.5, 60])    # circuit breaker
```

Iterable delays can express any waiting strategy, and constructors for common algorithms are also provided.

```python
wait.count(1)           # incremental backoff 1, 2, 3, 4, 5, ...
wait(1) + 1             # alternate syntax 1, 2, 3, 4, 5, ...
wait.fibonacci(1)       # 1, 1, 2, 3, 5, ...
wait.polynomial(2)      # 0, 1, 4, 9, 16, ...

wait.exponential(2)     # exponential backoff 1, 2, 4, 8, ...
backoff = wait(1) * 2   # alternate syntax 1, 2, 4, 8, ...
backoff[:3]             # limit attempt count 1, 2, 4
backoff <= 5            # set maximum delay   1, 2, 4, 5, 5, 5, ...
backoff.random(-1, 1)   # add random jitter
```

### iteration
Then simply use the `wait` object like any iterable, yielding the amount of elapsed time. Timeouts also supported of course.

```python
from waiter import wait, suppress, first

for elapsed in wait(delays):            # first iteration is immediate
    with suppress(exception):           # then each subsequent iteration sleeps as necessary
        ...
        break

for _ in wait(delays, timeout):         # standard convention for ignoring a loop variable
    ...                                 # won't sleep past the timeout
    if ...:
        break

results = (... for _ in wait(delays))   # expressions are even easier
first(predicate, results[, default])    # filter for first true item
assert any(results)                     # perfect for tests too
```

### functions
Yes, functional versions are provided, as well as being trivial to implement.

```python
wait(...).throttle(iterable)                      # generate items from iterable
wait(...).repeat(func, *args, **kwargs)           # generate successive results
wait(...).retry(exception, func, *args, **kwargs) # return first success or re-raise exception
wait(...).poll(predicate, func, *args, **kwargs)  # return first success or raise StopIteration
```

The decorator variants are simply partial applications of the corresponding methods. Note decorator syntax doesn't support arbitrary expressions.

```python
backoff = wait(0.1) * 2
@backoff.repeating
@backoff.retrying(exception)
@backoff.polling(predicate)
```

But in the real world:
* the function may not exist or be succinctly written as a lambda
* the predicate may not exist or be succinctly written as a lambda
* logging may be required
* there may be complex handling of different exceptions or results

So consider the block form, just as decorators don't render `with` blocks superfluous. Also note `wait` objects are re-iterable provided their original delays were.

### async
Waiters also support async iteration. `throttle` optionally accepts an async iterable. `repeat`, `retry`, and `poll` optionally accept coroutine functions.

### statistics
Waiter objects have a `stats` attribute for aggregating statistics about the calls made. The base implementation provides `total` and `failure` counts. The interface of the `stats` object itself is considered provisional for now, but can be extended by overriding the `Stats` class attribute. This also allows customization of the iterable values; elapsed time is the default.

## Installation
```console
% pip install waiter
```

## Dependencies
* multimethod

## Tests
100% branch coverage.

```console
% pytest [--cov]
```

## Changes
1.2

* Python >=3.6 required

1.1

* Stream from sized groups

1.0

* Map a function across an iterable in batches

0.6

* Extensible iterable values and statistics
* Additional constructors: fibonacci, polynomial, accumulate

0.5

* Asynchronous iteration

0.4

* Decorators support methods
* Iterables can be throttled

0.3

* Waiters behave as iterables instead of iterators
* Support for function decorators

0.2

* `suppress` context manager for exception handling
* `repeat` method for decoupled iteration
* `first` function for convenient filtering
