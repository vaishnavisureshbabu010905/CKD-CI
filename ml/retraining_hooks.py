from __future__ import annotations

from datetime import datetime
from typing import Dict


def get_retraining_hooks() -> Dict[str, object]:
    """Return non-invasive placeholders for future automation workflows."""
    return {
        "auto_retraining_enabled": False,
        "drift_alert_webhook": None,
        "scheduled_retraining_cron": None,
        "last_checked_at": datetime.utcnow().isoformat(),
        "notes": "Hooks are placeholders for MLOps orchestration integration.",
    }
