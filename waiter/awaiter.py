import asyncio
import time
from .base import waiter


class awaiter(waiter):
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
