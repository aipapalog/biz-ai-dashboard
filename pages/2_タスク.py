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

# フィールド正規化（name / title 統一）
for t in tasks:
    if not t.get("name"):
        t["name"] = t.get("title", "(無題)")

STATUS_ICONS   = {"open": "⬜", "in_progress": "🔵", "to_verify": "🟡", "closed": "✅"}
PRIORITY_ICONS = {"high": "🔴", "medium": "🟡", "low": "⚪"}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2, "": 3}

# ── KPI ──────────────────────────────────────────────────────────────────────
counts = {"open": 0, "in_progress": 0, "to_verify": 0, "closed": 0}
for t in tasks:
    s = t.get("status", "open")
    if s in counts:
        counts[s] += 1

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("⬜ Open", counts["open"])
with c2:
    st.metric("🔵 進行中", counts["in_progress"])
with c3:
    tv = counts["to_verify"]
    st.metric("🟡 確認待ち", tv,
              delta="要対応" if tv >= 5 else None,
              delta_color="inverse" if tv >= 5 else "normal")
with c4:
    st.metric("✅ 完了", counts["closed"])
with c5:
    st.metric("合計", len(tasks))

st.divider()

# ── フィルター ────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    status_filter = st.selectbox("ステータス", ["すべて", "open", "in_progress", "to_verify", "closed"])
with col2:
    priority_filter = st.selectbox("優先度", ["すべて", "high", "medium", "low"])
with col3:
    assignees = sorted({t.get("assignee", "") for t in tasks if t.get("assignee")})
    assignee_filter = st.selectbox("担当者", ["すべて"] + assignees)
with col4:
    search = st.text_input("キーワード検索", placeholder="タイトル・説明")

# フィルター適用
filtered = tasks
if status_filter != "すべて":
    filtered = [t for t in filtered if t.get("status") == status_filter]
if priority_filter != "すべて":
    filtered = [t for t in filtered if t.get("priority") == priority_filter]
if assignee_filter != "すべて":
    filtered = [t for t in filtered if t.get("assignee") == assignee_filter]
if search:
    kw = search.lower()
    filtered = [t for t in filtered
                if kw in (t.get("name", "") + " " + (t.get("description") or "")).lower()]

st.caption(f"表示中: **{len(filtered)} 件** / 全 {len(tasks)} 件")


# ── タスクカード描画 ──────────────────────────────────────────────────────────
def task_card(t: dict):
    status     = t.get("status", "open")
    priority   = t.get("priority", "")
    name       = t.get("name", "(無題)")
    assignee   = t.get("assignee", "-")
    task_id    = t.get("id", "-")
    desc       = t.get("description") or ""
    result     = t.get("result") or ""
    created    = (t.get("created_at") or "")[:10]
    updated    = (t.get("updated_at") or "")[:10]
    created_by = t.get("created_by", "-")
    comments   = t.get("comments") or []

    s_icon = STATUS_ICONS.get(status, "⬜")
    p_icon = PRIORITY_ICONS.get(priority, "⚪")

    with st.expander(f"{s_icon} {p_icon} **{name}** — 👤 {assignee}", expanded=False):
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            st.write(f"**ID:** `{task_id}`")
            st.write(f"**ステータス:** {status}")
            st.write(f"**優先度:** {priority or '-'}")
        with mc2:
            st.write(f"**担当者:** {assignee}")
            st.write(f"**起票者:** {created_by}")
        with mc3:
            st.write(f"**作成:** {created or '-'}")
            st.write(f"**更新:** {updated or '-'}")

        if desc:
            st.markdown("---")
            st.markdown(f"**説明:** {desc}")

        if result:
            st.markdown("---")
            st.success(f"**結果:** {result}")

        if comments:
            st.markdown("---")
            st.caption(f"💬 コメント（{len(comments)} 件）")
            for c in (comments[-3:] if isinstance(comments, list) else []):
                if not isinstance(c, dict):
                    continue
                author = c.get("author") or c.get("user") or "?"
                text   = c.get("text") or c.get("content") or ""
                ts     = (c.get("created_at") or c.get("timestamp") or "")[:10]
                st.markdown(f"**{author}** ({ts}): {text}")


# ── タブ ──────────────────────────────────────────────────────────────────────
tab_board, tab_list, tab_assignee = st.tabs(["📌 ボードビュー", "📋 リスト", "👤 担当者別"])

# ── ボードビュー ──────────────────────────────────────────────────────────────
with tab_board:
    board_tasks = filtered if (status_filter != "すべて" or priority_filter != "すべて"
                               or assignee_filter != "すべて" or search) else tasks

    b1, b2, b3, b4 = st.columns(4)
    for col, (label, status) in zip(
        [b1, b2, b3, b4],
        [("⬜ Open", "open"), ("🔵 進行中", "in_progress"),
         ("🟡 確認待ち", "to_verify"), ("✅ 完了", "closed")]
    ):
        with col:
            group = sorted(
                [t for t in board_tasks if t.get("status") == status],
                key=lambda t: PRIORITY_ORDER.get(t.get("priority", ""), 3)
            )
            st.markdown(f"**{label} ({len(group)})**")
            st.divider()
            for t in group[:25]:
                p_icon = PRIORITY_ICONS.get(t.get("priority", ""), "⚪")
                name   = t.get("name", "(無題)")
                tid    = t.get("id", "")
                assign = t.get("assignee", "")
                desc   = (t.get("description") or "")[:120]
                result = (t.get("result") or "")[:120]
                with st.expander(f"{p_icon} {name[:28]}", expanded=False):
                    st.caption(f"ID: {tid}  担当: {assign}")
                    if desc:
                        st.write(desc)
                    if result:
                        st.success(result)
            if len(group) > 25:
                st.caption(f"…他 {len(group)-25} 件（リストで全件確認）")

# ── リスト ────────────────────────────────────────────────────────────────────
with tab_list:
    sorted_tasks = sorted(
        [t for t in filtered if t.get("status") != "closed"],
        key=lambda t: PRIORITY_ORDER.get(t.get("priority", ""), 3)
    ) + sorted(
        [t for t in filtered if t.get("status") == "closed"],
        key=lambda t: (t.get("updated_at") or ""),
        reverse=True
    )
    for t in sorted_tasks:
        task_card(t)

# ── 担当者別 ──────────────────────────────────────────────────────────────────
with tab_assignee:
    groups: dict = {}
    for t in tasks:
        if status_filter != "すべて" and t.get("status") != status_filter:
            continue
        a = t.get("assignee") or "未割当"
        groups.setdefault(a, []).append(t)

    for assignee, a_tasks in sorted(groups.items()):
        c = {s: sum(1 for t in a_tasks if t.get("status") == s)
             for s in ["open", "in_progress", "to_verify", "closed"]}
        badge = (f"⬜{c['open']}  🔵{c['in_progress']}"
                 f"  🟡{c['to_verify']}  ✅{c['closed']}")
        st.subheader(f"👤 {assignee}  —  {len(a_tasks)} 件　　{badge}")

        for status_key in ["in_progress", "to_verify", "open", "closed"]:
            group = sorted(
                [t for t in a_tasks if t.get("status") == status_key],
                key=lambda t: PRIORITY_ORDER.get(t.get("priority", ""), 3)
            )
            if not group:
                continue
            st.markdown(
                f"**{STATUS_ICONS[status_key]} {status_key} ({len(group)})**"
            )
            for t in group[:20]:
                task_card(t)
            if len(group) > 20:
                st.caption(f"…他 {len(group)-20} 件")
        st.divider()
