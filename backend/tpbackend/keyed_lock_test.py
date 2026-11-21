import threading
import time

from tpbackend.keyed_lock import KeyedLock


def run_together(count: int, work):
    threads = [threading.Thread(target=work, args=(i,)) for i in range(count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


class TestKeyedLock:
    def test_same_key_one_at_a_time(self):
        locks = KeyedLock()
        inside = 0
        most_inside = 0
        counter = threading.Lock()

        def work(_):
            nonlocal inside, most_inside
            with locks.hold("a"):
                with counter:
                    inside += 1
                    most_inside = max(most_inside, inside)
                time.sleep(0.01)
                with counter:
                    inside -= 1

        run_together(5, work)
        assert most_inside == 1

    def test_other_keys_dont_wait(self):
        locks = KeyedLock()
        entered = threading.Event()
        with locks.hold("a"):

            def other():
                with locks.hold("b"):
                    entered.set()

            thread = threading.Thread(target=other)
            thread.start()
            assert entered.wait(timeout=1)
            thread.join()

    def test_forgets_unused_keys(self):
        locks = KeyedLock()

        def work(i):
            with locks.hold(str(i % 2)):
                time.sleep(0.01)

        run_together(5, work)
        assert locks.locks == {}
