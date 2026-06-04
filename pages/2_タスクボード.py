import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, style

st.set_page_config(page_title="🗂️ タスクボード", page_icon="🗂️", layout="wide")
style.inject()

st.markdown("""
<style>
.kb-card{background:white;border-radius:6px;padding:8px 10px;margin-bottom:6px;
         box-shadow:0 1px 3px rgba(0,0,0,.1);border-left:3px solid #ddd;cursor:default}
.kb-card:hover{box-shadow:0 2px 6px rgba(0,0,0,.18)}
.kb-cell{vertical-align:top;padding:8px;min-width:230px;background:#f8f9fa;border-radius:6px}
</style>
""", unsafe_allow_html=True)

tasks = data_loader.kanban_tasks()
for t in tasks:
    if not t.get("name"):
        t["name"] = t.get("title", "(無題)")

PRIORITY_COLORS = {"high": "#6a1b9a", "medium": "#e65100", "low": "#2e7d32"}
PRIORITY_ICONS  = {"high": "⚡", "medium": "🔴", "low": "⚪"}
PRIORITY_ORDER  = {"high": 0, "medium": 1, "low": 2}
STATUSES        = ["open", "in_progress", "to_verify", "closed"]

# ── KPI 集計 ──────────────────────────────────────────────────────────────────
counts = {s: 0 for s in STATUSES}
counts["cancel"] = 0
for t in tasks:
    s = t.get("status", "open")
    if s in counts:
        counts[s] += 1
tv = counts["to_verify"]

# ── ヘッダー（確認待ち過多で warn）────────────────────────────────────────────
style.page_header("🗂️ タスクボード（Kanban）",
                  status="warn" if tv >= 5 else "ok")

# ── KPI（優先度カラー付き section_card）────────────────────────────────────────
style.section_card_start("📋 タスクサマリー")
c1, c2, c3, c4, c5 = st.columns(5)
with c1: st.metric("⬜ Open",    counts["open"])
with c2: st.metric("🔵 進行中",  counts["in_progress"])
with c3:
    style.kpi_wrap_start("warn" if tv >= 5 else "ok")
    st.metric("👀 確認待ち", tv, delta="要対応" if tv >= 5 else None, delta_color="inverse" if tv >= 5 else "normal")
    style.kpi_wrap_end()
with c4: st.metric("✅ 完了",    counts["closed"])
with c5: st.metric("合計",       len(tasks))
style.section_card_end()

# ── セクション絞り込み ────────────────────────────────────────────────────────
sections = sorted({t.get("section", "") for t in tasks if t.get("section", "")})
selected_section = st.pills("セクション", ["すべて"] + sections, default="すべて", key="kb_section")

# ── フィルター適用 ────────────────────────────────────────────────────────────
active = [t for t in tasks if t.get("status") not in ("closed", "cancel", "completed")]
if selected_section and selected_section != "すべて":
    active = [t for t in active if t.get("section", "") == selected_section]
closed_tasks = sorted(
    [t for t in tasks if t.get("status") in ("closed", "completed")],
    key=lambda t: t.get("updated_at", ""), reverse=True
)

st.caption(f"ボード表示: **{len(active)} 件**（open/進行中/確認待ち） | 完了済み: {len(closed_tasks)} 件")

# ── カードHTML生成 ────────────────────────────────────────────────────────────
def make_card(t: dict) -> str:
    tid      = t.get("id", "")
    title    = (t.get("name") or t.get("title") or "(無題)")[:42]
    created  = (t.get("created_at") or "")
    date_str = created[5:10] if len(created) >= 10 else ""
    section  = t.get("section", "")
    assignee = t.get("assignee", "")
    priority = t.get("priority", "")
    border   = PRIORITY_COLORS.get(priority, "#ddd")
    p_icon   = PRIORITY_ICONS.get(priority, "")
    return (
        f'<div class="kb-card" style="border-left-color:{border};border-left-width:4px">'
        f'<div style="font-size:11px;font-weight:700;color:#333;margin-bottom:3px">{title}</div>'
        f'<div style="display:flex;justify-content:space-between;align-items:center">'
        f'<span style="font-size:10px;color:#aaa">{tid} · {date_str}</span>'
        f'<span style="font-size:10px">{p_icon}</span></div>'
        f'<div style="font-size:9px;color:#999;margin-top:2px">{section}</div>'
        f'<div style="font-size:9px;margin-top:2px;color:#2e7d32;font-weight:600">👤 {assignee}</div>'
        f'</div>'
    )

