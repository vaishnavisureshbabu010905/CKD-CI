"""
Risk progression and escalation detection system.

Tracks patient risk changes, detects escalations, and provides clinical alerts.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import pandas as pd


@dataclass
class RiskEvent:
    """Single risk assessment event."""
    prediction_id: int
    patient_id: int
    risk_class: int  # 0-3
    confidence: float
    timestamp: datetime
    model_version: str
    features: Dict[str, float]


@dataclass
class RiskProgression:
    """Patient's risk progression analysis."""
    patient_id: int
    current_risk_class: int
    previous_risk_class: Optional[int]
    risk_changed: bool
    escalation_detected: bool
    escalation_direction: str  # "up", "down", "stable"
    change_magnitude: int  # 0, 1, 2, 3 (number of stages)
    days_at_current_risk: float
    trend: str  # "improving", "stable", "worsening"
    consecutive_escalations: int  # Number of consecutive pred with increasing risk
    high_risk_duration: Optional[timedelta]  # How long at high risk


class RiskProgressionEngine:
    """Track and detect patient risk changes."""
    
    MIN_EVENTS_FOR_TREND = 3
    ESCALATION_THRESHOLD_DAYS = 7  # Consider escalation if risk increase within N days
    
    def __init__(self):
        self.risk_history: Dict[int, List[RiskEvent]] = {}
    
    def add_prediction(self, pred_dict: Dict) -> None:
        """Record new prediction."""
        patient_id = pred_dict.get("patient_id")
        if not patient_id:
            return
        
        if patient_id not in self.risk_history:
            self.risk_history[patient_id] = []
        
        event = RiskEvent(
            prediction_id=pred_dict.get("id"),
            patient_id=patient_id,
            risk_class=int(pred_dict.get("predicted_label", 0)),
            confidence=float(pred_dict.get("confidence", 0.5)),
            timestamp=datetime.fromisoformat(pred_dict.get("created_at", datetime.utcnow().isoformat())),
            model_version=str(pred_dict.get("model_version", "unknown")),
            features=pred_dict.get("input_features", {}),
        )
        
        self.risk_history[patient_id].append(event)
        # Keep only last 30 events per patient
        self.risk_history[patient_id] = self.risk_history[patient_id][-30:]
    
    def get_progression(self, patient_id: int) -> RiskProgression:
        """Analyze patient's risk progression."""
        history = self.risk_history.get(patient_id, [])
        
        if not history:
            return RiskProgression(
                patient_id=patient_id,
                current_risk_class=None,
                previous_risk_class=None,
                risk_changed=False,
                escalation_detected=False,
                escalation_direction="stable",
                change_magnitude=0,
                days_at_current_risk=0,
                trend="unknown",
                consecutive_escalations=0,
                high_risk_duration=None,
            )
        
        # Sort by timestamp
        history = sorted(history, key=lambda e: e.timestamp)
        
        current = history[-1]
        previous = history[-2] if len(history) >= 2 else None
        
        # Detect escalation (within threshold days)
        escalation_detected = False
        escalation_direction = "stable"
        
        if previous:
            time_diff = (current.timestamp - previous.timestamp).total_seconds() / 86400  # days
            
            if time_diff <= self.ESCALATION_THRESHOLD_DAYS:
                if current.risk_class > previous.risk_class:
                    escalation_detected = True
                    escalation_direction = "up"
                elif current.risk_class < previous.risk_class:
                    escalation_direction = "down"
        
        # Calculate days at current risk
        recent_same_risk = [e for e in history[-10:] if e.risk_class == current.risk_class]
        if recent_same_risk:
            days_at_current = (current.timestamp - recent_same_risk[0].timestamp).total_seconds() / 86400
        else:
            days_at_current = 0
        
        # Calculate trend from last N events
        trend = self._calculate_trend(history[-self.MIN_EVENTS_FOR_TREND:])
        
        # Consecutive escalations
        consecutive_escalations = self._count_consecutive_escalations(history)
        
        # How long at high risk
        high_risk_duration = self._get_high_risk_duration(history)
        
        return RiskProgression(
            patient_id=patient_id,
            current_risk_class=current.risk_class,
            previous_risk_class=previous.risk_class if previous else None,
            risk_changed=previous is not None and current.risk_class != previous.risk_class,
            escalation_detected=escalation_detected,
            escalation_direction=escalation_direction,
            change_magnitude=abs(current.risk_class - (previous.risk_class if previous else current.risk_class)),
            days_at_current_risk=days_at_current,
            trend=trend,
            consecutive_escalations=consecutive_escalations,
            high_risk_duration=high_risk_duration,
        )
    
    def _calculate_trend(self, recent_events: List[RiskEvent]) -> str:
        """Calculate trend from recent events."""
        if len(recent_events) < self.MIN_EVENTS_FOR_TREND:
            return "insufficient_data"
        
        classes = [e.risk_class for e in recent_events]
        
        if classes[-1] > classes[0]:
            return "worsening"
        elif classes[-1] < classes[0]:
            return "improving"
        else:
            # Check overall trend
            total_change = classes[-1] - classes[0]
            if total_change > 0:
                return "worsening"
            elif total_change < 0:
                return "improving"
            return "stable"
    
    def _count_consecutive_escalations(self, history: List[RiskEvent]) -> int:
        """Count consecutive increases in risk."""
        count = 0
        for i in range(len(history) - 1, 0, -1):
            if history[i].risk_class > history[i-1].risk_class:
                count += 1
            else:
                break
        return count
    
    def _get_high_risk_duration(self, history: List[RiskEvent]) -> Optional[timedelta]:
        """Get duration spent at high risk (class 3)."""
        high_risk_events = [e for e in history if e.risk_class >= 3]
        
        if not high_risk_events:
            return None
        
        if len(high_risk_events) == 1:
            return timedelta(0)
        
        first_high_risk = high_risk_events[0]
        last_high_risk = high_risk_events[-1]
        
        return last_high_risk.timestamp - first_high_risk.timestamp
    
    def get_risk_history_dataframe(self, patient_id: int) -> pd.DataFrame:
        """Get risk history as DataFrame for visualization."""
        history = self.risk_history.get(patient_id, [])
        
        if not history:
            return pd.DataFrame()
        
        data = [
            {
                "timestamp": e.timestamp,
                "risk_class": e.risk_class,
                "confidence": e.confidence,
                "model_version": e.model_version,
                "prediction_id": e.prediction_id,
                "egfr": e.features.get("egfr"),
                "creatinine": e.features.get("creatinine"),
            }
            for e in sorted(history, key=lambda e: e.timestamp)
        ]
        
        return pd.DataFrame(data)
    
    def generate_risk_alerts(self, progression: RiskProgression, patient_id: int) -> List[Dict]:
        """Generate clinical alerts based on risk progression."""
        alerts = []
        
        # High risk alert
        if progression.current_risk_class == 3:
            alerts.append({
                "severity": "CRITICAL",
                "title": "HIGH RISK - Cognitive Decline Detected",
                "detail": f"Patient at high risk (class 3). Recommend immediate cognitive assessment.",
                "type": "risk_level",
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        # Escalation alert
        if progression.escalation_detected and progression.escalation_direction == "up":
            prev = progression.previous_risk_class or 0
            curr = progression.current_risk_class
            alerts.append({
                "severity": "WARNING",
                "title": "⚠️ RISK ESCALATION DETECTED",
                "detail": f"Risk increased from class {prev} to {curr}. {progression.change_magnitude} stage(s) worsening.",
                "type": "escalation",
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        # Worsening trend alert
        if progression.trend == "worsening" and progression.consecutive_escalations >= 2:
            alerts.append({
                "severity": "WARNING",
                "title": "Worsening Trend Observed",
                "detail": f"{progression.consecutive_escalations} consecutive risk increases detected.",
                "type": "trend",
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        # Improving alert
        if progression.escalation_direction == "down" and progression.previous_risk_class is not None:
            prev = progression.previous_risk_class
            curr = progression.current_risk_class
            alerts.append({
                "severity": "INFO",
                "title": "✓ Risk Improvement",
                "detail": f"Positive trend: Risk decreased from class {prev} to {curr}.",
                "type": "improvement",
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        # Long high-risk duration
        if progression.high_risk_duration and progression.high_risk_duration.days >= 7:
            days = progression.high_risk_duration.days
            alerts.append({
                "severity": "WARNING",
                "title": "Prolonged High Risk Period",
                "detail": f"Patient has been at high risk for {days} days. Review intervention strategy.",
                "type": "duration",
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        return alerts


def format_risk_progression_summary(prog: RiskProgression) -> str:
    """Format progression for display."""
    status = "No change"
    if prog.escalation_detected and prog.escalation_direction == "up":
        status = f"⚠️ ESCALATION: {prog.change_magnitude} stage(s) worsening"
    elif prog.escalation_direction == "down":
        status = f"✓ IMPROVEMENT: {prog.change_magnitude} stage(s) improving"
    elif prog.trend == "worsening":
        status = "📈 Worsening trend"
    elif prog.trend == "improving":
        status = "📉 Improving trend"
    
    return status
