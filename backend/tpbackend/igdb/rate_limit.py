import threading
import time
from collections import deque
from contextlib import contextmanager


class RateLimiter:
    """
    at most max_per_second requests started per second, and at most max_open running at once.
    requests are made from several threads (sync routes, Oblivionis sync), so it's thread safe.
    clock and sleep can be swapped out in tests
    """

    def __init__(
        self,
        max_per_second: int,
        max_open: int,
        clock=time.monotonic,
        sleep=time.sleep,
    ):
        self.max_per_second = max_per_second
        self.open = threading.Semaphore(max_open)
        self.clock = clock
        self.sleep = sleep
        self.lock = threading.Lock()
        self.started: deque[float] = deque()

    def _wait_for_turn(self):
        # holding the lock while sleeping is on purpose, the other threads have to wait anyway
        with self.lock:
            while True:
                now = self.clock()
                while self.started and now - self.started[0] >= 1:
                    self.started.popleft()
                if len(self.started) < self.max_per_second:
                    self.started.append(now)
                    return
                self.sleep(1 - (now - self.started[0]))

    @contextmanager
    def slot(self):
        """wrap a request in this, it waits until the request is allowed"""
        self.open.acquire()
        try:
            self._wait_for_turn()
            yield
        finally:
            self.open.release()
