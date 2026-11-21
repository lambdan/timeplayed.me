"""
One lock per key, so the same thing (like fetching a game's cover) isn't done by several
requests at once: the others wait and then use what the first one stored.
Only within this process, which is all there is
"""

import threading
from contextlib import contextmanager


class KeyedLock:
    def __init__(self):
        self.guard = threading.Lock()
        # key -> (lock, how many hold or wait for it), removed when nobody does
        self.locks: dict[str, tuple[threading.Lock, int]] = {}

    @contextmanager
    def hold(self, key: str):
        with self.guard:
            lock, users = self.locks.get(key, (threading.Lock(), 0))
            self.locks[key] = (lock, users + 1)
        try:
            with lock:
                yield
        finally:
            with self.guard:
                lock, users = self.locks[key]
                if users == 1:
                    del self.locks[key]
                else:
                    self.locks[key] = (lock, users - 1)
