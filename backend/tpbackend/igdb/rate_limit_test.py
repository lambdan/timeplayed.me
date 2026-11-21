import pytest

from tpbackend.igdb.rate_limit import RateLimiter


class FakeClock:
    """sleeping moves the time forward instead of actually waiting"""

    def __init__(self):
        self.now = 100.0
        self.slept: list[float] = []

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float):
        self.slept.append(seconds)
        self.now += seconds


def make_limiter(fake: FakeClock, max_per_second=4, max_open=8) -> RateLimiter:
    return RateLimiter(max_per_second, max_open, clock=fake.clock, sleep=fake.sleep)


class TestRateLimiter:
    def test_under_the_limit_does_not_wait(self):
        fake = FakeClock()
        limiter = make_limiter(fake)
        for _ in range(4):
            with limiter.slot():
                pass
        assert fake.slept == []

    def test_fifth_request_in_a_second_waits(self):
        fake = FakeClock()
        limiter = make_limiter(fake)
        for _ in range(5):
            with limiter.slot():
                pass
        assert fake.slept == [1.0]

    def test_waits_only_until_the_oldest_is_a_second_old(self):
        fake = FakeClock()
        limiter = make_limiter(fake)
        for _ in range(4):
            with limiter.slot():
                pass
            fake.now += 0.1
        # the first one started 0.4s ago
        with limiter.slot():
            pass
        assert fake.slept == [pytest.approx(0.6)]

    def test_requests_older_than_a_second_do_not_count(self):
        fake = FakeClock()
        limiter = make_limiter(fake)
        for _ in range(4):
            with limiter.slot():
                pass
        fake.now += 1
        for _ in range(4):
            with limiter.slot():
                pass
        assert fake.slept == []

    def test_open_requests_are_limited(self):
        fake = FakeClock()
        limiter = make_limiter(fake, max_per_second=100, max_open=2)
        with limiter.slot():
            with limiter.slot():
                assert not limiter.open.acquire(blocking=False)
        # both are done, so there's room again
        assert limiter.open.acquire(blocking=False)
