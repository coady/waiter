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

__version__ = '0.4'


@contextlib.contextmanager
def suppress(*exceptions):
    """Backport of contextlib.suppress, which also records exception."""
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


class wait(object):
    """An iterable which sleeps for given delays.

    :param delays: any iterable of seconds, or a scalar which is repeated endlessly
    :param timeout: optional timeout for iteration
    """
    def __init__(self, delays, timeout=float('inf')):
        if not isinstance(delays, collections.Iterable):
            delays = itertools.repeat(delays)
        self.delays, self.timeout = delays, timeout

    def __iter__(self):
        """Generate a slow loop of elapsed time."""
        start = time.time()
        yield 0.0
        for delay in self.delays:
            remaining = start + self.timeout - time.time()
            if remaining < 0:
                break
            time.sleep(min(delay, remaining))
            yield time.time() - start

    def clone(self, func, *args):
        return type(self)(reiter(func, *args), self.timeout)

    def map(self, func, *iterables):
        return self.clone(map, func, self.delays, *iterables)

    def __getitem__(self, slc):
        """Slice delays, e.g., to limit attempt count."""
        return self.clone(itertools.islice, self.delays, slc.start, slc.stop, slc.step)

    def __le__(self, ceiling):
        """Limit maximum delay generated."""
        return self.map(partial(min, ceiling))

    def __add__(self, step):
        """Generate incremental backoff."""
        return self.map(operator.add, reiter(itertools.count, 0, step))

    def __mul__(self, step):
        """Generate exponential backoff."""
        return self.map(operator.mul, reiter(map, step.__pow__, reiter(itertools.count)))

    def random(self, start, stop):
        """Add random jitter within given range."""
        return self.map(lambda delay: delay + random.uniform(start, stop))

    def throttle(self, iterable):
        """Delay iteration."""
        return map(operator.itemgetter(1), zip(self, iterable))

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
