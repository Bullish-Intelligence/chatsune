from __future__ import annotations

import json
import urllib.error
import urllib.request


def fetch_json(url: str, timeout: int = 5) -> dict:
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def check_health(base_url: str, timeout: int = 5) -> tuple[bool, str]:
    for path in ("/health", "/v1/models"):
        url = f"{base_url.rstrip('/')}{path}"
        try:
            fetch_json(url, timeout=timeout)
            return True, f"OK via {path}"
        except (urllib.error.URLError, json.JSONDecodeError):
            continue
    return False, "No known health endpoint responded with JSON"
