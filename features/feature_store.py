from collections import deque
from threading import Lock
from typing import Dict, Optional
from datetime import datetime

_store = {}
_lock = Lock()


def store_features(patient_identifier: str, features: Dict) -> None:
    with _lock:
        _store[patient_identifier] = {"features": features.copy(), "updated_at": datetime.utcnow().isoformat()}


def get_latest_features(patient_identifier: str) -> Optional[Dict]:
    with _lock:
        return _store.get(patient_identifier)


def validate_features_entry(features: Dict) -> bool:
    # Reuse server-side validation
    from core.validation import validate_features

    issues = validate_features(features)
    return len(issues) == 0
