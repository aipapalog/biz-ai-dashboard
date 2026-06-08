import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import style, data_loader_v2, firebase_client

st.set_page_config(page_title="✅ タスク | BizDash", layout="wide")
style.inject()

# ── データ取得 ──────────────────────────────────────────────────────────────
push_log = data_loader_v2.get_push_log()
st.markdown(
    f'<div style="text-align:right;">{style.freshness_banner(push_log)}</div>',
    unsafe_allow_html=True
)

tasks_data = data_loader_v2.get_tasks()
health = data_loader_v2.get_system_health()

style.page_header(
    "✅ タスク",
    subtitle="Kanbanタスク状況 + 要対応項目",
    updated=push_log.get("timestamp", ""),
    status="ok"
)

# ── レイアウト（左：要対応、右：Kanban） ────────────────────────────────────
col_left, col_right = st.columns([1, 2])

with col_left:
    style.section_card_start("🔴 要対応", "", "err")
    alerts = health.get("alerts", [])
    high = tasks_data.get("high_priority", [])

    # alert と high priority をマージ
    items = [{"text": a, "level": "red"} for a in alerts] + \
            [{"text": t, "level": "yellow"} for t in high[:5]]

    if items:
        for item in items:
            css = "glass-alert-red" if item["level"] == "red" else "glass-alert-yellow"
            st.markdown(f'<div class="{css}">{item["text"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="glass-card" style="color:#a6e3a1;">✅ 要対応なし</div>',
            unsafe_allow_html=True
        )
    style.section_card_end()

with col_right:
    style.section_card_start("📋 Kanban", "", "info")

    summary = tasks_data.get("summary", {})
    active = tasks_data.get("active", {})

    # active がリストの場合とdictの場合に対応
    if isinstance(active, list):
        raw_tasks = active
    elif isinstance(active, dict):
        raw_tasks = list(active.values()) if active else []
    else:
        raw_tasks = []

    # ステータスでフィルタ
    todo = [
        t for t in raw_tasks
        if isinstance(t, dict) and t.get("status") == "todo"
    ]
    in_prog = [
        t for t in raw_tasks
        if isinstance(t, dict) and t.get("status") == "in_progress"
    ]
    done = [
        t for t in raw_tasks
        if isinstance(t, dict) and t.get("status") == "done"
    ]

    # summary から補完（active がない場合）
    todo_count = len(todo) or summary.get("todo", 0)
    in_prog_count = len(in_prog) or summary.get("in_progress", 0)
    done_count = len(done) or summary.get("done", 0)

    # 3カラムレイアウト
    c1, c2, c3 = st.columns(3)

    # TODO列
    with c1:
        st.markdown(
            f'<div style="color:#6c7086;font-size:11px;margin-bottom:6px;font-weight:600;">'
            f'TODO ({todo_count})</div>',
            unsafe_allow_html=True
        )
        for t in todo[:10]:
            title = str(t.get("title", t.get("subject", "")))[:40]
            kid = t.get("id", t.get("task_id", ""))
            st.markdown(
                f'<div class="glass-card" style="padding:8px;font-size:11px;">'
                f'<span style="color:#6c7086;font-family:monospace;">{kid}</span><br>'
                f'{title}</div>',
                unsafe_allow_html=True
            )

    # IN PROGRESS列
    with c2:
        st.markdown(
            f'<div style="color:#f9e2af;font-size:11px;margin-bottom:6px;font-weight:600;">'
            f'IN PROGRESS ({in_prog_count})</div>',
            unsafe_allow_html=True
        )
        for t in in_prog[:10]:
            title = str(t.get("title", t.get("subject", "")))[:40]
            kid = t.get("id", t.get("task_id", ""))
            st.markdown(
                f'<div class="glass-card" style="padding:8px;font-size:11px;">'
                f'<span style="color:#6c7086;font-family:monospace;">{kid}</span><br>'
                f'{title}</div>',
                unsafe_allow_html=True
            )

    # DONE列
    with c3:
        st.markdown(
            f'<div style="color:#a6e3a1;font-size:11px;margin-bottom:6px;font-weight:600;">'
            f'DONE ({done_count})</div>',
            unsafe_allow_html=True
        )
        for t in done[:10]:
            title = str(t.get("title", t.get("subject", "")))[:40]
            kid = t.get("id", t.get("task_id", ""))
            st.markdown(
                f'<div class="glass-card" style="padding:8px;font-size:11px;">'
                f'<span style="color:#6c7086;font-family:monospace;">{kid}</span><br>'
                f'{title}</div>',
                unsafe_allow_html=True
            )

    style.section_card_end()

# ── タスク統計（下部） ──────────────────────────────────────────────────────
style.section_card_start("📊 タスク統計", "", "info")
stat_c1, stat_c2, stat_c3, stat_c4 = st.columns(4)

with stat_c1:
    style.kpi_wrap_start("info")
    st.metric("📝 総タスク数", tasks_data.get("total", 0))
    style.kpi_wrap_end()

with stat_c2:
    style.kpi_wrap_start("warn")
    st.metric("🔄 進行中", in_prog_count)
    style.kpi_wrap_end()

with stat_c3:
    style.kpi_wrap_start("ok")
    st.metric("✅ 完了", done_count)
    style.kpi_wrap_end()

with stat_c4:
    style.kpi_wrap_start("critical" if tasks_data.get("in_progress", 0) > 10 else "info")
    st.metric("⚠️ 待機中", todo_count)
    style.kpi_wrap_end()

style.section_card_end()
