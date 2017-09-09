import pytest
from waiter import wait, first


def test_constructors():
    w = wait([1] * 3)
    assert w.delays == [1, 1, 1]
    assert w.timeout == float('inf')

    w = wait(1, timeout=10)
    assert next(w.delays) == 1
    assert w.timeout == 10

    assert list(wait(1)[:3].delays) == [1, 1, 1]
    assert list((wait(range(5)) <= 3).delays) == [0, 1, 2, 3, 3]
    assert list((wait(1)[:3] + 1).delays) == [1, 2, 3]
    w = wait(1)[:3] * 2
    assert list(w.delays) == list(w.delays) == [1, 2, 4]
    for delay in wait(1)[:100].random(-1, 1).delays:
        assert 0 <= delay < 2


def test_throttling():
    w = wait([0] * 2)
    assert ''.join(w.throttle('ab')) == 'ab'

    it = iter('abcde')
    throttled = w.throttle(it)
    assert next(it) == 'a'
    assert ''.join(throttled) == 'bcd'
    assert next(it) == 'e'


def test_functional():
    w = wait([0] * 2)
    assert w.retry(ValueError, lambda it: int(next(it)), iter('ab0')) == 0
    with pytest.raises(ValueError):
        w.retry(ValueError, lambda it: int(next(it)), iter('abc'))

    assert w.poll(str.islower, next, iter('ABc')) == 'c'
    with pytest.raises(StopIteration):
        assert w.poll(str.islower, next, iter('ABC'))

    assert first(str.islower, w.repeat(next, iter('ABC')), None) is None
    assert list(wait(1, timeout=-1)) == [0.0]


def test_waiting():
    elapsed = list(wait(0.1, timeout=1) * 2)
    assert elapsed[0] == 0.0
    assert 0.1 <= elapsed[1] < 0.3 <= elapsed[2] < 0.7 <= elapsed[3] < 1.0 <= elapsed[4] < 1.1


def test_decorators():
    w = wait(0)[:2]

    @w.repeating
    def func(x):
        return x
    assert ''.join(func('x')) == 'xxx'

    @w.retrying(ValueError)
    def func(it):
        return int(next(it))
    assert func(iter('ab0')) == 0

    @w.polling(str.islower)
    def func(it):
        return next(it)
    assert func(iter('ABc')) == 'c'

    class cls(object):
        @w.repeating
        def repeat(self):
            return self

        @w.retrying(Exception)
        def retry(self):
            return self

        @w.polling(bool)
        def poll(self):
            return self

    obj = cls()
    assert next(obj.repeat()) is obj
    assert obj.retry() is obj
    assert obj.poll() is obj


@pytest.mark.skipif(not hasattr(wait, '__aiter__'), reason='requires Python 3.6+')
def test_async():
    import asyncio
    run = asyncio.get_event_loop().run_until_complete

    ws = wait([]), wait(0)
    for ait in (ws[0].throttle(ws[1]), ws[1].throttle(ws[0])):
        anext = ait.__aiter__().__anext__
        assert run(anext()) == 0.0
        with pytest.raises(StopAsyncIteration):
            run(anext())

    anext = wait([0.1, 0.1], timeout=0.1).__aiter__().__anext__
    assert run(anext()) == 0.0
    assert run(anext()) > 0.0
    with pytest.raises(StopAsyncIteration):
        run(anext())

    w = wait([])
    anext = w.repeat(asyncio.sleep, 0).__aiter__().__anext__
    assert run(anext()) is None
    with pytest.raises(StopAsyncIteration):
        run(anext())

    assert run(w.retry(TypeError, asyncio.sleep, 0)) is None
    with pytest.raises(TypeError):
        run(w.retry(TypeError, asyncio.sleep))

    assert run(w.poll(None.__eq__, asyncio.sleep, 0)) is None
    with pytest.raises(StopAsyncIteration):
        run(w.poll(bool, asyncio.sleep, 0))
