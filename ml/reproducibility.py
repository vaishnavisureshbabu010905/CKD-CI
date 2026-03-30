from __future__ import annotations

from datetime import datetime
from typing import Any, Dict
import hashlib
import json


def build_inference_metadata(features: Dict[str, Any], model_version: str, user_email: str | None = None) -> Dict[str, Any]:
    """Create reproducibility metadata without altering inference behavior."""
    canonical = json.dumps(features or {}, sort_keys=True, default=str)
    signature = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {
        "timestamp_utc": datetime.utcnow().isoformat(),
        "model_version": model_version,
        "feature_signature_sha256": signature,
        "feature_count": len(features or {}),
        "requested_by": user_email,
    }
