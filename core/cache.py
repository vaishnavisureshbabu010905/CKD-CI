from collections import deque
from threading import Lock

_cache = deque(maxlen=50)
_lock = Lock()


def push_prediction(item: dict) -> None:
    with _lock:
        _cache.appendleft(item)


def list_predictions() -> list:
    with _lock:
        return list(_cache)
