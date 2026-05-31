"""Firebase優先でデータ取得し、未接続時はローカルJSONにフォールバック。"""
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
    """Kanbanタスク一覧を返す。"""
    fb = firebase_client.get("/dashboard/kanban")
    if fb:
        if isinstance(fb, dict):
            # {"tasks": [...]} 形式
            if "tasks" in fb:
                items = fb["tasks"]
                if isinstance(items, list):
                    return [t for t in items if isinstance(t, dict)]
            items = list(fb.values())
        elif isinstance(fb, list):
            items = fb
        else:
            items = []
        items = [t for t in items if isinstance(t, dict)]
        if items:
            return items
    data = _local("kanban_tasks.json", {})
    if isinstance(data, dict):
        # {"tasks": [...]} 形式
        if "tasks" in data:
            items = data["tasks"]
            if isinstance(items, list):
                return [t for t in items if isinstance(t, dict)]
        return [t for t in data.values() if isinstance(t, dict)]
    if isinstance(data, list):
        return [t for t in data if isinstance(t, dict)]
    return []


def business_status() -> dict:
    fb = firebase_client.get("/dashboard/business")
    return fb if isinstance(fb, dict) else _local("business_status.json", {})


def pf_watch() -> dict:
    fb = firebase_client.get("/dashboard/pf_watch")
    return fb if isinstance(fb, dict) else _local("pf_watch.json", {})


def system_info() -> dict:
    fb = firebase_client.get("/dashboard/system")
    return fb if isinstance(fb, dict) else {}


def pipeline_logs() -> dict:
    fb = firebase_client.get("/dashboard/pipeline_logs")
    return fb if isinstance(fb, dict) else {}


def levelup_history() -> list:
    fb = firebase_client.get("/dashboard/levelup")
    if fb:
        return fb if isinstance(fb, list) else list(fb.values())
    # ローカルlevelup_logsフォルダから最新10件
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
    fb = firebase_client.get("/dashboard/scheduler")
    return fb if isinstance(fb, list) else []


def datasource() -> dict:
    fb = firebase_client.get("/dashboard/datasource")
    return fb if isinstance(fb, dict) else _local("data/datasource.json", {})


def last_updated() -> str:
    fb = firebase_client.get("/dashboard/last_updated", "")
    return fb if fb else ""
