import asyncio
import collections
import time
from .base import suppress, waiter


class awaiter(waiter):
    __doc__ = waiter.__doc__

    async def __aiter__(self):
        """Asynchronously generate a slow loop of elapsed time."""
        start = time.time()
        yield 0.0
        for delay in self.delays:
            remaining = start + self.timeout - time.time()
            if remaining < 0:
                break
            await asyncio.sleep(min(delay, remaining))
            yield time.time() - start

    async def athrottle(self, aiterable):
        anext = aiterable.__aiter__().__anext__
        with suppress(StopAsyncIteration):
            async for _ in self:  # noqa
                yield await anext()

    async def arepeat(self, func, *args, **kwargs):
        async for _ in self:  # noqa
            yield await func(*args, **kwargs)

    async def aretry(self, exception, func, *args, **kwargs):
        async for _ in self:  # noqa
            with suppress(exception) as excs:
                return await func(*args, **kwargs)
        raise excs[0]

    async def apoll(self, predicate, func, *args, **kwargs):
        async for result in self.arepeat(func, *args, **kwargs):
            if predicate(result):
                return result
        raise StopAsyncIteration

    def throttle(self, iterable):
        """Delay iteration, or async iteration."""
        if isinstance(iterable, collections.AsyncIterable):
            return self.athrottle(iterable)
        return super().throttle(iterable)

    def repeat(self, func, *args, **kwargs):
        """Repeat function or coroutine call."""
        method = self.arepeat if asyncio.iscoroutinefunction(func) else super().repeat
        return method(func, *args, **kwargs)

    def retry(self, exception, func, *args, **kwargs):
        """Repeat function or coroutine call until exception isn't raised."""
        method = self.aretry if asyncio.iscoroutinefunction(func) else super().retry
        return method(exception, func, *args, **kwargs)

    def poll(self, predicate, func, *args, **kwargs):
        """Repeat function or coroutine call until predicate evaluates to true."""
        method = self.apoll if asyncio.iscoroutinefunction(func) else super().poll
        return method(predicate, func, *args, **kwargs)
