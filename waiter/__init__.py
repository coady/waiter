import asyncio
import collections
import contextlib
import itertools
import operator
import random
import time
import types
from collections.abc import AsyncIterable, AsyncIterator, Callable, Iterable, Iterator, Sequence
from functools import partial, singledispatchmethod
from typing import Optional


def fibonacci(x, y):
    """Generate fibonacci sequence."""
    while True:
        yield x
        x, y = y, (x + y)


@contextlib.contextmanager
def suppress(*exceptions: Exception):
    """Variant of `contextlib.suppress`, which also records exception."""
    excs: list = []
    try:
        yield excs
    except exceptions as exc:  # type: ignore
        excs.append(exc)


def first(predicate: Callable, iterable: Iterable, *default):
    """Return first item which evaluates to true, like `any` with filtering."""
    return next(filter(predicate, iterable), *default)


class reiter(partial):
    """A partial iterator which is re-iterable."""

    __iter__ = partial.__call__


class partialmethod(partial):
    """Variant of functools.partialmethod."""

    def __get__(self, instance, owner):
        return self if instance is None else types.MethodType(self, instance)


class Stats(collections.Counter):
    """Mapping of attempt counts."""

    def add(self, attempt: int, elapsed: float) -> float:
        """Record attempt and return next value."""
        self[attempt] += 1
        return elapsed


def grouped(queue, size=None):
    """Generate slices from a sequence without relying on a fixed `len`."""
    start = 0
    while group := queue[start : size and start + size]:
        start += len(group)
        yield group


