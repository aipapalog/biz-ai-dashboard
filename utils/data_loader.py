import streamlit as st
from utils.firebase_client import get_doc


@st.cache_data(ttl=3600)
def get_system_health() -> dict:
    return get_doc("dashboard", "system_health") or {
        "flows": {}, "alerts": [], "pipeline_count": 0,
        "scheduler": {}, "last_run": "",
    }


@st.cache_data(ttl=3600)
def get_tasks() -> dict:
    return get_doc("dashboard", "tasks") or {
        "summary": {}, "active": {}, "total": 0,
        "in_progress": 0, "high_priority": [],
    }


@st.cache_data(ttl=3600)
def get_business() -> dict:
    return get_doc("dashboard", "business") or {
        "business_status": {}, "pf_watch": {}, "freelance": {},
    }


@st.cache_data(ttl=3600)
def get_bizdev() -> dict:
    return get_doc("dashboard", "bizdev") or {"report": {}, "trend": {}}


@st.cache_data(ttl=3600)
def get_cx_quality() -> dict:
    return get_doc("dashboard", "cx_quality") or {
        "cx_report": {}, "levelup_status": {}, "levelup_history": [],
    }


@st.cache_data(ttl=3600)
def get_ai_ops() -> dict:
    return get_doc("dashboard", "ai_ops") or {
        "autonomous_loop": {}, "agent_run_stats": {}, "agent_insights": {},
    }


@st.cache_data(ttl=3600)
def get_finance() -> dict:
    return get_doc("dashboard", "finance") or {
        "api_budget": {}, "cost_report": {}, "token_usage": {},
    }


@st.cache_data(ttl=3600)
def get_content() -> dict:
    return get_doc("dashboard", "content") or {
        "mempalace": {}, "mempalace_rooms": {}, "obsidian": {},
        "sync_brain": {}, "sync_tasks": {},
    }


@st.cache_data(ttl=3600)
def get_meta() -> dict:
    return get_doc("dashboard", "meta") or {
        "risk_report": {}, "failure_patterns": {}, "code_health": {},
        "eval_status": {}, "pdca": {}, "biz_pdca": {}, "last_updated": "",
    }


def get_push_log() -> dict:
    """キャッシュなし — 鮮度バナー表示用"""
    return get_doc("dashboard", "_push_log") or {
        "timestamp": None, "success_count": 0, "fail_count": 0, "errors": {},
    }


# ── v1 互換関数（data_loader.py から統合）────────────────────────────────────
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


def kanban_summary() -> dict:
    fb = firebase_client.get_doc("dashboard", "kanban_summary")
    return fb if isinstance(fb, dict) else {}


def kanban_tasks() -> list:
    fb = firebase_client.get_collection("kanban_tasks")
    if fb:
        tasks = [t for t in fb if isinstance(t, dict)]
        for t in tasks:
            if not t.get("name"):
                t["name"] = t.get("title", "")
        return tasks
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


def pipeline_status() -> dict:
    """PIPELINES_DEF×スケジューラ×ログ×ファイルを自動突合した統合ステータス（推奨）。"""
    fb = firebase_client.get_doc("dashboard", "pipeline_status")
    return fb if isinstance(fb, dict) else {}


def pipeline_logs() -> dict:
    """後方互換用。新規ページは pipeline_status() を使うこと。"""
    fb = firebase_client.get_doc("dashboard", "pipeline_logs")
    return fb if isinstance(fb, dict) else {}


def pipeline_merged() -> dict:
    """pipeline_status + pipeline_token_usage を統合した per-pipeline dict。"""
    status_doc = pipeline_status()
    token_doc  = pipeline_token_usage()
    result = {}
    for p in status_doc.get("pipelines", []):
        name = p.get("name", "")
        if not name:
            continue
        tok = token_doc.get(name, {})
        result[name] = {
            **p,
            "token_total":  tok.get("total", 0),
            "token_input":  tok.get("input", 0),
            "token_output": tok.get("output", 0),
            "cost_usd":     tok.get("cost_usd", 0),
            "token_model":  tok.get("model", ""),
            "token_ts":     (tok.get("ts", "") or "")[:10],
        }
    return result


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


def mempalace_rooms() -> dict:
    fb = firebase_client.get_doc("dashboard", "mempalace_rooms")
    return fb if isinstance(fb, dict) else {}


def agent_insights() -> dict:
    fb = firebase_client.get_doc("dashboard", "agent_insights")
    return fb if isinstance(fb, dict) else {}


def comments() -> dict:
    fb = firebase_client.get_doc("dashboard", "comments")
    return fb if isinstance(fb, dict) else {}


def biz_pdca_reports() -> dict:
    fb = firebase_client.get_doc("dashboard", "biz_pdca_reports")
    return fb if isinstance(fb, dict) else {}


def code_health() -> dict:
    fb = firebase_client.get_doc("dashboard", "code_health")
    return fb if isinstance(fb, dict) else {}


