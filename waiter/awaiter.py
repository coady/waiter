import asyncio
import time
from typing import AsyncIterable
from multimethod import isa, overload
from .base import suppress, waiter


def override(func):
    return overload(getattr(waiter, func.__name__)).register(func)


class awaiter(waiter):
    __doc__ = waiter.__doc__

    async def __aiter__(self):
        start = time.time()
        yield self.stats.add(0, 0.0)
        for attempt, delay in enumerate(self.delays, 1):
            remaining = start + self.timeout - time.time()
            if remaining < 0:
                break
            await asyncio.sleep(min(delay, remaining))
            yield self.stats.add(attempt, time.time() - start)

    __aiter__.__doc__ = waiter.__iter__.__doc__

    @override
    async def throttle(self, iterable: isa(AsyncIterable)):
        anext = iterable.__aiter__().__anext__
        with suppress(StopAsyncIteration):
            async for _ in self:
                yield await anext()

    @override
    async def repeat(self, func: asyncio.iscoroutinefunction, *args, **kwargs):
        async for _ in self:
            yield await func(*args, **kwargs)

    @override
    async def retry(self, exception, func: asyncio.iscoroutinefunction, *args, **kwargs):
        async for _ in self:
            with suppress(exception) as excs:
                return await func(*args, **kwargs)
        raise excs[0]

    @override
    async def poll(self, predicate, func: asyncio.iscoroutinefunction, *args, **kwargs):
        async for result in self.repeat(func, *args, **kwargs):
            if predicate(result):
                return result
        raise StopAsyncIteration
