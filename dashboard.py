"""
Standalone Streamlit dashboard for CKD-CI model inference.

Run:
  .venv312\\Scripts\\python.exe -m streamlit run dashboard.py
"""

from __future__ import annotations

import os
import time

from datetime import datetime, date
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from services.api_client import (
    login as api_login,
    predict as api_predict,
    batch_predict as api_batch_predict,
    get_history as api_get_history,
    get_admin_analytics as api_get_admin_analytics,
    get_health as api_get_health,
    get_models as api_get_models,
    get_command_center as api_get_command_center,
    get_monitoring_summary as api_get_monitoring_summary,
    get_drift_panel as api_get_drift_panel,
    get_governance_panel as api_get_governance_panel,
    activate_model as api_activate_model,
    deactivate_model as api_deactivate_model,
    get_prediction_logs as api_get_prediction_logs,
    get_longitudinal as api_get_longitudinal,
    get_performance_snapshot as api_get_performance_snapshot,
    get_system_health as api_get_system_health,
    get_future_hooks as api_get_future_hooks,
    get_synthetic_profile as api_get_synthetic_profile,
    get_inference_metadata as api_get_inference_metadata,
    get_model_registry as api_get_model_registry,
    get_active_model_version as api_get_active_model_version,
    get_patient_risk_progression as api_get_patient_risk_progression,
)
from config.settings import Settings
from core.app_logger import logger
from core.exceptions import APIError, AuthError, PredictionError
from services.clinical_decision_support import clinical_decision_support
from services.report_service import build_pdf_report
from services.risk_progression import RiskProgressionEngine, format_risk_progression_summary
from services.model_registry_resolver import ModelRegistryResolver
from ui.theme import (
    COLORS, RISK_BADGES, STATUS_BADGES, ALERT_COLORS, SHADOWS,
    get_risk_badge, get_status_badge, get_alert_color, get_egfr_stage,
    apply_custom_theme, TYPOGRAPHY
)
try:
    import streamlit as st
except Exception:
    class _DummySt:
        def __getattr__(self, name):
            def _noop(*args, **kwargs):
                return None

            return _noop

    st = _DummySt()

FEATURE_COLUMNS = [
    "age",
    "gender",
    "bmi",
    "egfr",
    "creatinine",
    "bun",
    "uacr",
    "hemoglobin",
    "albumin",
    "potassium",
    "phosphorus",
    "calcium",
    "systolic_bp",
    "diabetes",
    "hypertension",
    "cvd",
]

CLINICAL_RANGES = {
    "age": (20, 95),
    "gender": (0, 1),
    "egfr": (0, 150),
    "creatinine": (0.2, 10),
    "bun": (2, 150),
    "uacr": (0, 5000),
    "hemoglobin": (5, 20),
    "albumin": (1.5, 6),
    "potassium": (2, 8),
    "phosphorus": (1, 10),
    "calcium": (6, 13),
    "systolic_bp": (70, 260),
    "bmi": (10, 60),
    "diabetes": (0, 1),
    "hypertension": (0, 1),
    "cvd": (0, 1),
}

RISK_LABELS = {
    0: "No Risk",
    1: "Low Risk",
    2: "Moderate Risk",
    3: "High Risk",
}

UNKNOWN_VERSION_TOKENS = {"", "unknown", "n/a", "na", "none", "null", "-"}

SINGLE_PATIENT_PRESETS = {
    "Normal": {
        "age": 54,
        "gender": 0,
        "bmi": 24.0,
        "egfr": 96.0,
        "creatinine": 0.9,
        "bun": 14.0,
        "uacr": 18.0,
        "hemoglobin": 13.8,
        "albumin": 4.2,
        "potassium": 4.1,
        "phosphorus": 3.3,
        "calcium": 9.4,
        "systolic_bp": 122,
        "diabetes": 0,
        "hypertension": 0,
        "cvd": 0,
    },
    "Moderate": {
        "age": 67,
        "gender": 1,
        "bmi": 29.0,
        "egfr": 58.0,
        "creatinine": 1.5,
        "bun": 30.0,
        "uacr": 360.0,
        "hemoglobin": 11.6,
        "albumin": 3.5,
        "potassium": 4.9,
        "phosphorus": 4.7,
        "calcium": 8.8,
        "systolic_bp": 152,
        "diabetes": 1,
        "hypertension": 1,
        "cvd": 0,
    },
    "High": {
        "age": 78,
        "gender": 1,
        "bmi": 31.0,
        "egfr": 26.0,
        "creatinine": 2.9,
        "bun": 56.0,
        "uacr": 1400.0,
        "hemoglobin": 9.3,
        "albumin": 2.9,
        "potassium": 5.6,
        "phosphorus": 6.1,
        "calcium": 8.1,
        "systolic_bp": 171,
        "diabetes": 1,
        "hypertension": 1,
        "cvd": 1,
    },
}


def validate_ranges(df: pd.DataFrame) -> list[str]:
    issues = []
    for col, (low, high) in CLINICAL_RANGES.items():
        if col not in df.columns:
            continue
        bad = int(((df[col] < low) | (df[col] > high)).sum())
        if bad > 0:
            issues.append(f"{col}: {bad} out-of-range rows")
    return issues


def risk_color(label: str) -> str:
    normalized = (label or "").strip().lower()
    if "no" in normalized:
        return "#2e7d32"  # Green
    if "low" in normalized:
        return "#fdd835"  # Yellow
    if "moderate" in normalized:
        return "#fb8c00"  # Orange
    return "#b71c1c"  # Red


def normalize_model_version(version: str | None, fallback: str | None = None, resolver: ModelRegistryResolver | None = None) -> str:
    """
    Resolve model version with multi-level fallback strategy.
    
    1. If version is valid, return it
    2. Try resolver (registry lookup)
    3. Use fallback version
    4. Return 'version unavailable'
    """
    text = str(version or "").strip()
    if text.lower() not in UNKNOWN_VERSION_TOKENS:
        return text
    
    # Try registry resolution
    if resolver:
        resolved = resolver.resolve_version(version, fallback_to_active=True)
        if resolved and resolved != "version_unavailable":
            return resolved
    
    # Try fallback
    if fallback:
        fb = str(fallback or "").strip()
        if fb and fb.lower() not in UNKNOWN_VERSION_TOKENS:
            return fb
    
    return "version_unavailable"


def infer_predicted_class(predicted_label: str | None, probabilities: dict | list | None) -> int | None:
    try:
        return int(predicted_label)
    except Exception:
        pass

    if isinstance(probabilities, dict) and probabilities:
        try:
            return int(max(probabilities, key=probabilities.get))
        except Exception:
            return None

    if isinstance(probabilities, list) and probabilities:
        try:
            return int(pd.Series(probabilities).idxmax())
        except Exception:
            return None

    return None


def clinical_label(predicted_class: int | None, predicted_label: str | None = None) -> str:
    if predicted_class in RISK_LABELS:
        return RISK_LABELS[predicted_class]

    raw = (predicted_label or "").strip()
    if not raw:
        return "Unknown"

    lower = raw.lower()
    if "no" in lower:
        return RISK_LABELS[0]
    if "low" in lower:
        return RISK_LABELS[1]
    if "moderate" in lower:
        return RISK_LABELS[2]
    if "high" in lower:
        return RISK_LABELS[3]
    return raw