# ── ボードHTML生成 ────────────────────────────────────────────────────────────
STATUS_COLS = [
    ("open",        "🟢 Open",   "#388e3c"),
    ("in_progress", "🔵 進行中", "#1565c0"),
    ("to_verify",   "👀 To Verify", "#6a1b9a"),
]
assignees = ["会長", "社長"]

header_cells = '<th style="width:70px"></th>' + "".join(
    f'<th style="padding:8px 4px;font-size:12px;font-weight:700;color:{color};'
    f'text-align:center;border-bottom:2px solid {color}">{label}</th>'
    for _, label, color in STATUS_COLS
)

rows_html = ""
for assignee in assignees:
    cells = (
        f'<td style="padding:6px 10px 6px 0;white-space:nowrap;vertical-align:top;padding-top:14px">'
        f'<span style="font-size:13px;font-weight:700;color:#333">👤 {assignee}</span></td>'
    )
    for status, _, _ in STATUS_COLS:
        group = sorted(
            [t for t in active if t.get("assignee") == assignee and t.get("status") == status],
            key=lambda t: PRIORITY_ORDER.get(t.get("priority", ""), 3)
        )
        cards_html = "".join(make_card(t) for t in group[:20])
        if len(group) > 20:
            cards_html += f'<div style="font-size:10px;color:#aaa;text-align:center">…他 {len(group)-20} 件</div>'
        cells += f'<td class="kb-cell">{cards_html}</td>'
    rows_html += f"<tr>{cells}</tr>"

board_html = (
    '<div style="overflow-x:auto">'
    '<table style="width:100%;border-collapse:separate;border-spacing:6px">'
    f'<thead><tr>{header_cells}</tr></thead>'
    f'<tbody>{rows_html}</tbody>'
    '</table></div>'
)

# ── タブ ──────────────────────────────────────────────────────────────────────
tab_board, tab_list, tab_new = st.tabs(["📌 ボード", "✏️ 編集・詳細", "➕ 新規起票"])

with tab_board:
    st.markdown(board_html, unsafe_allow_html=True)
    with st.expander(f"✅ 完了済み（{len(closed_tasks)} 件）", expanded=False):
        for t in closed_tasks[:50]:
            st.markdown(make_card(t), unsafe_allow_html=True)
        if len(closed_tasks) > 50:
            st.caption(f"…他 {len(closed_tasks)-50} 件")

