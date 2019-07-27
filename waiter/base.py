import collections
import contextlib
import itertools
import operator
import random
import time
import types
from functools import partial

try:
    from future_builtins import filter, map, zip
except ImportError:
    pass


def fibonacci(x, y):
    """Generate fibonacci sequence."""
    while True:
        yield x
        x, y = y, (x + y)


@contextlib.contextmanager
def suppress(*exceptions):
    """Backport of `contextlib.suppress`, which also records exception."""
    excs = []
    try:
        yield excs
    except exceptions as exc:
        excs.append(exc)


def first(predicate, iterable, *default):
    """Return first item which evaluates to true, like `any` with filtering."""
    return next(filter(predicate, iterable), *default)


class reiter(partial):
    """A partial iterator which is re-iterable."""

    __iter__ = partial.__call__


class partialmethod(partial):
    """Backport of functools.partialmethod."""

    def __get__(self, instance, owner):
        return self if instance is None else types.MethodType(self, instance)


class Stats(collections.Counter):
    """Mapping of attempt counts."""

    def add(self, attempt, elapsed):
        """Record attempt and return next value."""
        self[attempt] += 1
        return elapsed

    @property
    def total(self):
        """total number of attempts"""
        return sum(self.values())

    @property
    def failures(self):
        """number of repeat attempts"""
        return self.total - self[0]


class waiter(object):
    """An iterable which sleeps for given delays.

    :param delays: any iterable of seconds, or a scalar which is repeated endlessly
    :param timeout: optional timeout for iteration
    """

    Stats = Stats

    def __init__(self, delays, timeout=float('inf')):
        with suppress(TypeError) as excs:
            iter(delays)
        self.delays = itertools.repeat(delays) if excs else delays
        self.timeout = timeout
        self.stats = self.Stats()

    def __iter__(self):
        """Generate a slow loop of elapsed time."""
        start = time.time()
        yield self.stats.add(0, 0.0)
        for attempt, delay in enumerate(self.delays, 1):
            remaining = start + self.timeout - time.time()
            if remaining < 0:
                break
            time.sleep(min(delay, remaining))
            yield self.stats.add(attempt, time.time() - start)

    def clone(self, func, *args):
        return type(self)(reiter(func, *args), self.timeout)

    def map(self, func, *iterables):
        """Return new waiter with function mapped across delays."""
        return self.clone(map, func, self.delays, *iterables)

    @classmethod
    def fibonacci(cls, delay, **kwargs):
        """Create waiter with fibonacci backoff."""
        return cls(reiter(fibonacci, delay, delay), **kwargs)

    @classmethod
    def count(cls, *args, **kwargs):
        """Create waiter based on `itertools.count`."""
        return cls(reiter(itertools.count, *args), **kwargs)

    @classmethod
    def accumulate(cls, *args, **kwargs):
        """Create waiter based on `itertools.accumulate` (requires Python 3)."""
        return cls(reiter(itertools.accumulate, *args), **kwargs)

    @classmethod
    def exponential(cls, base, **kwargs):
        """Create waiter with exponential backoff."""
        return cls.count(**kwargs).map(base.__pow__)

    @classmethod
    def polynomial(cls, exp, **kwargs):
        """Create waiter with polynomial backoff."""
        return cls.count(**kwargs).map(exp.__rpow__)

    def __getitem__(self, slc):
        """Slice delays, e.g., to limit attempt count."""
        return self.clone(itertools.islice, self.delays, slc.start, slc.stop, slc.step)

    def __le__(self, ceiling):
        """Limit maximum delay generated."""
        return self.map(partial(min, ceiling))

    def __ge__(self, floor):
        """Limit minimum delay generated."""
        return self.map(partial(max, floor))

    def __add__(self, step):
        """Generate incremental backoff."""
        return self.map(operator.add, reiter(itertools.count, 0, step))

    def __mul__(self, factor):
        """Generate exponential backoff."""
        return self.map(operator.mul, reiter(map, factor.__pow__, reiter(itertools.count)))

    def random(self, start, stop):
        """Add random jitter within given range."""
        return self.map(lambda delay: delay + random.uniform(start, stop))

    def throttle(self, iterable):
        """Delay iteration."""
        return map(operator.itemgetter(1), zip(self, iterable))

    def stream(self, queue):
        """Generate chained values in batches from a mutable sequence."""
        start = 0
        for _ in self:  # pragma: no branch
            values, start = queue[start:], len(queue)
            if not values:
                break
            for value in values:
                yield value

    def suppressed(self, exception, func, iterable):
        """Provisionally generate `arg, func(arg)` pairs while exception isn't raised."""
        queue = list(iterable)
        for arg in self.stream(queue):
            try:
                yield arg, func(arg)
            except exception:
                queue.append(arg)

    def filtered(self, predicate, func, iterable):
        """Provisionally generate `arg, func(arg)` pairs while predicate evaluates to true."""
        queue = list(iterable)
        for arg in self.stream(queue):
            result = func(arg)
            if predicate(result):
                yield arg, result
            else:
                queue.append(arg)

    def repeat(self, func, *args, **kwargs):
        """Repeat function call."""
        return (func(*args, **kwargs) for _ in self)

    def retry(self, exception, func, *args, **kwargs):
        """Repeat function call until exception isn't raised."""
        for _ in self:
            with suppress(exception) as excs:
                return func(*args, **kwargs)
        raise excs[0]

    def poll(self, predicate, func, *args, **kwargs):
        """Repeat function call until predicate evaluates to true."""
        return first(predicate, self.repeat(func, *args, **kwargs))

    def repeating(self, func):
        """A decorator for `repeat`."""
        return partialmethod(self.repeat, func)

    def retrying(self, exception):
        """Return a decorator for `retry`."""
        return partial(partialmethod, self.retry, exception)

    def polling(self, predicate):
        """Return a decorator for `poll`."""
        return partial(partialmethod, self.poll, predicate)
