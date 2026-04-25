from __future__ import annotations

import json
import urllib.error
import urllib.request


def fetch_json(url: str, timeout: int = 5) -> dict:
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def _normalize_path(path: str) -> str:
    return path if path.startswith("/") else f"/{path}"


def check_health(base_url: str, timeout: int = 5, preferred_path: str | None = None) -> tuple[bool, str]:
    candidates: list[str] = []
    if preferred_path:
        candidates.append(_normalize_path(preferred_path))
    for fallback in ("/health", "/v1/models"):
        if fallback not in candidates:
            candidates.append(fallback)

    for path in candidates:
        url = f"{base_url.rstrip('/')}{path}"
        try:
            fetch_json(url, timeout=timeout)
            return True, f"OK via {path}"
        except (urllib.error.URLError, json.JSONDecodeError):
            continue
    return False, "No known health endpoint responded with JSON"
