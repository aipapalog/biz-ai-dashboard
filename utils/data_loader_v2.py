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