def agents_context() -> dict:
    fb = firebase_client.get_doc("dashboard", "agents_context")
    return fb if isinstance(fb, dict) else {}


def rule_engine() -> dict:
    fb = firebase_client.get_doc("dashboard", "rule_engine")
    return fb if isinstance(fb, dict) else {}


def bizdev_trend() -> dict:
    fb = firebase_client.get_doc("dashboard", "bizdev_trend")
    return fb if isinstance(fb, dict) else {}


def pipeline_cost_report() -> dict:
    fb = firebase_client.get_doc("dashboard", "pipeline_cost_report")
    return fb if isinstance(fb, dict) else {}


def routines() -> list:
    fb = firebase_client.get_doc("dashboard", "routines")
    if isinstance(fb, dict):
        return fb.get("items", []) if "items" in fb else list(fb.values())
    return []


# ── 書き込み関数 ─────────────────────────────────────────────────────────────

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


def pipeline_token_usage() -> dict:
    fb = firebase_client.get_doc("dashboard", "pipeline_token_usage")
    return fb if isinstance(fb, dict) else {}


def agent_run_stats() -> dict:
    fb = firebase_client.get_doc("dashboard", "agent_run_stats")
    return fb if isinstance(fb, dict) else {}


def send_pipeline_command(pipeline_name: str, task_name: str) -> bool:
    """Firestore commands コレクションに実行コマンドを書き込む。"""
    now = datetime.now().isoformat()
    return firebase_client.patch_doc("commands", pipeline_name, {
        "action": "run",
        "task_name": task_name,
        "pipeline_name": pipeline_name,
        "status": "pending",
        "created_at": now,
    })


def sync_brain() -> dict:
    fb = firebase_client.get_doc("dashboard", "sync_brain")
    return fb if isinstance(fb, dict) else {}


def sync_tasks() -> dict:
    fb = firebase_client.get_doc("dashboard", "sync_tasks")
    return fb if isinstance(fb, dict) else {}


def learning_system() -> dict:
    fb = firebase_client.get_doc("dashboard", "learning_system")
    return fb if isinstance(fb, dict) else {}


def sync_outputs() -> dict:
    fb = firebase_client.get_doc("dashboard", "sync_outputs")
    return fb if isinstance(fb, dict) else {}


def lessons_learned() -> dict:
    fb = firebase_client.get_doc("dashboard", "lessons_learned")
    return fb if isinstance(fb, dict) else {}


def obsidian_stats() -> dict:
    fb = firebase_client.get_doc("dashboard", "obsidian_stats")
    return fb if isinstance(fb, dict) else {}


def datasource() -> dict:
    fb = firebase_client.get_doc("dashboard", "datasource")
    return fb if fb else _local("data/datasource.json", {})


def eval_status() -> dict:
    fb = firebase_client.get_doc("dashboard", "eval_status")
    return fb if isinstance(fb, dict) else {}


def failure_patterns() -> dict:
    fb = firebase_client.get_doc("dashboard", "failure_patterns")
    return fb if isinstance(fb, dict) else {}


@st.cache_data(ttl=300)
def reliability_kpi() -> dict:
    fb = firebase_client.get_doc("dashboard", "reliability_kpi")
    return fb if isinstance(fb, dict) else {}


@st.cache_data(ttl=300)
def autonomy_kpi() -> dict:
    fb = firebase_client.get_doc("dashboard", "autonomy_kpi")
    return fb if isinstance(fb, dict) else {}


@st.cache_data(ttl=300)
def efficiency_kpi() -> dict:
    fb = firebase_client.get_doc("dashboard", "efficiency_kpi")
    return fb if isinstance(fb, dict) else {}


@st.cache_data(ttl=300)
def learning_kpi() -> dict:
    fb = firebase_client.get_doc("dashboard", "learning_kpi")
    return fb if isinstance(fb, dict) else {}


@st.cache_data(ttl=300)
def roi_score() -> dict:
    fb = firebase_client.get_doc("dashboard", "roi_score")
    return fb if isinstance(fb, dict) else {}


@st.cache_data(ttl=300)
def model_usage_kpi() -> dict:
    fb = firebase_client.get_doc("dashboard", "model_usage_kpi")
    return fb if isinstance(fb, dict) else {}


@st.cache_data(ttl=300)
def anthropic_github_kpi() -> dict:
    fb = firebase_client.get_doc("dashboard", "anthropic_github_kpi")
    return fb if isinstance(fb, dict) else {}


@st.cache_data(ttl=300)
def architecture_kpi() -> dict:
    fb = firebase_client.get_doc("dashboard", "architecture_kpi")
    return fb if isinstance(fb, dict) else {}


def last_updated() -> str:
    fb = firebase_client.get_doc("dashboard", "meta")
    return fb.get("last_updated", "") if fb else ""
