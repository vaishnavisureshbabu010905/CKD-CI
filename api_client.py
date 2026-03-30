import os
from typing import Any, Dict, List

import requests

API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")


def _extract_error_message(resp: requests.Response) -> str:
    try:
        payload = resp.json()
        if isinstance(payload, dict):
            return str(payload.get("detail") or payload.get("message") or payload)
        return str(payload)
    except Exception:
        return resp.text or f"HTTP {resp.status_code}"


def login(email: str, password: str, timeout: int = 20) -> Dict[str, Any]:
    resp = requests.post(f"{API_BASE_URL}/auth/login", json={"email": email, "password": password}, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(_extract_error_message(resp))
    return resp.json()


def predict(payload: Dict[str, Any], token: str | None = None, timeout: int = 25) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    resp = requests.post(f"{API_BASE_URL}/predictions/predict", json=payload, headers=headers, timeout=timeout)
    if resp.status_code in (401, 403):
        raise PermissionError(_extract_error_message(resp))
    if resp.status_code != 200:
        raise RuntimeError(_extract_error_message(resp))
    return resp.json()


def batch_predict(items: List[Dict[str, Any]], token: str | None = None, timeout: int = 60) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    resp = requests.post(f"{API_BASE_URL}/predictions/batch", json={"items": items}, headers=headers, timeout=timeout)
    if resp.status_code in (401, 403):
        raise PermissionError(_extract_error_message(resp))
    if resp.status_code != 200:
        raise RuntimeError(_extract_error_message(resp))
    return resp.json()


def get_history(token: str | None = None, timeout: int = 25) -> List[Dict[str, Any]]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    resp = requests.get(f"{API_BASE_URL}/predictions/history", headers=headers, timeout=timeout)
    if resp.status_code in (401, 403):
        raise PermissionError(_extract_error_message(resp))
    if resp.status_code != 200:
        raise RuntimeError(_extract_error_message(resp))
    return resp.json()


def get_admin_analytics(token: str | None = None, timeout: int = 25) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    resp = requests.get(f"{API_BASE_URL}/admin/analytics", headers=headers, timeout=timeout)
    if resp.status_code in (401, 403):
        raise PermissionError(_extract_error_message(resp))
    if resp.status_code != 200:
        raise RuntimeError(_extract_error_message(resp))
    return resp.json()


def get_health(timeout: int = 5) -> bool:
    try:
        resp = requests.get(f"{API_BASE_URL}/health", timeout=timeout)
        return resp.status_code == 200
    except Exception:
        return False
