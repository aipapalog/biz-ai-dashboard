import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader

st.set_page_config(page_title="タスク（Kanban）", page_icon="📋", layout="wide")
st_autorefresh(interval=60_000, key="tasks_refresh")
st.title("📋 タスク（Kanban）")

tasks = data_loader.kanban_tasks()

# ── フィルター ────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    status_filter = st.selectbox("ステータス", ["すべて", "open", "in_progress", "to_verify", "closed"])
with col2:
    priority_filter = st.selectbox("優先度", ["すべて", "high", "medium", "low"])
with col3:
    search = st.text_input("タイトル検索", placeholder="キーワードを入力")

# フィルター適用
filtered = tasks
if status_filter != "すべて":
    filtered = [t for t in filtered if t.get("status") == status_filter]
if priority_filter != "すべて":
    filtered = [t for t in filtered if t.get("priority") == priority_filter]
if search:
    filtered = [t for t in filtered if search.lower() in t.get("title", "").lower()]

# ── KPI ──────────────────────────────────────────────────────────────────────
status_counts = {"open": 0, "in_progress": 0, "to_verify": 0, "closed": 0}
for t in tasks:
    s = t.get("status", "open")
    if s in status_counts:
        status_counts[s] += 1

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Open", status_counts["open"])
with c2:
    st.metric("進行中", status_counts["in_progress"])
with c3:
    tv = status_counts["to_verify"]
    st.metric("確認待ち", tv, delta="⚠️ 多い" if tv >= 5 else None,
              delta_color="inverse" if tv >= 5 else "normal")
with c4:
    st.metric("完了", status_counts["closed"])

st.caption(f"表示中: {len(filtered)} 件 ／ 全 {len(tasks)} 件")
st.divider()

# ── ステータス別カラムビュー（すべて表示時）─────────────────────────────────
if status_filter == "すべて" and not search and priority_filter == "すべて":
    st.subheader("ボードビュー")
    cols = st.columns(4)
    headers = [("Open", "open"), ("進行中", "in_progress"), ("確認待ち", "to_verify"), ("完了", "closed")]
    for col, (label, status) in zip(cols, headers):
        with col:
            group = [t for t in tasks if t.get("status") == status]
            st.markdown(f"**{label} ({len(group)})**")
            for t in group[:10]:
                p = t.get("priority", "")
                icon = "🔴" if p == "high" else ("🟡" if p == "medium" else "⚪")
                st.markdown(f"{icon} {t.get('title', '(無題)')[:30]}")
            if len(group) > 10:
                st.caption(f"...他 {len(group)-10} 件")
    st.divider()

# ── タスク詳細リスト ──────────────────────────────────────────────────────────
st.subheader("タスク詳細")
priority_order = {"high": 0, "medium": 1, "low": 2, "": 3}
filtered_sorted = sorted(filtered, key=lambda t: (
    priority_order.get(t.get("priority", ""), 3),
    t.get("due_date", "9999")
))

STATUS_ICONS = {
    "open": "⬜", "in_progress": "🔵", "to_verify": "🟡", "closed": "✅"
}
PRIORITY_ICONS = {"high": "🔴", "medium": "🟡", "low": "⚪"}

for t in filtered_sorted:
    status = t.get("status", "open")
    priority = t.get("priority", "")
    s_icon = STATUS_ICONS.get(status, "⬜")
    p_icon = PRIORITY_ICONS.get(priority, "⚪")
    title = t.get("title", "(無題)")
    due = t.get("due_date", "-")
    assignee = t.get("assignee", "-")

    with st.expander(f"{s_icon} {p_icon} **{title}** — 担当: {assignee} ／ 期限: {due}"):
        col1, col2 = st.columns([3, 1])
        with col1:
            desc = t.get("description", "")
            if desc:
                st.write(desc[:500])
            result = t.get("result", "")
            if result:
                st.success(f"**結果:** {result[:300]}")
        with col2:
            st.write(f"**ID:** {t.get('id', '-')}")
            st.write(f"**ステータス:** {status}")
            st.write(f"**優先度:** {priority or '-'}")
            created = t.get("created_at", "-")
            st.write(f"**作成:** {created[:10] if created and created != '-' else '-'}")

        # コメント
        comments = t.get("comments", [])
        if comments:
            st.divider()
            st.caption(f"💬 コメント ({len(comments)} 件)")
            for c in comments[-3:]:
                st.markdown(f"**{c.get('author', '?')}** ({c.get('created_at', '')[:10]}): {c.get('text', '')}")
