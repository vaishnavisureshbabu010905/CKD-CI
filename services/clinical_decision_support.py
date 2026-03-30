from __future__ import annotations

from typing import Any, Dict, List


def _risk_class(predicted_label: str | int | None) -> int:
    try:
        return int(predicted_label)
    except Exception:
        text = str(predicted_label or "").strip().lower()
        if "high" in text:
            return 3
        if "moderate" in text:
            return 2
        if "low" in text:
            return 1
        return 0


def clinical_decision_support(predicted_label: str | int | None, features: Dict[str, Any] | None) -> Dict[str, Any]:
    risk = _risk_class(predicted_label)
    f = features or {}

    headline = "Stable profile"
    interpretation = "Current profile does not suggest immediate cognitive decline risk."
    badge = "Stable"
    actions: List[str] = ["Continue routine CKD monitoring"]

    if risk >= 3:
        headline = "HIGH RISK DETECTED"
        interpretation = "Kidney function decline pattern and clinical profile suggest elevated cognitive impairment risk."
        badge = "Critical"
        actions = [
            "Nephrology referral",
            "Cognitive screening (MoCA/MMSE)",
            "Medication review for nephrotoxic burden",
            "Follow-up laboratory testing within 2-4 weeks",
        ]
    elif risk == 2:
        headline = "Moderate risk profile"
        interpretation = "Findings indicate moderate cognitive risk requiring closer surveillance."
        badge = "Attention"
        actions = [
            "Schedule focused nephrology follow-up",
            "Initiate targeted cognitive screening",
            "Review cardiovascular and metabolic control",
        ]
    elif risk == 1:
        headline = "Low risk profile"
        interpretation = "Mild risk markers identified; monitor longitudinal trend."
        badge = "Monitor"
        actions = [
            "Repeat labs in routine interval",
            "Assess adherence and blood pressure control",
        ]

    try:
        egfr = float(f.get("egfr")) if f.get("egfr") is not None else None
        if egfr is not None and egfr < 30 and "Urgent nephrology review" not in actions:
            actions.insert(0, "Urgent nephrology review")
    except Exception:
        pass

    next_step = actions[0] if actions else "Continue routine monitoring"

    return {
        "headline": headline,
        "interpretation": interpretation,
        "actions": actions,
        "recommended_next_step": next_step,
        "badge": badge,
    }