with tab_list:
    col1, col2, col3, col4 = st.columns(4)
    with col1: sf = st.selectbox("ステータス", ["すべて"] + STATUSES, key="lf_st")
    with col2: pf = st.selectbox("優先度",    ["すべて", "high", "medium", "low"], key="lf_pr")
    with col3:
        all_assignees = sorted({t.get("assignee","") for t in tasks if t.get("assignee","")})
        af = st.selectbox("担当者", ["すべて"] + all_assignees, key="lf_as")
    with col4: kw = st.text_input("キーワード", placeholder="タイトル・説明", key="lf_kw")

    list_tasks = tasks[:]
    if sf != "すべて": list_tasks = [t for t in list_tasks if t.get("status") == sf]
    if pf != "すべて": list_tasks = [t for t in list_tasks if t.get("priority") == pf]
    if af != "すべて": list_tasks = [t for t in list_tasks if t.get("assignee") == af]
    if kw:
        kw_l = kw.lower()
        list_tasks = [t for t in list_tasks if kw_l in (t.get("name","") + " " + (t.get("description") or "")).lower()]
    list_tasks = sorted([t for t in list_tasks if t.get("status") != "closed"],
                        key=lambda t: PRIORITY_ORDER.get(t.get("priority",""), 3)) + \
                 sorted([t for t in list_tasks if t.get("status") == "closed"],
                        key=lambda t: t.get("updated_at",""), reverse=True)
    st.caption(f"表示: **{len(list_tasks)} 件**")

    for t in list_tasks:
        status   = t.get("status", "open")
        priority = t.get("priority", "")
        name     = t.get("name", "(無題)")
        assignee = t.get("assignee", "-")
        task_id  = t.get("id", "")
        s_icon   = {"open":"⬜","in_progress":"🔵","to_verify":"👀","closed":"✅"}.get(status,"⬜")
        p_icon   = PRIORITY_ICONS.get(priority, "⚪")
        with st.expander(f"{s_icon} {p_icon} **{name}** — 👤 {assignee}", expanded=False):
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                st.write(f"**ID:** `{task_id}`")
                st.write(f"**ステータス:** {status}")
                st.write(f"**優先度:** {priority or '-'}")
            with mc2:
                st.write(f"**担当者:** {assignee}")
                st.write(f"**起票者:** {t.get('created_by','-')}")
            with mc3:
                st.write(f"**作成:** {(t.get('created_at') or '')[:10] or '-'}")
                st.write(f"**更新:** {(t.get('updated_at') or '')[:10] or '-'}")
            if t.get("description"):
                st.markdown("---"); st.markdown(f"**説明:** {t['description']}")
            if t.get("result"):
                st.markdown("---"); st.success(f"**結果:** {t['result']}")
            comments = t.get("comments") or []
            if comments:
                st.markdown("---"); st.caption(f"💬 コメント（{len(comments)} 件）")
                for c in (comments[-3:] if isinstance(comments, list) else []):
                    if not isinstance(c, dict): continue
                    st.markdown(f"**{c.get('author','?')}** ({(c.get('created_at') or '')[:10]}): {c.get('text') or c.get('content','')}")
            if not task_id: continue
            st.markdown("---"); st.markdown("**✏️ 更新**")
            with st.form(f"edit_{task_id}", clear_on_submit=False):
                ec1, ec2, ec3 = st.columns(3)
                with ec1:
                    new_status = st.selectbox("ステータス", STATUSES,
                                              index=STATUSES.index(status) if status in STATUSES else 0,
                                              key=f"st_{task_id}")
                with ec2:
                    priorities = ["high", "medium", "low"]
                    new_priority = st.selectbox("優先度", priorities,
                                                index=priorities.index(priority) if priority in priorities else 1,
                                                key=f"pr_{task_id}")
                with ec3:
                    opts = all_assignees if all_assignees else ["社長", "会長"]
                    new_assignee = st.selectbox("担当者", opts,
                                                index=opts.index(assignee) if assignee in opts else 0,
                                                key=f"as_{task_id}")
                new_result  = st.text_area("結果（上書き）", value=t.get("result") or "", key=f"re_{task_id}", height=80)
                new_comment = st.text_area("コメント追加", placeholder="新しいコメントを入力", key=f"co_{task_id}", height=60)
                if st.form_submit_button("💾 更新する", use_container_width=True):
                    ok = data_loader.update_task(task_id, {"status": new_status, "priority": new_priority,
                                                           "assignee": new_assignee, "result": new_result})
                    if new_comment.strip() and ok:
                        ok = data_loader.add_task_comment(task_id, "ダッシュボード", new_comment.strip(), comments)
                    if ok:
                        st.success("✅ 更新しました"); st.rerun()
                    else:
                        st.error("❌ 更新失敗（Firebase接続を確認）")

with tab_new:
    with st.form("new_task_form", clear_on_submit=True):
        nt_name = st.text_input("タスク名 *", placeholder="例: ○○機能を実装する")
        nc1, nc2, nc3 = st.columns(3)
        with nc1: nt_assignee   = st.selectbox("担当者", ["社長", "会長"])
        with nc2: nt_priority   = st.selectbox("優先度", ["high", "medium", "low"], index=1)
        with nc3: nt_created_by = st.text_input("起票者", value="ダッシュボード")
        nt_desc = st.text_area("説明", placeholder="タスクの詳細を入力")
        if st.form_submit_button("✅ 起票する", use_container_width=True):
            if not nt_name.strip():
                st.error("タスク名を入力してください")
            else:
                ok, new_id = data_loader.create_task(nt_name.strip(), nt_assignee, nt_priority, nt_desc, nt_created_by)
                if ok:
                    st.success(f"✅ {new_id}「{nt_name}」を起票しました"); st.rerun()
                else:
                    st.error("❌ 起票に失敗しました（Firebase接続を確認）")