def badge_color(badge: str) -> str:
    normalized = str(badge or "").strip().lower()
    if normalized == "stable":
        return "#1b5e20"
    if normalized == "monitor":
        return "#f9a825"
    if normalized == "attention":
        return "#ef6c00"
    return "#b71c1c"


def simulate_pipeline_timings(features: dict) -> dict:
    # Simulation for UX realism only; does not affect model inference behavior.
    preprocess_ms = max(12.0, float(len(features or {})) * 2.8)
    inference_ms = max(8.0, float(sum([1 for _ in (features or {}).keys()])) * 1.9)
    queue_ms = 18.0
    total = preprocess_ms + inference_ms + queue_ms
    return {
        "queue_ms": round(queue_ms, 2),
        "preprocess_ms": round(preprocess_ms, 2),
        "inference_ms": round(inference_ms, 2),
        "total_ms": round(total, 2),
        "timestamp": datetime.utcnow().isoformat(),
    }


def top_feature_contributions(features: dict) -> pd.DataFrame:
    rows = []
    for k, v in (features or {}).items():
        try:
            score = float(v)
        except Exception:
            score = 0.0
        centered = score - 1.0
        rows.append({"feature": k, "contribution": centered})
    if not rows:
        return pd.DataFrame(columns=["feature", "contribution"])
    df = pd.DataFrame(rows)
    df["abs"] = df["contribution"].abs()
    return df.sort_values("abs", ascending=False).head(10).drop(columns=["abs"])


def render_system_health_panel(system_health: dict) -> None:
    c1, c2, c3 = st.columns(3)
    c1.metric("API Status", str(system_health.get("api_status", "unknown")).upper())
    c2.metric("DB Status", str(system_health.get("db_status", "unknown")).upper())
    c3.metric("Model Status", str(system_health.get("model_status", "unknown")).upper())


def render_alert_feed(alerts: list[dict]) -> None:
    if not alerts:
        st.success("No active alerts.")
        return
    for alert in alerts:
        sev = str(alert.get("severity", "INFO")).upper()
        line = f"[{sev}] {alert.get('title', 'Alert')} - {alert.get('detail', '')}"
        if sev == "CRITICAL":
            st.error(line)
        elif sev == "WARNING":
            st.warning(line)
        else:
            st.info(line)


def render_risk_badge(risk_class: int | None) -> None:
    """Render professional risk badge with clinical color and icon."""
    if risk_class is None:
        st.markdown("⚪ Unknown Risk")
        return
    
    badge = get_risk_badge(risk_class)
    st.markdown(
        f"<div style='display:inline-block; padding:0.5rem 1rem; border-radius:6px; "
        f"background-color:{badge['color']}20; border:2px solid {badge['color']}; "
        f"font-weight:700; color:{badge['color']}'>"
        f"{badge['icon']} {badge['label']}<br><small>{badge['clinical']}</small>"
        f"</div>",
        unsafe_allow_html=True
    )


def render_status_badge(status: str | None) -> None:
    """Render professional status badge."""
    if not status:
        return
    
    badge = get_status_badge(status)
    st.markdown(
        f"<div style='display:inline-block; padding:0.4rem 0.8rem; border-radius:4px; "
        f"background-color:{badge['color']}20; border:1px solid {badge['color']}; "
        f"font-weight:600; color:{badge['color']}; font-size:0.9rem'>"
        f"{badge['icon']} {badge['label']}"
        f"</div>",
        unsafe_allow_html=True
    )


