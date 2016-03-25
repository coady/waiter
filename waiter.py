import collections
import itertools
import random
import time
try:
    from future_builtins import filter
except ImportError:
    pass

__version__ = '0.1'


class wait(object):
    """Provide an iterator which sleeps for given delays.

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

    def clone(self, delays):
        return type(self)(delays, self.timeout)

    def __getitem__(self, slc):
        """Slice delays, e.g., to limit attempt count."""
        return self.clone(itertools.islice(self.delays, slc.start, slc.stop, slc.step))

    def __le__(self, ceiling):
        """Limit maximum delay generated."""
        return self.clone(min(delay, ceiling) for delay in self.delays)

    def __add__(self, step):
        """Generate incremental backoff."""
        return self.clone(delay + (step * index) for index, delay in enumerate(self.delays))

    def __mul__(self, step):
        """Generate exponential backoff."""
        return self.clone(delay * (step ** index) for index, delay in enumerate(self.delays))

    def random(self, start, stop):
        """Add random jitter within given range."""
        return self.clone(delay + start + (stop - start) * random.random() for delay in self.delays)

    def retry(self, exception, func, *args, **kwargs):
        """Repeat function call until no exception is raised."""
        exc = None
        for _ in self:
            try:
                return func(*args, **kwargs)
            except exception as e:
                exc = e  # py3 requires a local variable
        raise exc

    def poll(self, predicate, func, *args, **kwargs):
        """Repeat function call until predicate evaluates to true."""
        results = (func(*args, **kwargs) for _ in self)
        return next(filter(predicate, results))
