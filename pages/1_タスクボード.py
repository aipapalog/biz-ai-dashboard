import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, style

st.set_page_config(page_title="🗂️ タスクボード", page_icon="🗂️", layout="wide")
style.inject()
st.title("🗂️ タスクボード（Kanban）")

tasks = data_loader.kanban_tasks()
for t in tasks:
    if not t.get("name"):
        t["name"] = t.get("title", "(無題)")

STATUS_ICONS   = {"open": "⬜", "in_progress": "🔵", "to_verify": "🟡", "closed": "✅"}
PRIORITY_ICONS = {"high": "🔴", "medium": "🟡", "low": "⚪"}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2, "": 3}
STATUSES = ["open", "in_progress", "to_verify", "closed"]

# ── 新規タスク起票 ────────────────────────────────────────────────────────────
with st.expander("➕ 新規タスクを起票", expanded=False):
    with st.form("new_task_form", clear_on_submit=True):
        nt_name = st.text_input("タスク名 *", placeholder="例: ○○機能を実装する")
        nt_col1, nt_col2, nt_col3 = st.columns(3)
        with nt_col1: nt_assignee  = st.selectbox("担当者", ["社長", "会長"])
        with nt_col2: nt_priority  = st.selectbox("優先度", ["high", "medium", "low"], index=1)
        with nt_col3: nt_created_by = st.text_input("起票者", value="ダッシュボード")
        nt_desc = st.text_area("説明", placeholder="タスクの詳細を入力")
        if st.form_submit_button("✅ 起票する", use_container_width=True):
            if not nt_name.strip():
                st.error("タスク名を入力してください")
            else:
                ok, new_id = data_loader.create_task(nt_name.strip(), nt_assignee, nt_priority, nt_desc, nt_created_by)
                if ok:
                    st.success(f"✅ {new_id}「{nt_name}」を起票しました")
                    st.rerun()
                else:
                    st.error("❌ 起票に失敗しました（Firebase接続を確認）")

# ── KPI ──────────────────────────────────────────────────────────────────────
counts = {"open": 0, "in_progress": 0, "to_verify": 0, "closed": 0}
for t in tasks:
    s = t.get("status", "open")
    if s in counts: counts[s] += 1
c1, c2, c3, c4, c5 = st.columns(5)
with c1: st.metric("⬜ Open",    counts["open"])
with c2: st.metric("🔵 進行中",  counts["in_progress"])
with c3:
    tv = counts["to_verify"]
    st.metric("🟡 確認待ち", tv, delta="要対応" if tv >= 5 else None, delta_color="inverse" if tv >= 5 else "normal")
with c4: st.metric("✅ 完了",    counts["closed"])
with c5: st.metric("合計",       len(tasks))
st.divider()

# ── フィルター ────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1: status_filter   = st.selectbox("ステータス", ["すべて"] + STATUSES)
with col2: priority_filter = st.selectbox("優先度", ["すべて", "high", "medium", "low"])
with col3:
    assignees = sorted({t.get("assignee", "") for t in tasks if t.get("assignee")})
    assignee_filter = st.selectbox("担当者", ["すべて"] + assignees)
with col4: search = st.text_input("キーワード検索", placeholder="タイトル・説明")

filtered = tasks
if status_filter   != "すべて": filtered = [t for t in filtered if t.get("status")   == status_filter]
if priority_filter != "すべて": filtered = [t for t in filtered if t.get("priority") == priority_filter]
if assignee_filter != "すべて": filtered = [t for t in filtered if t.get("assignee") == assignee_filter]
if search:
    kw = search.lower()
    filtered = [t for t in filtered if kw in (t.get("name","") + " " + (t.get("description") or "")).lower()]
st.caption(f"表示中: **{len(filtered)} 件** / 全 {len(tasks)} 件")


