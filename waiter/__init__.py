from .base import first, suppress, waiter as wait  # noqa
with suppress(SyntaxError):
    from .awaiter import awaiter as wait  # noqa

__version__ = '0.5'