class waiter:
    """An iterable which sleeps for given delays. Aliased as `wait`.

    Args:
        delays iterable | number: any iterable of seconds, or a scalar which is repeated endlessly
        timeout number: optional timeout for iteration
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

    async def __aiter__(self):
        """Asynchronously generate a slow loop of elapsed time."""
        start = time.time()
        yield self.stats.add(0, 0.0)
        for attempt, delay in enumerate(self.delays, 1):
            remaining = start + self.timeout - time.time()
            if remaining < 0:
                break
            await asyncio.sleep(min(delay, remaining))
            yield self.stats.add(attempt, time.time() - start)

    def clone(self, func: Callable, *args) -> 'waiter':
        return type(self)(reiter(func, *args), self.timeout)

    def map(self, func: Callable, *iterables: Iterable) -> 'waiter':
        """Return new waiter with function mapped across delays."""
        return self.clone(map, func, self.delays, *iterables)

    @classmethod
    def fibonacci(cls, delay, **kwargs) -> 'waiter':
        """Create waiter with fibonacci backoff."""
        return cls(reiter(fibonacci, delay, delay), **kwargs)

    @classmethod
    def count(cls, *args, **kwargs) -> 'waiter':
        """Create waiter based on `itertools.count`."""
        return cls(reiter(itertools.count, *args), **kwargs)

    @classmethod
    def accumulate(cls, *args, **kwargs) -> 'waiter':
        """Create waiter based on `itertools.accumulate`."""
        return cls(reiter(itertools.accumulate, *args), **kwargs)

    @classmethod
    def exponential(cls, base, **kwargs) -> 'waiter':
        """Create waiter with exponential backoff."""
        return cls.count(**kwargs).map(base.__pow__)

    @classmethod
    def polynomial(cls, exp, **kwargs) -> 'waiter':
        """Create waiter with polynomial backoff."""
        return cls.count(**kwargs).map(exp.__rpow__)

    def __getitem__(self, slc: slice) -> 'waiter':
        """Slice delays, e.g., to limit attempt count."""
        return self.clone(itertools.islice, self.delays, slc.start, slc.stop, slc.step)

    def __le__(self, ceiling) -> 'waiter':
        """Limit maximum delay generated."""
        return self.map(partial(min, ceiling))

    def __ge__(self, floor) -> 'waiter':
        """Limit minimum delay generated."""
        return self.map(partial(max, floor))

    def __add__(self, step) -> 'waiter':
        """Generate incremental backoff."""
        return self.map(operator.add, reiter(itertools.count, 0, step))

    def __mul__(self, factor) -> 'waiter':
        """Generate exponential backoff."""
        return self.map(operator.mul, reiter(map, factor.__pow__, reiter(itertools.count)))

    def random(self, start, stop) -> 'waiter':
        """Add random jitter within given range."""
        return self.map(lambda delay: delay + random.uniform(start, stop))

    @singledispatchmethod
    def throttle(self, iterable: Iterable):
        """Delay iteration."""
        return map(operator.itemgetter(1), zip(self, iterable))

    @throttle.register
    async def _(self, iterable: AsyncIterable) -> AsyncIterator:
        anext = iterable.__aiter__().__anext__
        with suppress(StopAsyncIteration):  # type: ignore
            async for _ in self:
                yield await anext()

    def stream(self, queue: Iterable, size: Optional[int] = None) -> Iterator:
        """Generate chained values in groups from an iterable.

        The queue can be extended while in use.
        """
        it = iter(queue)
        groups = iter(lambda: list(itertools.islice(it, size)), [])
        if isinstance(queue, Sequence):
            groups = grouped(queue, size)
        return itertools.chain.from_iterable(self.throttle(groups))

    def suppressed(self, exception, func: Callable, iterable: Iterable) -> Iterator[tuple]:
        """Generate `arg, func(arg)` pairs while exception isn't raised."""
        queue = list(iterable)
        for arg in self.stream(queue):
            try:
                yield arg, func(arg)
            except exception:
                queue.append(arg)

    def filtered(self, predicate: Callable, func: Callable, iterable: Iterable) -> Iterator[tuple]:
        """Generate `arg, func(arg)` pairs while predicate evaluates to true."""
        queue = list(iterable)
        for arg in self.stream(queue):
            result = func(arg)
            if predicate(result):
                yield arg, result
            else:
                queue.append(arg)

    def repeat(self, func: Callable, *args, **kwargs):
        """Repeat function call."""
        if asyncio.iscoroutinefunction(func):
            return self.arepeat(func, *args, **kwargs)
        return (func(*args, **kwargs) for _ in self)

    async def arepeat(self, func: Callable, *args, **kwargs) -> AsyncIterator:
        async for _ in self:
            yield await func(*args, **kwargs)

    def retry(self, exception: Exception, func: Callable, *args, **kwargs):
        """Repeat function call until exception isn't raised."""
        if asyncio.iscoroutinefunction(func):
            return self.aretry(exception, func, *args, **kwargs)
        for _ in self:
            with suppress(exception) as excs:
                return func(*args, **kwargs)
        raise excs[0]

    async def aretry(self, exception: Exception, func: Callable, *args, **kwargs):
        async for _ in self:
            with suppress(exception) as excs:
                return await func(*args, **kwargs)
        raise excs[0]

    def poll(self, predicate: Callable, func: Callable, *args, **kwargs):
        """Repeat function call until predicate evaluates to true."""
        if asyncio.iscoroutinefunction(func):
            return self.apoll(predicate, func, *args, **kwargs)
        return first(predicate, self.repeat(func, *args, **kwargs))

    async def apoll(self, predicate: Callable, func: Callable, *args, **kwargs):
        async for result in self.repeat(func, *args, **kwargs):
            if predicate(result):  # pragma: no branch
                return result
        raise StopAsyncIteration

    def repeating(self, func: Callable):
        """A decorator for `repeat`."""
        return partialmethod(self.repeat, func)

    def retrying(self, exception: Exception):
        """Return a decorator for `retry`."""
        return partial(partialmethod, self.retry, exception)

    def polling(self, predicate: Callable):
        """Return a decorator for `poll`."""
        return partial(partialmethod, self.poll, predicate)


wait = waiter