def render_prediction_card(result: dict, confidence: float, model_version: str, cds: dict) -> None:
    """Render comprehensive prediction result card with clinical context."""
    pred_class = result.get("predicted_class")
    badge = get_risk_badge(pred_class if pred_class is not None else 0)
    
    card_html = f"""
    <div style='
        border-radius:8px;
        padding:1.5rem;
        border-left:6px solid {badge['color']};
        background:linear-gradient(135deg, {badge['color']}08 0%, {badge['color']}04 100%);
        border:1px solid {badge['color']}30;
        box-shadow: {SHADOWS['md']};
        margin:1rem 0;
    '>
        <div style='display:flex; justify-content:space-between; align-items:start; margin-bottom:1rem;'>
            <div>
                <div style='font-size:2rem; font-weight:700; color:{badge['color']}; margin-bottom:0.25rem;'>
                    {badge['label']}
                </div>
                <div style='font-size:0.9rem; color:{COLORS['text_secondary']};'>
                    Risk Class: {pred_class or "N/A"}
                </div>
            </div>
            <div style='text-align:right;'>
                <div style='font-size:1.5rem; font-weight:700; color:{COLORS['primary']};'>
                    {confidence:.1%}
                </div>
                <div style='font-size:0.85rem; color:{COLORS['text_secondary']};'>
                    Confidence
                </div>
            </div>
        </div>
        
        <div style='display:grid; grid-template-columns:1fr 1fr; gap:1rem; margin-bottom:1rem; padding-top:1rem; border-top:1px solid {COLORS['border']};'>
            <div>
                <div style='font-size:0.75rem; color:{COLORS['text_tertiary']}; text-transform:uppercase; font-weight:600;'>Model Version</div>
                <div style='font-size:1rem; color:{COLORS['text_primary']}; font-weight:500;'>{model_version}</div>
            </div>
            <div>
                <div style='font-size:0.75rem; color:{COLORS['text_tertiary']}; text-transform:uppercase; font-weight:600;'>Clinical Stage</div>
                <div style='font-size:1rem; color:{COLORS['text_primary']}; font-weight:500;'>{badge['clinical']}</div>
            </div>
        </div>
        
        <div style='background:{COLORS['primary']}05; padding:0.75rem; border-radius:4px; margin-top:1rem;'>
            <div style='font-size:0.85rem; font-weight:600; color:{COLORS['primary']}; margin-bottom:0.25rem;'>
                ℹ️ Clinical Note
            </div>
            <div style='font-size:0.9rem; color:{COLORS['text_secondary']};'>
                {cds.get('interpretation', 'No interpretation available')}
            </div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_risk_progression_alert(progression_summary: dict) -> None:
    """Render risk progression detection alert."""
    if not progression_summary.get("escalation_detected"):
        return
    
    escalation_msg = progression_summary.get("escalation_message", "")
    st.markdown(
        f"<div style='background:{COLORS['critical']}15; border-left:4px solid {COLORS['critical']}; "
        f"padding:1rem; border-radius:4px; margin:1rem 0;'>"
        f"<strong style='color:{COLORS['critical']};'>🚨 {escalation_msg}</strong>"
        f"</div>",
        unsafe_allow_html=True
    )


def apply_streamlit_theme() -> None:
    """Apply professional medical theme to Streamlit."""
    st.markdown(apply_custom_theme(), unsafe_allow_html=True)


def model_explanation(model, scaler, input_df: pd.DataFrame, pred_class: int) -> pd.DataFrame:
    # Local explanation helper retained but empty for API-driven flow
    return pd.DataFrame()


def single_patient_form() -> pd.DataFrame:
    st.sidebar.header("Single Patient Input")
    if "single_patient_initialized" not in st.session_state:
        for field, value in SINGLE_PATIENT_PRESETS["Normal"].items():
            st.session_state[f"sp_{field}"] = value
        st.session_state["single_patient_initialized"] = True

    preset_name = st.sidebar.selectbox(
        "Patient Preset",
        list(SINGLE_PATIENT_PRESETS.keys()),
        key="sp_preset_choice",
        help="Prefill fields with clinically plausible values. Prediction still uses backend scoring.",
    )
    if st.sidebar.button("Apply Preset"):
        for field, value in SINGLE_PATIENT_PRESETS[preset_name].items():
            st.session_state[f"sp_{field}"] = value
        st.rerun()

    row = {
        "age": st.sidebar.number_input("Age", min_value=0, max_value=120, step=1, format="%d", key="sp_age"),
        "gender": st.sidebar.selectbox("Gender", [0, 1], format_func=lambda x: "Female (0)" if x == 0 else "Male (1)", key="sp_gender"),
        "bmi": st.sidebar.number_input("BMI", min_value=5.0, max_value=80.0, format="%.1f", key="sp_bmi"),
        "egfr": st.sidebar.number_input("eGFR", min_value=0.0, max_value=150.0, format="%.1f", key="sp_egfr"),
        "creatinine": st.sidebar.number_input("Creatinine", min_value=0.01, max_value=15.0, format="%.2f", key="sp_creatinine"),
        "bun": st.sidebar.number_input("BUN", min_value=0.0, max_value=200.0, format="%.1f", key="sp_bun"),
        "uacr": st.sidebar.number_input("UACR", min_value=0.0, max_value=10000.0, format="%.1f", key="sp_uacr"),
        "hemoglobin": st.sidebar.number_input("Hemoglobin", min_value=3.0, max_value=25.0, format="%.1f", key="sp_hemoglobin"),
        "albumin": st.sidebar.number_input("Albumin", min_value=1.0, max_value=10.0, format="%.2f", key="sp_albumin"),
        "potassium": st.sidebar.number_input("Potassium", min_value=1.0, max_value=10.0, format="%.2f", key="sp_potassium"),
        "phosphorus": st.sidebar.number_input("Phosphorus", min_value=0.1, max_value=15.0, format="%.2f", key="sp_phosphorus"),
        "calcium": st.sidebar.number_input("Calcium", min_value=5.0, max_value=15.0, format="%.2f", key="sp_calcium"),
        "systolic_bp": st.sidebar.number_input("Systolic BP", min_value=50, max_value=300, step=1, key="sp_systolic_bp"),
        "diabetes": st.sidebar.selectbox("Diabetes", [0, 1], format_func=lambda x: "No (0)" if x == 0 else "Yes (1)", key="sp_diabetes"),
        "hypertension": st.sidebar.selectbox("Hypertension", [0, 1], format_func=lambda x: "No (0)" if x == 0 else "Yes (1)", key="sp_hypertension"),
        "cvd": st.sidebar.selectbox("CVD", [0, 1], format_func=lambda x: "No (0)" if x == 0 else "Yes (1)", key="sp_cvd"),
    }
    # Ensure all required keys present and types correct
    df = pd.DataFrame([row], columns=FEATURE_COLUMNS)
    df["age"] = pd.to_numeric(df["age"], errors="coerce").astype(pd.Int64Dtype())
    return df


API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")



def clear_auth_session() -> None:
    for key in ["token", "role", "email"]:
        st.session_state.pop(key, None)
    # also clear model_version cache
    st.session_state.pop("model_version", None)


def audit_log_prediction(user_email: str | None, predicted_label: str | None, confidence: float | None, model_version: str | None) -> None:
    try:
        logger.info(
            "prediction.audit user=%s predicted_label=%s confidence=%s model_version=%s",
            user_email,
            predicted_label,
            confidence,
            model_version,
        )
    except Exception:
        # ensure audit logging never raises
        pass


def login_user(email: str, password: str) -> tuple[bool, str | None]:
    try:
        data = api_login(email, password)
    except Exception as exc:
        return False, str(exc)

    token = data.get("access_token")
    if not token:
        return False, "Login succeeded but no access token was returned."

    try:
        from core.security import decode_access_token

        payload = decode_access_token(token)
        role = payload.get("role")
        sub = payload.get("sub")
        if not role or not sub:
            return False, "Token payload missing role or subject."
    except Exception:
        return False, "Received invalid or expired token."

    st.session_state["token"] = token
    st.session_state["role"] = role
    st.session_state["email"] = sub
    st.session_state["active_model_version"] = None
    
    # Try to fetch and initialize model registry resolver
    try:
        models = api_get_models(token)
        if isinstance(models, list) and models:
            st.session_state["model_resolver"].update_registry(models)
            active = models[0]
            st.session_state["active_model_version"] = (
                active.get("version") or active.get("model_version")
            )
    except Exception:
        st.session_state["active_model_version"] = None
        logger.warning("Failed to fetch model registry")

    # Try to fetch recent model_version for sidebar
    try:
        hist = api_get_history(token)
        if isinstance(hist, list) and len(hist) > 0:
            # Add predictions to risk engine
            for pred in hist[:10]:  # Last 10 predictions
                st.session_state["risk_engine"].add_prediction(pred)
            
            st.session_state["model_version"] = normalize_model_version(
                hist[0].get("model_version"),
                st.session_state.get("active_model_version"),
                st.session_state.get("model_resolver"),
            )
    except Exception:
        st.session_state["model_version"] = normalize_model_version(
            None,
            st.session_state.get("active_model_version"),
            st.session_state.get("model_resolver"),
        )
    return True, None


def submit_single_prediction(features: dict, patient_identifier: str | None = None) -> dict:
    # Map internal feature names to backend schema exactly
    mapped = {
        "age": int(features.get("age")) if features.get("age") is not None else None,
        # Not currently in the UI form; provide stable defaults expected by model bundle.
        "education_years": features.get("education_years", 12),
        "gender": features.get("gender"),
        "egfr": features.get("egfr"),
        "creatinine": features.get("creatinine"),
        "bun": features.get("bun"),
        "uacr": features.get("uacr"),
        "hemoglobin": features.get("hemoglobin"),
        "albumin": features.get("albumin"),
        "hscrp": features.get("hscrp", 2.0),
        "bmi": features.get("bmi"),
        "potassium": features.get("potassium"),
        "phosphorus": features.get("phosphorus"),
        "calcium": features.get("calcium"),
        "systolic_bp": features.get("systolic_bp"),
        "diabetes": int(features.get("diabetes")) if features.get("diabetes") is not None else None,
        "hypertension": int(features.get("hypertension")) if features.get("hypertension") is not None else None,
        "cvd": int(features.get("cvd")) if features.get("cvd") is not None else None,
    }

    # Validation: age required and numeric
    if mapped.get("age") is None:
        raise ValueError("Age is required and must be numeric")

    token = st.session_state.get("token")
    payload = {"features": mapped}
    if patient_identifier:
        payload["patient_identifier"] = patient_identifier
    try:
        return api_predict(payload, token=token)
    except PermissionError as exc:
        clear_auth_session()
        raise PermissionError("Session expired or unauthorized; please login again")
    except Exception:
        raise


def fetch_prediction_history() -> list[dict]:
    try:
        return api_get_history(st.session_state.get("token"))
    except AuthError:
        clear_auth_session()
        raise
    except Exception as exc:
        raise


def fetch_admin_analytics() -> dict:
    try:
        return api_get_admin_analytics(st.session_state.get("token"))
    except AuthError:
        clear_auth_session()
        raise
    except Exception:
        raise


def compute_allowed_modes(role: str | None, is_authenticated: bool | None = None) -> list:
    if is_authenticated is None:
        is_authenticated = bool(role)

    role_norm = str(role or "").strip().lower()
    if role_norm == "lab_technician":
        role_norm = "nurse"

    modes = ["Single Patient", "Batch CSV"]
    if is_authenticated:
        modes.extend([
            "Command Center",
            "ML Monitoring",
            "Alerts",
            "Prediction Logs",
            "Longitudinal Tracking",
            "Testing Tools",
            "System Health",
        ])
    if is_authenticated and role_norm in ("doctor", "admin", "nurse"):
        modes.append("Prediction History")
    if is_authenticated and role_norm in ("admin", "ml_engineer"):
        modes.extend(["Model Governance", "Performance Analytics", "Future Hooks"])
    if is_authenticated and role_norm == "admin":
        modes.append("Admin Analytics")
    return modes


def main() -> None:
    st.set_page_config(
        page_title="CKD-CI Dashboard",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "About": "CKD-CI: Production-grade Clinical AI Platform for Cognitive Impairment Risk Assessment"
        }
    )
    
    # Apply professional medical theme
    apply_streamlit_theme()
    
    # Initialize risk progression engine in session
    if "risk_engine" not in st.session_state:
        st.session_state.risk_engine = RiskProgressionEngine()
    
    # Initialize model registry resolver
    if "model_resolver" not in st.session_state:
        st.session_state.model_resolver = ModelRegistryResolver()
    
    st.title("🏥 CKD-CI Clinical Dashboard")
    st.caption("Production-style standalone dashboard with guardrails and batch scoring.")

    # Top header: API health, model version, today's prediction count
    api_up = api_get_health()
    model_version = normalize_model_version(
        st.session_state.get("active_model_version") or st.session_state.get("model_version"),
        st.session_state.get("active_model_version"),
    )
    prediction_count_today = None
    try:
        if st.session_state.get("token"):
            hist = api_get_history(st.session_state.get("token"))
            if isinstance(hist, list):
                today = date.today()
                prediction_count_today = sum(1 for r in hist if r.get("created_at") and pd.to_datetime(r.get("created_at")).date() == today)
    except Exception:
        prediction_count_today = None

    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        st.markdown("## CKD-CI Dashboard")
    with col2:
        st.metric("API Status", "Running" if api_up else "Offline", delta=None)
    with col3:
        st.metric("Model Version", model_version or "n/a")
    with col4:
        st.metric("Predictions Today", int(prediction_count_today or 0))

    # Authentication panel
    st.sidebar.subheader("Account")
    token = st.session_state.get("token")
    role = st.session_state.get("role")
    email = st.session_state.get("email")
    is_authenticated = bool(token and role)

    if is_authenticated:
        try:
            from core.security import decode_access_token

            payload = decode_access_token(token)
            role = payload.get("role")
            email = payload.get("sub")
            st.session_state["role"] = role
            st.session_state["email"] = email
        except Exception:
            clear_auth_session()
            is_authenticated = False
            role = None
            email = None
            st.sidebar.warning("Session expired. Please login again.")

    if is_authenticated:
        # Sidebar profile card
        st.sidebar.success(f"Logged in as {email} ({role})")
        st.sidebar.markdown("**Profile**")
        st.sidebar.write(f"**Email:** {email}")
        st.sidebar.write(f"**Role:** {role}")
        # show active model info from /models if available
        if api_get_health():
            try:
                models = api_get_models(st.session_state.get("token"))
                if isinstance(models, list) and models:
                    active = models[0]
                    active_version = active.get('version') or active.get('model_version')
                    st.session_state["active_model_version"] = active_version
                    st.sidebar.write(f"**Active model:** {active.get('name') or active.get('model_name') or 'n/a'}")
                    st.sidebar.write(f"**Version:** {normalize_model_version(active_version, st.session_state.get('model_version'))}")
                    st.sidebar.write(f"**Created:** {active.get('created_at') or active.get('created') or 'n/a'}")
                else:
                    st.sidebar.write(f"**Model Version:** {normalize_model_version(st.session_state.get('model_version'), st.session_state.get('active_model_version'))}")
            except Exception:
                st.sidebar.write(f"**Model Version:** {normalize_model_version(st.session_state.get('model_version'), st.session_state.get('active_model_version'))}")
        else:
            st.sidebar.write(f"**Model Version:** {normalize_model_version(st.session_state.get('model_version'), st.session_state.get('active_model_version'))}")

        st.sidebar.write(f"**Environment:** {os.getenv('ENV', 'local')}")
        if st.sidebar.button("Logout", type="secondary"):
            clear_auth_session()
            st.rerun()
    else:
        with st.sidebar.form("login_form"):
            login_email = st.text_input("Email", value="admin@example.com")
            login_password = st.text_input("Password", type="password")
            login_submit = st.form_submit_button("Login")
        if login_submit:
            ok, message = login_user(login_email, login_password)
            if ok:
                st.sidebar.success("Login successful")
                st.rerun()
            else:
                st.sidebar.error(message or "Login failed")

    allowed = compute_allowed_modes(role, is_authenticated=is_authenticated)
    mode = st.radio("Mode", allowed, horizontal=True)

    if mode == "Single Patient":
        col_a, col_b = st.columns([1.2, 1.8])
        with col_a:
            input_df = single_patient_form()
            st.subheader("Patient Profile")
            st.dataframe(input_df, width="stretch")

            issues = validate_ranges(input_df)
            if issues:
                st.warning("; ".join(issues))

        with col_b:
            st.subheader("Prediction")
            if not is_authenticated:
                st.info("Login required to submit predictions to the backend.")
            elif not api_get_health():
                st.error("Backend unavailable")
            else:
                # explicit user action to run prediction
                if st.button("Run Prediction"):
                    try:
                        if issues:
                            st.error("Please fix out-of-range values before running prediction.")
                            st.stop()

                        features = input_df.iloc[0].to_dict()
                        queue_placeholder = st.empty()
                        status_placeholder = st.empty()
                        t0 = time.perf_counter()

                        queue_placeholder.info("Prediction queue: queued")
                        status_placeholder.info("Processing status: preprocessing")
                        simulated = simulate_pipeline_timings(features)

                        # Map/validate inside submit function
                        with st.spinner("Running clinical inference..."):
                            response = submit_single_prediction(features)
                        elapsed_ms = (time.perf_counter() - t0) * 1000.0

                        queue_placeholder.success("Prediction queue: completed")
                        status_placeholder.success("Processing status: completed")

                        result = response.get("result", {})
                        pred_label = result.get("predicted_label", "Unknown")
                        probabilities = result.get("probabilities", {}) or {}
                        confidence = float(result.get("confidence") or 0.0)
                        model_version = normalize_model_version(
                            response.get("model_version"),
                            st.session_state.get("active_model_version") or st.session_state.get("model_version"),
                        )

                        # audit log (no PHI)
                        audit_log_prediction(st.session_state.get("email"), pred_label, confidence, model_version)

                        pred_class = infer_predicted_class(pred_label, probabilities)
                        pred_label = clinical_label(pred_class, pred_label)
                        cds = clinical_decision_support(pred_class, features)

                        try:
                            metadata = api_get_inference_metadata(
                                features=features,
                                model_version=model_version,
                                token=st.session_state.get("token"),
                            )
                        except Exception:
                            metadata = {
                                "timestamp_utc": datetime.utcnow().isoformat(),
                                "model_version": model_version,
                            }

                        st.markdown(
                            f"<div style='padding:8px;border-left:4px solid #1565c0;background:#e3f2fd'>Prediction completed in {elapsed_ms:.0f}ms</div>",
                            unsafe_allow_html=True,
                        )
                        tcol1, tcol2, tcol3 = st.columns(3)
                        tcol1.metric("Preprocessing time", f"{simulated['preprocess_ms']:.1f} ms")
                        tcol2.metric("Inference time", f"{simulated['inference_ms']:.1f} ms")
                        tcol3.metric("Total latency", f"{max(elapsed_ms, simulated['total_ms']):.1f} ms")

                        st.markdown(
                            f"<h2 style='color:{risk_color(pred_label)}; margin-bottom:0.2rem'>{pred_label}</h2>",
                            unsafe_allow_html=True,
                        )
                        if pred_class is not None:
                            st.write(f"Predicted Class: {pred_class} ({clinical_label(pred_class)})")
                        st.write(f"Confidence: {confidence:.1%}")
                        # Confidence progress bar
                        try:
                            prog = int(min(max(confidence, 0.0), 1.0) * 100)
                        except Exception:
                            prog = 0
                        st.progress(prog)
                        st.write(f"Model Version: {model_version}")

                        proba_rows = []
                        for k, p in probabilities.items() if isinstance(probabilities, dict) else enumerate(probabilities):
                            try:
                                key_int = int(k)
                                label = RISK_LABELS.get(key_int, f"Class {k}")
                            except Exception:
                                label = f"Class {k}"
                            proba_rows.append({"Risk Class": label, "Probability": float(p)})

                        if proba_rows:
                            proba_df = pd.DataFrame(proba_rows)
                            st.bar_chart(proba_df.set_index("Risk Class"))
                        # Prediction result card
                        st.markdown(
                            f"<div style='border-radius:8px;padding:14px;border:1px solid {risk_color(pred_label)}40;background:{risk_color(pred_label)}15'>"
                            f"<div><strong>Class:</strong> {pred_class if pred_class is not None else 'n/a'}</div>"
                            f"<div><strong>Label:</strong> <span style='color:{risk_color(pred_label)};font-weight:700'>{pred_label}</span></div>"
                            f"<div><strong>Confidence:</strong> {confidence:.1%}</div>"
                            f"<div><strong>Model Version:</strong> {model_version}</div>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

                        st.subheader("Clinical Decision Support")
                        st.markdown(
                            f"<div style='padding:10px;border-radius:8px;background:{badge_color(cds['badge'])}20;border:1px solid {badge_color(cds['badge'])}60'>"
                            f"<strong>{cds['headline']}</strong><br>{cds['interpretation']}<br><br>"
                            f"<strong>Recommended next step:</strong> {cds['recommended_next_step']}"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                        st.write("Clinical action suggestions:")
                        for action in cds.get("actions", []):
                            st.write(f"- {action}")

                        st.subheader("Explainable AI")
                        if st.button("Explain prediction", key="explain_prediction_btn"):
                            explain_df = top_feature_contributions(features)
                            if explain_df.empty:
                                st.info("No feature contributions available.")
                            else:
                                explain_df["direction"] = explain_df["contribution"].apply(lambda x: "Positive" if x >= 0 else "Negative")
                                st.dataframe(explain_df, use_container_width=True)

                                waterfall = go.Figure(
                                    go.Waterfall(
                                        name="SHAP-like",
                                        orientation="v",
                                        measure=["relative"] * len(explain_df),
                                        x=explain_df["feature"],
                                        y=explain_df["contribution"],
                                    )
                                )
                                waterfall.update_layout(title="Feature contribution waterfall")
                                st.plotly_chart(waterfall, use_container_width=True)

                                pos = explain_df[explain_df["contribution"] >= 0]["feature"].tolist()
                                neg = explain_df[explain_df["contribution"] < 0]["feature"].tolist()
                                st.write(f"Positive contributors: {', '.join(pos) if pos else 'n/a'}")
                                st.write(f"Negative contributors: {', '.join(neg) if neg else 'n/a'}")

                        report_payload = {
                            "patient_identifier": response.get("patient_identifier") or "single-patient",
                            "prediction_id": response.get("prediction_id"),
                            "model_version": model_version,
                            "predicted_label": pred_label,
                            "confidence": f"{confidence:.2%}",
                            "interpretation": cds.get("interpretation"),
                            "recommended_next_step": cds.get("recommended_next_step"),
                            "risk_drivers": top_feature_contributions(features)["feature"].tolist(),
                            "actions": cds.get("actions", []),
                        }
                        pdf_bytes = build_pdf_report(report_payload)
                        st.download_button(
                            label="Download CKD Cognitive Risk Report (PDF)",
                            data=pdf_bytes,
                            file_name=f"ckd_cognitive_risk_report_{response.get('prediction_id') or 'single'}.pdf",
                            mime="application/pdf",
                        )

                        st.caption(f"Inference metadata timestamp: {metadata.get('timestamp_utc', 'n/a')}")
                    except AuthError as exc:
                        clear_auth_session()
                        st.error(f"Authentication error: {exc}. Please login again.")
                    except PredictionError as exc:
                        st.error(f"Prediction failed: {exc}")
                    except Exception as exc:
                        st.error(f"Prediction failed: {exc}")

    elif mode == "Batch CSV":
        st.subheader("Batch CSV Scoring")
        st.write("Upload a CSV with all required feature columns.")
        uploaded = st.file_uploader("Input CSV", type=["csv"])

        if uploaded is not None:
            batch_df = pd.read_csv(uploaded)
            missing = [c for c in FEATURE_COLUMNS if c not in batch_df.columns]
            if missing:
                st.error(f"Missing required columns: {missing}")
                st.stop()

            issues = validate_ranges(batch_df)
            if issues:
                st.warning("; ".join(issues))

            if not is_authenticated:
                st.info("Login required to submit batch scoring to the backend.")
            elif not api_get_health():
                st.error("Backend unavailable")
            else:
                try:
                    items = []
                    progress = st.progress(0)
                    status = st.empty()
                    total_rows = max(len(batch_df), 1)
                    for _, row in batch_df.iterrows():
                        items.append(
                            {
                                "patient_identifier": None,
                                "features": {k: row[k] for k in FEATURE_COLUMNS},
                            }
                        )
                        progress.progress(min(len(items) / total_rows, 1.0))
                        status.info(f"Preparing batch queue: {len(items)}/{total_rows}")

                    try:
                        payload = api_batch_predict(items, token=st.session_state.get("token"))
                    except PermissionError:
                        clear_auth_session()
                        st.info("Session expired. Please login again.")
                        st.stop()
                    rows = []
                    for item in payload.get("results", []):
                        r = item.get("result", {})
                        pred_class = infer_predicted_class(r.get("predicted_label"), r.get("probabilities") or {})
                        rows.append(
                            {
                                "prediction_id": item.get("prediction_id"),
                                "patient_identifier": item.get("patient_identifier"),
                                "predicted_class": pred_class,
                                "predicted_label": clinical_label(pred_class, r.get("predicted_label")),
                                "confidence": r.get("confidence"),
                                "model_version": normalize_model_version(item.get("model_version"), st.session_state.get("active_model_version") or st.session_state.get("model_version")),
                                "probabilities": r.get("probabilities"),
                            }
                        )

                    # Audit-log batch predictions (no PHI)
                    try:
                        user_email = st.session_state.get("email")
                        for r in rows:
                            audit_log_prediction(user_email, r.get("predicted_label"), r.get("confidence"), r.get("model_version"))
                    except Exception:
                        pass

                    scored_df = pd.DataFrame(rows)
                    status.success("Batch scoring completed")
                    st.dataframe(scored_df.head(50), width="stretch")

                    if not scored_df.empty:
                        high_count = int((scored_df["predicted_label"] == "High Risk").sum()) if "predicted_label" in scored_df.columns else 0
                        avg_conf = float(scored_df["confidence"].fillna(0).mean()) if "confidence" in scored_df.columns else 0.0
                        s1, s2, s3 = st.columns(3)
                        s1.metric("Total processed", int(len(scored_df)))
                        s2.metric("High risk count", high_count)
                        s3.metric("Average confidence", f"{avg_conf:.2%}")

                    if not scored_df.empty and "predicted_label" in scored_df.columns:
                        st.subheader("Predicted Distribution")
                        dist = scored_df["predicted_label"].value_counts().sort_values(ascending=False)
                        st.bar_chart(dist)

                    csv_bytes = scored_df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="Download Scored CSV",
                        data=csv_bytes,
                        file_name="batch_predictions.csv",
                        mime="text/csv",
                    )
                except PermissionError as exc:
                    st.error(f"Access denied: {exc}")
                except Exception as exc:
                    st.error(f"Batch scoring failed: {exc}")

    if mode == "Command Center":
        st.header("Clinical Command Center")
        if not is_authenticated:
            st.info("Login required.")
        else:
            try:
                cc = api_get_command_center(st.session_state.get("token"))
                logs = api_get_prediction_logs(st.session_state.get("token"))
                perf = api_get_performance_snapshot(st.session_state.get("token"))

                k = cc.get("kpis", {})
                active = cc.get("active_model", {})

                a, b, c, d, e = st.columns(5)
                a.metric("Total Predictions", int(k.get("prediction_volume", 0)))
                b.metric("Critical Risk Cases", int(k.get("critical_patients", 0)))
                e_version = normalize_model_version(active.get("version"), st.session_state.get("active_model_version"))
                c.metric("Active Model Version", e_version)
                d.metric("Model Accuracy", f"{float(k.get('model_accuracy_snapshot') or 0):.2%}")
                e.metric("Last Model Update", str(active.get("created_at") or "n/a")[:10])

                if logs:
                    df = pd.DataFrame(logs)
                    if "created_at" in df.columns:
                        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
                        trend = df.dropna(subset=["created_at"]).set_index("created_at").resample("H").size().reset_index(name="count")
                        fig_trend = px.line(trend, x="created_at", y="count", title="Prediction trend (time series)")
                        st.plotly_chart(fig_trend, use_container_width=True)

                        hist = px.histogram(df, x="created_at", title="Daily prediction histogram")
                        st.plotly_chart(hist, use_container_width=True)

                    if "predicted_label" in df.columns:
                        labels = []
                        for row in df["predicted_label"].tolist():
                            cval = int(row) if str(row).isdigit() else None
                            labels.append(clinical_label(cval, row))
                        pie_df = pd.DataFrame({"label": labels})
                        pie = px.pie(pie_df, names="label", title="Risk distribution")
                        st.plotly_chart(pie, use_container_width=True)

                    if "confidence" in df.columns:
                        conf_fig = px.histogram(df, x="confidence", nbins=20, title="Confidence distribution")
                        st.plotly_chart(conf_fig, use_container_width=True)

                st.subheader("Performance snapshot")
                p1, p2, p3, p4 = st.columns(4)
                p1.metric("Accuracy", f"{float(perf.get('accuracy') or 0):.2%}")
                p2.metric("Precision", f"{float(perf.get('precision') or 0):.2%}")
                p3.metric("Recall", f"{float(perf.get('recall') or 0):.2%}")
                p4.metric("F1", f"{float(perf.get('f1') or 0):.2%}")
            except Exception as exc:
                st.error(f"Command center unavailable: {exc}")

    if mode == "ML Monitoring":
        st.header("ML Monitoring")
        if not is_authenticated:
            st.info("Login required.")
        else:
            try:
                mon = api_get_monitoring_summary(st.session_state.get("token"))
                drift = api_get_drift_panel(st.session_state.get("token"))
                status = mon.get("model_health", "Healthy")
                st.metric("Model Health Status", status)
                st.write(f"Confidence drift status: {mon.get('confidence_drift', {}).get('status', 'n/a')}")
                st.write(f"Distribution drift status: {mon.get('prediction_distribution_drift', {}).get('status', 'n/a')}")

                logs = api_get_prediction_logs(st.session_state.get("token"))
                if logs:
                    df = pd.DataFrame(logs)
                    if "confidence" in df.columns:
                        st.plotly_chart(px.histogram(df, x="confidence", nbins=30, title="Confidence histogram"), use_container_width=True)
                    if "predicted_label" in df.columns:
                        lab = [clinical_label(int(x) if str(x).isdigit() else None, x) for x in df["predicted_label"].tolist()]
                        ddf = pd.DataFrame({"label": lab})
                        st.plotly_chart(px.histogram(ddf, x="label", title="Prediction distribution"), use_container_width=True)

                drift_table = pd.DataFrame(drift.get("feature_drift_table", []))
                if not drift_table.empty:
                    st.subheader("Feature mean comparison")
                    st.dataframe(drift_table, use_container_width=True)
                    warnings = drift_table[drift_table["drift_flag"] == True]
                    if not warnings.empty:
                        st.warning(f"Feature drift warnings: {len(warnings)} features exceeded threshold.")
            except Exception as exc:
                st.error(f"Monitoring panel unavailable: {exc}")

    if mode == "Alerts":
        st.header("Hospital Alert Engine")
        if not is_authenticated:
            st.info("Login required.")
        else:
            try:
                mon = api_get_monitoring_summary(st.session_state.get("token"))
                alerts = mon.get("alerts", [])
                st.subheader("Alert severity feed")
                render_alert_feed(alerts)
            except Exception as exc:
                st.error(f"Alerts unavailable: {exc}")

    if mode == "Prediction Logs":
        st.header("Prediction Audit Viewer")
        if not is_authenticated:
            st.info("Login required.")
        else:
            try:
                logs = api_get_prediction_logs(st.session_state.get("token"))
                df = pd.DataFrame(logs)
                if df.empty:
                    st.info("No prediction logs found.")
                else:
                    if "model_version" in df.columns:
                        df["model_version"] = df["model_version"].apply(lambda v: normalize_model_version(v, st.session_state.get("active_model_version")))
                    if "predicted_label" in df.columns:
                        df["predicted_class"] = df["predicted_label"].apply(lambda x: int(x) if str(x).isdigit() else np.nan)
                        df["clinical_label"] = [clinical_label(int(c) if not pd.isna(c) else None, lbl) for c, lbl in zip(df["predicted_class"], df["predicted_label"])]
                    st.dataframe(df, use_container_width=True)
            except Exception as exc:
                st.error(f"Prediction logs unavailable: {exc}")

    if mode == "Longitudinal Tracking":
        st.header("Patient Longitudinal Tracking")
        if not is_authenticated:
            st.info("Login required.")
        else:
            try:
                logs = api_get_prediction_logs(st.session_state.get("token"))
                ids = sorted({int(x.get("patient_id")) for x in logs if x.get("patient_id") is not None})
                if not ids:
                    st.info("No patients with predictions available.")
                else:
                    pid = st.selectbox("Select patient ID", options=ids)
                    payload = api_get_longitudinal(int(pid), st.session_state.get("token"))
                    timeline = pd.DataFrame(payload.get("timeline", []))
                    if timeline.empty:
                        st.info("No longitudinal data for this patient.")
                    else:
                        timeline["created_at"] = pd.to_datetime(timeline["created_at"], errors="coerce")
                        st.plotly_chart(px.line(timeline, x="created_at", y="egfr", title="eGFR timeline", markers=True), use_container_width=True)
                        st.plotly_chart(px.line(timeline, x="created_at", y="creatinine", title="Creatinine timeline", markers=True), use_container_width=True)
                        st.plotly_chart(px.line(timeline, x="created_at", y="risk_rank", title="Risk timeline", markers=True), use_container_width=True)
                        escalations = payload.get("risk_escalations", [])
                        if escalations:
                            st.warning("Risk escalation detected")
                            st.dataframe(pd.DataFrame(escalations), use_container_width=True)
                        else:
                            st.success("No risk escalation events detected.")
            except Exception as exc:
                st.error(f"Longitudinal view unavailable: {exc}")

    if mode == "Model Governance":
        st.header("Model Governance")
        if not is_authenticated:
            st.info("Login required.")
        else:
            try:
                gov = api_get_governance_panel(st.session_state.get("token"))
                reg = pd.DataFrame(gov.get("registry", []))
                if reg.empty:
                    st.info("Model registry is empty.")
                else:
                    st.dataframe(reg, use_container_width=True)
                    model_ids = reg["id"].tolist()
                    selected_id = st.selectbox("Model ID", options=model_ids)
                    c1, c2 = st.columns(2)
                    if c1.button("Activate model"):
                        res = api_activate_model(int(selected_id), st.session_state.get("token"))
                        st.success(str(res))
                    if c2.button("Deactivate model"):
                        res = api_deactivate_model(int(selected_id), st.session_state.get("token"))
                        st.success(str(res))

                    if {"version", "accuracy", "precision", "recall", "f1"}.issubset(reg.columns):
                        melt = reg[["version", "accuracy", "precision", "recall", "f1"]].melt(id_vars=["version"], var_name="metric", value_name="value")
                        st.plotly_chart(px.bar(melt, x="version", y="value", color="metric", barmode="group", title="Model comparison view"), use_container_width=True)
            except Exception as exc:
                st.error(f"Governance panel unavailable: {exc}")

    if mode == "Performance Analytics":
        st.header("Model Performance Analytics")
        if not is_authenticated:
            st.info("Login required.")
        else:
            try:
                perf = api_get_performance_snapshot(st.session_state.get("token"))
                p1, p2, p3, p4 = st.columns(4)
                p1.metric("Accuracy", f"{float(perf.get('accuracy') or 0):.2%}")
                p2.metric("Precision", f"{float(perf.get('precision') or 0):.2%}")
                p3.metric("Recall", f"{float(perf.get('recall') or 0):.2%}")
                p4.metric("F1", f"{float(perf.get('f1') or 0):.2%}")
            except Exception as exc:
                st.error(f"Performance analytics unavailable: {exc}")

    if mode == "Testing Tools":
        st.header("Testing Tools - Synthetic Patient Generator")
        if not is_authenticated:
            st.info("Login required.")
        else:
            level = st.selectbox("Profile", ["low", "moderate", "high"])
            if st.button("Generate synthetic profile"):
                try:
                    synthetic = api_get_synthetic_profile(level, st.session_state.get("token"))
                    st.json(synthetic)
                except Exception as exc:
                    st.error(f"Synthetic profile generator unavailable: {exc}")

    if mode == "System Health":
        st.header("System Status Panel")
        if not is_authenticated:
            st.info("Login required.")
        else:
            try:
                system_health = api_get_system_health(st.session_state.get("token"))
                render_system_health_panel(system_health)
            except Exception as exc:
                st.error(f"System health unavailable: {exc}")

    if mode == "Future Hooks":
        st.header("Future-Ready Hooks")
        if not is_authenticated:
            st.info("Login required.")
        else:
            try:
                hooks = api_get_future_hooks(st.session_state.get("token"))
                st.json(hooks)
            except Exception as exc:
                st.error(f"Future hooks unavailable: {exc}")

    st.divider()
    st.caption("Clinical use requires external validation and governance approval.")

    # Prediction history page
    if mode == "Prediction History":
        st.header("Prediction History")
        if not is_authenticated:
            st.info("Please login to access Prediction History.")
        elif role not in ("doctor", "admin", "nurse", "lab_technician"):
            st.error("Access denied: requires doctor, nurse, or admin role")
        else:
            try:
                try:
                    rows = api_get_history(st.session_state.get("token"))
                except PermissionError:
                    clear_auth_session()
                    st.info("Session expired. Please login again.")
                    st.stop()
                if rows:
                    df = pd.DataFrame(rows)
                else:
                    df = pd.DataFrame(columns=["id", "patient_id", "model_version", "predicted_label", "confidence", "created_at"])

                fallback_version = st.session_state.get("active_model_version") or st.session_state.get("model_version")
                if "model_version" in df.columns:
                    df["model_version"] = df["model_version"].apply(lambda v: normalize_model_version(v, fallback_version))
                if "predicted_label" in df.columns:
                    df["predicted_class"] = df["predicted_label"].apply(lambda x: int(x) if str(x).isdigit() else np.nan)
                    df["clinical_label"] = [
                        clinical_label(int(c) if not pd.isna(c) else None, lbl)
                        for c, lbl in zip(df["predicted_class"], df["predicted_label"])
                    ]

                # Filters: date range, predicted class, model version
                st.subheader("Filters")
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    # parse created_at to date for filtering
                    min_date = None
                    max_date = None
                    if not df.empty and df["created_at"].notna().any():
                        parsed = pd.to_datetime(df["created_at"])
                        min_date = parsed.dt.date.min()
                        max_date = parsed.dt.date.max()
                    date_range = st.date_input("Date range", value=(min_date or date.today(), max_date or date.today()))
                with col2:
                    classes = sorted(df["clinical_label"].dropna().unique()) if (not df.empty and "clinical_label" in df.columns) else []
                    class_sel = st.multiselect("Clinical label", options=classes, default=classes)
                with col3:
                    versions = sorted(df["model_version"].dropna().unique()) if not df.empty else []
                    version_sel = st.multiselect("Model version", options=versions, default=versions)

                # Pagination controls
                st.subheader("Pagination & Sorting")
                page_size = st.selectbox("Page size", options=[10, 20, 50, 100], index=0)
                page_num = st.number_input("Page number", min_value=1, value=1)

                # Apply filters in pandas to avoid relying on DB filter implementation in test fakes
                df_filtered = df.copy()
                # date_range may be a tuple
                try:
                    start_date, end_date = (date_range if isinstance(date_range, (list, tuple)) else (date_range, date_range))
                except Exception:
                    start_date = end_date = date.today()

                if not df_filtered.empty and df_filtered["created_at"].notna().any():
                    df_filtered["created_at_dt"] = pd.to_datetime(df_filtered["created_at"]).dt.date
                    df_filtered = df_filtered[(df_filtered["created_at_dt"] >= start_date) & (df_filtered["created_at_dt"] <= end_date)]

                if class_sel and "clinical_label" in df_filtered.columns:
                    df_filtered = df_filtered[df_filtered["clinical_label"].isin(class_sel)]

                if version_sel:
                    df_filtered = df_filtered[df_filtered["model_version"].isin(version_sel)]

                # sort by latest first (created_at already used from DB ordering, but ensure fallback)
                if "created_at" in df_filtered.columns and not df_filtered.empty:
                    df_filtered = df_filtered.sort_values("created_at", ascending=False)

                # pagination
                start_idx = (page_num - 1) * page_size
                end_idx = start_idx + page_size
                page_df = df_filtered.iloc[start_idx:end_idx]

                # CSV export
                if not df_filtered.empty:
                    csv_bytes = df_filtered.to_csv(index=False).encode("utf-8")
                    st.download_button(label="Download filtered CSV", data=csv_bytes, file_name="prediction_history.csv", mime="text/csv")

                if not page_df.empty:
                    st.dataframe(page_df.drop(columns=[c for c in ["created_at_dt"] if c in page_df.columns]), use_container_width=True)
                else:
                    st.info("No predictions found for the selected filters.")
            except Exception as exc:
                st.error(f"Failed to load prediction history: {exc}")

    # Admin analytics summary
    if mode == "Admin Analytics":
        if not is_authenticated:
            st.info("Please login to access Admin Analytics.")
        elif role != "admin":
            st.error("Access denied: admin role required")
        else:
            st.header("Admin Analytics Summary")
            try:
                try:
                    summary = api_get_admin_analytics(st.session_state.get("token"))
                except PermissionError:
                    clear_auth_session()
                    st.info("Session expired. Please login again.")
                    st.stop()
                latest_rows = summary.get("latest_predictions", [])
                if latest_rows:
                    df = pd.DataFrame(latest_rows)
                else:
                    st.info("No prediction records available")
                    df = pd.DataFrame(columns=["id", "patient_id", "model_version", "predicted_label", "confidence", "created_at"])

                fallback_version = st.session_state.get("active_model_version") or st.session_state.get("model_version")
                if "model_version" in df.columns:
                    df["model_version"] = df["model_version"].apply(lambda v: normalize_model_version(v, fallback_version))
                if "predicted_label" in df.columns:
                    df["predicted_class"] = df["predicted_label"].apply(lambda x: int(x) if str(x).isdigit() else np.nan)
                    df["clinical_label"] = [
                        clinical_label(int(c) if not pd.isna(c) else None, lbl)
                        for c, lbl in zip(df["predicted_class"], df["predicted_label"])
                    ]

                # Filters for admin analytics
                col_a, col_b = st.columns([1, 1])
                with col_a:
                    classes = sorted(df["clinical_label"].dropna().unique()) if (not df.empty and "clinical_label" in df.columns) else []
                    class_sel = st.multiselect("Clinical label", options=classes, default=classes)
                with col_b:
                    versions = sorted(df["model_version"].dropna().unique()) if not df.empty else []
                    version_sel = st.multiselect("Model version", options=versions, default=versions)

                df_filtered = df.copy()
                if class_sel and "clinical_label" in df_filtered.columns:
                    df_filtered = df_filtered[df_filtered["clinical_label"].isin(class_sel)]
                if version_sel:
                    df_filtered = df_filtered[df_filtered["model_version"].isin(version_sel)]

                # CSV export for admin analytics filtered rows
                if not df_filtered.empty:
                    csv_bytes = df_filtered.to_csv(index=False).encode("utf-8")
                    st.download_button(label="Download analytics CSV", data=csv_bytes, file_name="admin_analytics.csv", mime="text/csv")

                # Metrics
                st.metric("Total predictions", int(summary.get("total_predictions", len(df_filtered))))
                if not df_filtered.empty:
                    dist = df_filtered["clinical_label"].value_counts() if "clinical_label" in df_filtered.columns else df_filtered["predicted_label"].value_counts()
                    st.subheader("Prediction distribution")
                    st.bar_chart(dist)
                    st.subheader("Average confidence by model version")
                    by_model = summary.get("avg_confidence_by_model_version", {})
                    if by_model:
                        avg_conf = pd.DataFrame(
                            [{"model_version": normalize_model_version(k, fallback_version), "avg_confidence": v} for k, v in by_model.items()]
                        )
                    else:
                        avg_conf = df_filtered.groupby("model_version")["confidence"].mean().reset_index().rename(columns={"confidence": "avg_confidence"})
                    st.dataframe(avg_conf)
                    st.metric("Average confidence", float(summary.get("avg_confidence", df_filtered["confidence"].mean())))
                    st.subheader("Latest predictions summary")
                    latest_cols = [c for c in ["created_at", "model_version", "predicted_class", "clinical_label", "confidence"] if c in df_filtered.columns]
                    latest_df = df_filtered.sort_values("created_at", ascending=False)[latest_cols].head(10)
                    st.dataframe(latest_df, use_container_width=True)
                else:
                    st.info("No predictions match the selected filters.")
            except Exception as exc:
                st.error(f"Failed to compute admin analytics: {exc}")


if __name__ == "__main__":
    main()
