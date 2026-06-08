"""flow_status コレクションを Firestore REST API 経由で読み込む。"""
from datetime import datetime, timezone
from typing import Any


def get_flow_status(firebase_client_module) -> dict[str, dict[str, Any]]:
    """Firestore の flow_status/latest ドキュメントを読む。
    引数は utils.firebase_client モジュール（get_doc を持つ）。
    """
    _default = {
        "maintenance": {"status": "unknown", "last_run": None, "duration_seconds": None},
        "strategy":    {"status": "unknown", "last_run": None, "duration_seconds": None},
        "content":     {"status": "unknown", "last_run": None, "duration_seconds": None},
        "daily":       {"status": "unknown", "last_run": None, "duration_seconds": None},
    }
    try:
        doc = firebase_client_module.get_doc("flow_status", "latest")
        if doc:
            return doc
    except Exception:
        pass
    return _default


def format_last_run(iso_str: str | None) -> str:
    if not iso_str:
        return "未実行"
    try:
        dt = datetime.fromisoformat(iso_str).astimezone()
        now = datetime.now(timezone.utc).astimezone()
        diff = now - dt
        if diff.days == 0 and diff.seconds < 3600:
            return f"{diff.seconds // 60}分前"
        if diff.days == 0:
            return dt.strftime("%H:%M")
        return dt.strftime("%m/%d %H:%M")
    except Exception:
        return (iso_str[:16] if iso_str else "不明")


def status_icon(status: str | None) -> str:
    if not status or status == "unknown":
        return "⬜"
    if status == "ok":
        return "✅"
    if "実行中" in status:
        return "⚙️"
    return "❌"
