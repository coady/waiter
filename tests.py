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
