"""Firestore優先でデータ取得し、未接続時はローカルJSONにフォールバック。"""
import json
import os
from pathlib import Path
from typing import Any
from utils import firebase_client

AGENTS_DIR = Path(r"C:\Users\0000112191\.claude\scripts\agents")


def _local(filename: str, default: Any = None) -> Any:
    for base in [AGENTS_DIR, AGENTS_DIR / "data"]:
        p = base / filename
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8-sig"))
            except Exception:
                pass
    return default


def kanban_tasks() -> list:
    fb = firebase_client.get_collection("kanban_tasks")
    if fb:
        return [t for t in fb if isinstance(t, dict)]
    # ローカルフォールバック
    data = _local("kanban_tasks.json", {})
    if isinstance(data, dict) and "tasks" in data:
        return [t for t in data["tasks"] if isinstance(t, dict)]
    return []


def business_status() -> dict:
    fb = firebase_client.get_doc("dashboard", "business_status")
    return fb if fb else _local("business_status.json", {})


def pf_watch() -> dict:
    fb = firebase_client.get_doc("dashboard", "pf_watch")
    return fb if fb else _local("pf_watch.json", {})


def system_info() -> dict:
    return firebase_client.get_doc("dashboard", "system_info")


def pipeline_logs() -> dict:
    fb = firebase_client.get_doc("dashboard", "pipeline_logs")
    return fb if isinstance(fb, dict) else {}


def levelup_history() -> list:
    fb = firebase_client.get_collection("levelup_history")
    if fb:
        return fb
    logs_dir = AGENTS_DIR / "levelup_logs"
    if not logs_dir.exists():
        return []
    files = sorted(logs_dir.glob("*.json"), key=os.path.getmtime, reverse=True)[:10]
    result = []
    for f in files:
        try:
            result.append(json.loads(f.read_text(encoding="utf-8-sig")))
        except Exception:
            pass
    return result


def scheduler_tasks() -> list:
    fb = firebase_client.get_doc("dashboard", "scheduler")
    return fb.get("tasks", []) if isinstance(fb, dict) else []


def bizdev_report() -> dict:
    fb = firebase_client.get_doc("dashboard", "bizdev_report")
    return fb if isinstance(fb, dict) else {}


def datasource() -> dict:
    fb = firebase_client.get_doc("dashboard", "datasource")
    return fb if fb else _local("data/datasource.json", {})


def last_updated() -> str:
    fb = firebase_client.get_doc("dashboard", "meta")
    return fb.get("last_updated", "") if fb else ""