def task_card(t: dict):
    status    = t.get("status", "open")
    priority  = t.get("priority", "")
    name      = t.get("name", "(無題)")
    assignee  = t.get("assignee", "-")
    task_id   = t.get("id", "")
    desc      = t.get("description") or ""
    result    = t.get("result") or ""
    created   = (t.get("created_at") or "")[:10]
    updated   = (t.get("updated_at") or "")[:10]
    created_by= t.get("created_by", "-")
    comments  = t.get("comments") or []
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
        if desc:   st.markdown("---"); st.markdown(f"**説明:** {desc}")
        if result: st.markdown("---"); st.success(f"**結果:** {result}")
        if comments:
            st.markdown("---")
            st.caption(f"💬 コメント（{len(comments)} 件）")
            for c in (comments[-3:] if isinstance(comments, list) else []):
                if not isinstance(c, dict): continue
                author = c.get("author") or "?"
                text   = c.get("text") or c.get("content") or ""
                ts     = (c.get("created_at") or "")[:10]
                st.markdown(f"**{author}** ({ts}): {text}")
        if not task_id: return
        st.markdown("---"); st.markdown("**✏️ 更新**")
        with st.form(f"edit_{task_id}", clear_on_submit=False):
            ec1, ec2, ec3 = st.columns(3)
            with ec1:
                cur_idx = STATUSES.index(status) if status in STATUSES else 0
                new_status = st.selectbox("ステータス", STATUSES, index=cur_idx, key=f"st_{task_id}")
            with ec2:
                priorities = ["high", "medium", "low", ""]
                cur_p = priorities.index(priority) if priority in priorities else 1
                new_priority = st.selectbox("優先度", priorities[:3], index=min(cur_p, 2), key=f"pr_{task_id}")
            with ec3:
                opts = assignees if assignees else ["社長", "会長"]
                idx  = opts.index(assignee) if assignee in opts else 0
                new_assignee = st.selectbox("担当者", opts, index=idx, key=f"as_{task_id}")
            new_result  = st.text_area("結果（上書き）", value=result, key=f"re_{task_id}", height=80)
            new_comment = st.text_area("コメント追加", placeholder="新しいコメントを入力", key=f"co_{task_id}", height=60)
            if st.form_submit_button("💾 更新する", use_container_width=True):
                updates = {"status": new_status, "priority": new_priority, "assignee": new_assignee, "result": new_result}
                ok = data_loader.update_task(task_id, updates)
                if new_comment.strip() and ok:
                    ok = data_loader.add_task_comment(task_id, "ダッシュボード", new_comment.strip(), comments)
                if ok:
                    st.success("✅ 更新しました"); st.rerun()
                else:
                    st.error("❌ 更新失敗（Firebase接続を確認）")


tab_board, tab_list, tab_assignee = st.tabs(["📌 ボードビュー", "📋 リスト", "👤 担当者別"])

with tab_board:
    board_tasks = filtered if (status_filter != "すべて" or priority_filter != "すべて" or assignee_filter != "すべて" or search) else tasks
    b1, b2, b3, b4 = st.columns(4)
    for col, (label, status) in zip([b1, b2, b3, b4], [("⬜ Open","open"),("🔵 進行中","in_progress"),("🟡 確認待ち","to_verify"),("✅ 完了","closed")]):
        with col:
            group = sorted([t for t in board_tasks if t.get("status") == status], key=lambda t: PRIORITY_ORDER.get(t.get("priority",""),3))
            st.markdown(f"**{label} ({len(group)})**"); st.divider()
            for t in group[:25]:
                p_icon = PRIORITY_ICONS.get(t.get("priority",""),"⚪")
                with st.expander(f"{p_icon} {t.get('name','(無題)')[:28]}", expanded=False):
                    st.caption(f"ID: {t.get('id','')}  担当: {t.get('assignee','')}")
                    if t.get("description"): st.write((t["description"] or "")[:120])
                    if t.get("result"):      st.success((t["result"] or "")[:120])
            if len(group) > 25: st.caption(f"…他 {len(group)-25} 件（リストで全件確認）")

with tab_list:
    sorted_tasks = sorted([t for t in filtered if t.get("status") != "closed"], key=lambda t: PRIORITY_ORDER.get(t.get("priority",""),3)) + \
                   sorted([t for t in filtered if t.get("status") == "closed"], key=lambda t: (t.get("updated_at") or ""), reverse=True)
    for t in sorted_tasks:
        task_card(t)

with tab_assignee:
    for a in assignees:
        group = [t for t in filtered if t.get("assignee") == a]
        if group:
            st.subheader(f"👤 {a}（{len(group)} 件）")
            for t in group[:20]:
                task_card(t)
