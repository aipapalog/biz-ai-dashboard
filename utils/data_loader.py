"""Firestore優先でデータ取得し、未接続時はローカルJSONにフォールバック。"""
import json
import os
from datetime import datetime
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
    # kanban_tasks コレクション優先（書き込みを即時反映）
    fb = firebase_client.get_collection("kanban_tasks")
    if fb:
        tasks = [t for t in fb if isinstance(t, dict)]
        # name フィールド正規化
        for t in tasks:
            if not t.get("name"):
                t["name"] = t.get("title", "")
        return tasks
    # dashboard/kanban_active（pusher が 30 分毎更新）
    fb_doc = firebase_client.get_doc("dashboard", "kanban_active")
    if fb_doc and fb_doc.get("tasks"):
        return [t for t in fb_doc["tasks"] if isinstance(t, dict)]
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


def cx_report() -> dict:
    fb = firebase_client.get_doc("dashboard", "cx_report")
    return fb if isinstance(fb, dict) else {}


def risk_report() -> dict:
    fb = firebase_client.get_doc("dashboard", "risk_report")
    return fb if isinstance(fb, dict) else {}


def health_check() -> dict:
    fb = firebase_client.get_doc("dashboard", "health_check")
    return fb if isinstance(fb, dict) else {}


def freelance_report() -> dict:
    fb = firebase_client.get_doc("dashboard", "freelance_report")
    return fb if isinstance(fb, dict) else {}


def api_budget() -> dict:
    fb = firebase_client.get_doc("dashboard", "api_budget")
    return fb if isinstance(fb, dict) else {}


def execution_times() -> dict:
    fb = firebase_client.get_doc("dashboard", "execution_times")
    return fb if isinstance(fb, dict) else {}


def levelup_status() -> dict:
    fb = firebase_client.get_doc("dashboard", "levelup_status")
    return fb if isinstance(fb, dict) else {}


def autonomous_loop() -> dict:
    fb = firebase_client.get_doc("dashboard", "autonomous_loop")
    return fb if isinstance(fb, dict) else {}


def funnel() -> dict:
    fb = firebase_client.get_doc("dashboard", "funnel")
    return fb if isinstance(fb, dict) else {}


def pdca() -> dict:
    fb = firebase_client.get_doc("dashboard", "pdca")
    return fb if isinstance(fb, dict) else {}


def mempalace() -> dict:
    fb = firebase_client.get_doc("dashboard", "mempalace")
    return fb if isinstance(fb, dict) else {}


def agent_insights() -> dict:
    fb = firebase_client.get_doc("dashboard", "agent_insights")
    return fb if isinstance(fb, dict) else {}


def routines() -> list:
    fb = firebase_client.get_doc("dashboard", "routines")
    if isinstance(fb, dict):
        return fb.get("items", []) if "items" in fb else list(fb.values())
    return []


# ── 書き込み関数 ──────────────────────────────────────────────────────────────

def update_task(task_id: str, updates: dict) -> bool:
    """タスクフィールドを更新する。kanban_tasks/{task_id} に PATCH。"""
    updates["updated_at"] = datetime.now().isoformat()
    return firebase_client.patch_doc("kanban_tasks", task_id, updates)


def add_task_comment(task_id: str, author: str, text: str, existing_comments: list) -> bool:
    """タスクにコメントを追加する。"""
    new_comment = {
        "author": author,
        "text": text,
        "created_at": datetime.now().isoformat(),
    }
    updated = list(existing_comments or []) + [new_comment]
    return firebase_client.patch_doc("kanban_tasks", task_id, {
        "comments": updated,
        "updated_at": datetime.now().isoformat(),
    })


def create_task(name: str, assignee: str = "社長", priority: str = "medium",
                description: str = "", created_by: str = "ダッシュボード") -> tuple:
    """新規タスクを作成して (ok: bool, new_id: str) を返す。"""
    tasks = kanban_tasks()
    nums = []
    for t in tasks:
        tid = t.get("id", "")
        if tid.startswith("KT-") and tid[3:].isdigit():
            nums.append(int(tid[3:]))
    new_num = max(nums, default=0) + 1
    new_id = f"KT-{new_num}"
    now = datetime.now().isoformat()
    data = {
        "id": new_id, "name": name, "status": "open",
        "priority": priority, "assignee": assignee,
        "created_by": created_by, "description": description,
        "result": "", "comments": [],
        "created_at": now, "updated_at": now,
    }
    ok = firebase_client.patch_doc("kanban_tasks", new_id, data)
    return ok, new_id


def datasource() -> dict:
    fb = firebase_client.get_doc("dashboard", "datasource")
    return fb if fb else _local("data/datasource.json", {})


def last_updated() -> str:
    fb = firebase_client.get_doc("dashboard", "meta")
    return fb.get("last_updated", "") if fb else ""
