import asyncio
import collections
import functools
import inspect
import time
from .base import suppress, waiter


def overload(func):
    base = getattr(waiter, func.__name__)
    bind = inspect.signature(func).bind
    (arg, predicate), = func.__annotations__.items()

    def wrapper(*args, **kwargs):
        match = predicate(bind(*args, **kwargs).arguments[arg])
        return (func if match else base)(*args, **kwargs)
    return functools.update_wrapper(wrapper, base)


class awaiter(waiter):
    __doc__ = waiter.__doc__

    async def __aiter__(self):
        start = time.time()
        yield 0.0
        for delay in self.delays:
            remaining = start + self.timeout - time.time()
            if remaining < 0:
                break
            await asyncio.sleep(min(delay, remaining))
            yield time.time() - start
    __aiter__.__doc__ = waiter.__iter__.__doc__

    @overload
    async def throttle(self, iterable: lambda it: isinstance(it, collections.AsyncIterable)):
        anext = iterable.__aiter__().__anext__
        with suppress(StopAsyncIteration):
            async for _ in self:  # noqa
                yield await anext()

    @overload
    async def repeat(self, func: asyncio.iscoroutinefunction, *args, **kwargs):
        async for _ in self:  # noqa
            yield await func(*args, **kwargs)

    @overload
    async def retry(self, exception, func: asyncio.iscoroutinefunction, *args, **kwargs):
        async for _ in self:  # noqa
            with suppress(exception) as excs:
                return await func(*args, **kwargs)
        raise excs[0]

    @overload
    async def poll(self, predicate, func: asyncio.iscoroutinefunction, *args, **kwargs):
        async for result in self.repeat(func, *args, **kwargs):
            if predicate(result):
                return result
        raise StopAsyncIteration
