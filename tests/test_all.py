import asyncio
import itertools
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
    assert list((wait(range(5)) >= 2).delays) == [2, 2, 2, 3, 4]
    assert list((wait(1)[:3] + 1).delays) == [1, 2, 3]
    w = wait(1)[:3] * 2
    assert list(w.delays) == list(w.delays) == [1, 2, 4]
    for delay in wait(1)[:100].random(-1, 1).delays:
        assert 0 <= delay < 2

    assert list(wait.fibonacci(1)[:5].delays) == [1, 1, 2, 3, 5]
    assert list(wait.count(1)[:5].delays) == [1, 2, 3, 4, 5]
    if hasattr(itertools, 'accumulate'):
        assert list(wait.accumulate(range(5)).delays) == [0, 1, 3, 6, 10]
    assert list(wait.exponential(2)[:5].delays) == [1, 2, 4, 8, 16]
    assert list(wait.polynomial(2)[:5].delays) == [0, 1, 4, 9, 16]


def test_iteration():
    w = wait([0] * 2)
    assert ''.join(w.throttle('ab')) == 'ab'

    it = iter('abcde')
    throttled = w.throttle(it)
    assert next(it) == 'a'
    assert ''.join(throttled) == 'bcd'
    assert next(it) == 'e'

    assert ''.join(w.stream('abc')) == 'abc'
    assert ''.join(w.stream('abc', 2)) == 'abc'
    assert ''.join(w.stream(iter('abc'), 2)) == 'abc'
    seq = ['a']
    it = w.stream(seq)
    assert next(it) == 'a'
    seq.append('b')
    assert list(it) == ['b']
    assert list(w.suppressed(ValueError, int, 'a0')) == [('0', 0)]
    assert list(w.filtered(str.isalpha, str.upper, iter('0a'))) == [('a', 'A')]


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

    class cls:
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


def test_stats():
    w = wait([0] * 2)
    for index, elapsed in enumerate(w):
        assert elapsed >= 0.0
        assert w.stats[index] == 1


def test_async():
    run = asyncio.new_event_loop().run_until_complete

    ws = wait([]), wait(0)
    for ait in (ws[0].throttle(ws[1]), ws[1].throttle(ws[0])):
        anext = ait.__aiter__().__anext__
        assert run(anext()) == 0.0
        with pytest.raises(StopAsyncIteration):
            run(anext())
    assert ws[0].stats == {0: 2}
    assert ws[1].stats == {0: 2, 1: 1}

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
