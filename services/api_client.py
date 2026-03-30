import time
from typing import Any, Dict, List

import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from core.app_logger import logger
from core.exceptions import APIError, AuthError, PredictionError

# Config via env with sensible defaults (allows existing config.settings to remain authoritative)
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))


def _session_with_retries(retries: int = 3, backoff: float = 0.3) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def _extract_error(resp: requests.Response) -> str:
    try:
        j = resp.json()
        if isinstance(j, dict):
            return str(j.get("detail") or j.get("message") or j)
        return str(j)
    except Exception:
        return resp.text or f"HTTP {resp.status_code}"


def login(email: str, password: str, timeout: int | None = None) -> Dict[str, Any]:
    timeout = timeout or REQUEST_TIMEOUT
    url = f"{API_URL.rstrip('/')}/auth/login"
    s = _session_with_retries()
    try:
        resp = s.post(url, json={"email": email, "password": password}, timeout=timeout)
    except requests.RequestException as exc:
        logger.error("Login request failed: %s", exc)
        raise AuthError(str(exc))
    if resp.status_code != 200:
        msg = _extract_error(resp)
        logger.error("Login failed: %s", msg)
        raise AuthError(msg)
    return resp.json()


def predict(payload: Dict[str, Any], token: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    timeout = timeout or REQUEST_TIMEOUT
    url = f"{API_URL.rstrip('/')}/predictions/predict"
    s = _session_with_retries()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = s.post(url, json=payload, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        logger.error("Predict request failed: %s", exc)
        raise PredictionError(str(exc))
    if resp.status_code in (401, 403):
        msg = _extract_error(resp)
        logger.error("Predict unauthorized: %s", msg)
        raise AuthError(msg)
    if resp.status_code != 200:
        msg = _extract_error(resp)
        logger.error("Predict failed: %s", msg)
        raise PredictionError(msg)
    return resp.json()


def batch_predict(items: List[Dict[str, Any]], token: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    timeout = timeout or REQUEST_TIMEOUT
    url = f"{API_URL.rstrip('/')}/predictions/batch"
    s = _session_with_retries()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = s.post(url, json={"items": items}, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        logger.error("Batch predict failed: %s", exc)
        raise PredictionError(str(exc))
    if resp.status_code in (401, 403):
        msg = _extract_error(resp)
        logger.error("Batch predict unauthorized: %s", msg)
        raise AuthError(msg)
    if resp.status_code != 200:
        msg = _extract_error(resp)
        logger.error("Batch predict failed: %s", msg)
        raise PredictionError(msg)
    return resp.json()


def get_history(token: str | None = None, timeout: int | None = None) -> List[Dict[str, Any]]:
    timeout = timeout or REQUEST_TIMEOUT
    url = f"{API_URL.rstrip('/')}/predictions/history"
    s = _session_with_retries()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = s.get(url, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        logger.error("Get history failed: %s", exc)
        raise APIError(str(exc))
    if resp.status_code in (401, 403):
        msg = _extract_error(resp)
        logger.error("Get history unauthorized: %s", msg)
        raise AuthError(msg)
    if resp.status_code != 200:
        msg = _extract_error(resp)
        logger.error("Get history failed: %s", msg)
        raise APIError(msg)
    return resp.json()


def get_admin_analytics(token: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    timeout = timeout or REQUEST_TIMEOUT
    url = f"{API_URL.rstrip('/')}/admin/analytics"
    s = _session_with_retries()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = s.get(url, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        logger.error("Get admin analytics failed: %s", exc)
        raise APIError(str(exc))
    if resp.status_code in (401, 403):
        msg = _extract_error(resp)
        logger.error("Get admin unauthorized: %s", msg)
        raise AuthError(msg)
    if resp.status_code != 200:
        msg = _extract_error(resp)
        logger.error("Get admin analytics failed: %s", msg)
        raise APIError(msg)
    return resp.json()


def get_health(timeout: int | None = None) -> bool:
    timeout = timeout or REQUEST_TIMEOUT
    url = f"{API_URL.rstrip('/')}/health"
    s = _session_with_retries()
    try:
        resp = s.get(url, timeout=timeout)
        return resp.status_code == 200
    except Exception as exc:
        logger.warning("Health check failed: %s", exc)
        return False


def get_models(token: str | None = None, timeout: int | None = None) -> List[Dict[str, Any]]:
    timeout = timeout or REQUEST_TIMEOUT
    url = f"{API_URL.rstrip('/')}/models"
    s = _session_with_retries()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = s.get(url, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        logger.error("Get models failed: %s", exc)
        raise APIError(str(exc))
    if resp.status_code in (401, 403):
        msg = _extract_error(resp)
        logger.error("Get models failed: %s", msg)
        raise AuthError(msg)
    if resp.status_code != 200:
        msg = _extract_error(resp)
        logger.error("Get models failed: %s", msg)
        raise APIError(msg)
    return resp.json()


def _authed_get(path: str, token: str | None, timeout: int | None = None) -> Any:
    timeout = timeout or REQUEST_TIMEOUT
    url = f"{API_URL.rstrip('/')}{path}"
    s = _session_with_retries()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = s.get(url, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        raise APIError(str(exc))
    if resp.status_code in (401, 403):
        raise AuthError(_extract_error(resp))
    if resp.status_code != 200:
        raise APIError(_extract_error(resp))
    return resp.json()


def _authed_post(path: str, token: str | None, payload: Dict[str, Any] | None = None, timeout: int | None = None) -> Any:
    timeout = timeout or REQUEST_TIMEOUT
    url = f"{API_URL.rstrip('/')}{path}"
    s = _session_with_retries()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = s.post(url, json=payload or {}, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        raise APIError(str(exc))
    if resp.status_code in (401, 403):
        raise AuthError(_extract_error(resp))
    if resp.status_code != 200:
        raise APIError(_extract_error(resp))
    return resp.json()


def get_command_center(token: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    return _authed_get("/clinical/command-center", token, timeout=timeout)


def get_monitoring_summary(token: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    return _authed_get("/clinical/monitoring", token, timeout=timeout)


def get_drift_panel(token: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    return _authed_get("/clinical/drift", token, timeout=timeout)


def get_governance_panel(token: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    return _authed_get("/clinical/governance", token, timeout=timeout)


def activate_model(model_id: int, token: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    return _authed_post(f"/clinical/governance/activate/{model_id}", token, timeout=timeout)


def deactivate_model(model_id: int, token: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    return _authed_post(f"/clinical/governance/deactivate/{model_id}", token, timeout=timeout)


def get_prediction_logs(token: str | None = None, timeout: int | None = None) -> List[Dict[str, Any]]:
    return _authed_get("/clinical/prediction-logs", token, timeout=timeout)


def get_longitudinal(patient_id: int, token: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    return _authed_get(f"/clinical/patient/{patient_id}/longitudinal", token, timeout=timeout)


def get_performance_snapshot(token: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    return _authed_get("/clinical/performance", token, timeout=timeout)


def get_system_health(token: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    return _authed_get("/clinical/system-health", token, timeout=timeout)


def get_future_hooks(token: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    return _authed_get("/clinical/future-hooks", token, timeout=timeout)


def get_synthetic_profile(profile: str, token: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    return _authed_get(f"/clinical/synthetic/{profile}", token, timeout=timeout)


def get_inference_metadata(features: Dict[str, Any], model_version: str, token: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    return _authed_post(
        "/clinical/inference-metadata",
        token,
        payload={"features": features, "model_version": model_version},
        timeout=timeout,
    )


def get_model_registry(token: str | None = None, timeout: int | None = None) -> List[Dict[str, Any]]:
    """Fetch full model registry from backend."""
    return _authed_get("/models/registry", token, timeout=timeout)


def get_active_model_version(token: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    """Get information about currently active/production model."""
    return _authed_get("/models/active", token, timeout=timeout)


def get_model_version_info(version: str, token: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    """Get detailed info for a specific model version."""
    return _authed_get(f"/models/version/{version}", token, timeout=timeout)


def compare_model_versions(version1: str, version2: str, token: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    """Compare performance metrics between two model versions."""
    return _authed_get(f"/models/compare?v1={version1}&v2={version2}", token, timeout=timeout)


def get_model_performance_history(token: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    """Get historical performance metrics for models."""
    return _authed_get("/models/performance-history", token, timeout=timeout)


def get_prediction_confidence_trend(days: int = 7, token: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    """Get prediction confidence trend over time period."""
    return _authed_get(f"/analytics/confidence-trend?days={days}", token, timeout=timeout)


def get_drift_trends(token: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    """Get drift metric trends over time."""
    return _authed_get("/analytics/drift-trends", token, timeout=timeout)


def resolve_model_version(runtime_version: str | None, patient_id: int | None = None, token: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    """Request server-side version resolution with fallback."""
    return _authed_post(
        "/models/resolve-version",
        token,
        payload={"runtime_version": runtime_version, "patient_id": patient_id},
        timeout=timeout,
    )


def get_patient_risk_progression(patient_id: int, token: str | None = None, timeout: int | None = None) -> Dict[str, Any]:
    """Get risk progression analysis for a patient."""
    return _authed_get(f"/patients/{patient_id}/risk-progression", token, timeout=timeout)


def get_prediction_audit_logs(patient_id: int | None = None, limit: int = 100, token: str | None = None, timeout: int | None = None) -> List[Dict[str, Any]]:
    """Get audit trail of predictions with searchable filters."""
    params = f"?limit={limit}"
    if patient_id:
        params += f"&patient_id={patient_id}"
    return _authed_get(f"/audit/predictions{params}", token, timeout=timeout)
