"""Firestore REST API接続。Admin SDK不要。APIキーのみで動作。"""
import requests
from typing import Any

PROJECT_ID = "ai-agent-dashboard-5810b"
API_KEY = "AIzaSyAphCqxbM-fHenxUNFikW_AsVTNuPc_Ems"
BASE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"
HEADERS = {"User-Agent": "Claude-Script/1.0"}
_ok: bool | None = None


def _from_firestore(field: dict) -> Any:
    """Firestoreフィールド形式をPython値に変換。"""
    if "stringValue" in field:
        return field["stringValue"]
    if "integerValue" in field:
        return int(field["integerValue"])
    if "doubleValue" in field:
        return field["doubleValue"]
    if "booleanValue" in field:
        return field["booleanValue"]
    if "nullValue" in field:
        return None
    if "arrayValue" in field:
        return [_from_firestore(v) for v in field["arrayValue"].get("values", [])]
    if "mapValue" in field:
        return {k: _from_firestore(v) for k, v in field["mapValue"].get("fields", {}).items()}
    return None


def get_doc(collection: str, doc_id: str) -> dict:
    try:
        r = requests.get(f"{BASE_URL}/{collection}/{doc_id}?key={API_KEY}",
                         headers=HEADERS, timeout=10)
        if r.status_code == 200:
            fields = r.json().get("fields", {})
            return {k: _from_firestore(v) for k, v in fields.items()}
    except Exception:
        pass
    return {}


def get_collection(collection: str, max_docs: int = 1000) -> list:
    result, page_token = [], None
    while len(result) < max_docs:
        url = f"{BASE_URL}/{collection}?pageSize=300&key={API_KEY}"
        if page_token:
            url += f"&pageToken={page_token}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                break
            data = r.json()
            for d in data.get("documents", []):
                result.append({k: _from_firestore(v) for k, v in d.get("fields", {}).items()})
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        except Exception:
            break
    return result


def is_available() -> bool:
    global _ok
    if _ok is not None:
        return _ok
    try:
        r = requests.get(f"{BASE_URL}/dashboard/meta?key={API_KEY}",
                         headers=HEADERS, timeout=5)
        _ok = r.status_code in (200, 404)
    except Exception:
        _ok = False
    return _ok
