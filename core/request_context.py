from contextvars import ContextVar
from typing import Optional

_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_prediction_time_ms: ContextVar[Optional[float]] = ContextVar("prediction_time_ms", default=None)


def set_request_id(req_id: str) -> None:
    _request_id.set(req_id)


def get_request_id() -> Optional[str]:
    return _request_id.get()


def set_prediction_time_ms(ms: float) -> None:
    _prediction_time_ms.set(ms)


def get_prediction_time_ms() -> Optional[float]:
    return _prediction_time_ms.get()
