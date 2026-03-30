from typing import Dict, List
from core.validation import validate_features


def validate_request_payload(payload: Dict) -> List[str]:
    issues = []
    if "features" not in payload:
        issues.append("missing:features")
        return issues
    features = payload.get("features")
    issues.extend(validate_features(features))
    return issues
