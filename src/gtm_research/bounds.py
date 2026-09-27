"""Deadline helper for blocking DNS and model calls."""

from queue import Empty, Queue
from threading import Thread


def bounded_call(function, timeout):
    """Bound caller wait; a timed-out worker cannot mutate harness state.

    A daemon worker may finish its in-flight operation later. Network clients
    must also set transport timeouts and disable retries; no new work is started
    by this helper after timeout.
    """
    if timeout <= 0:
        raise TimeoutError
    result = Queue(maxsize=1)

    def worker():
        try:
            result.put((True, function()))
        except Exception as exc:
            result.put((False, exc))

    Thread(target=worker, daemon=True).start()
    try:
        ok, value = result.get(timeout=timeout)
    except Empty:
        raise TimeoutError from None
    if not ok:
        raise value
    return value
