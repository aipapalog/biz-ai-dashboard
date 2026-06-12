import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, style
from utils.data_loader import get_push_log
from utils.style import freshness_banner

st.set_page_config(page_title="タスク", page_icon="✅", layout="wide")
style.inject()

st.markdown("""
<style>
.kb-card{background:white;border-radius:6px;padding:8px 10px;margin-bottom:6px;
         box-shadow:0 1px 3px rgba(0,0,0,.1);border-left:3px solid #ddd;cursor:default}
.kb-card:hover{box-shadow:0 2px 6px rgba(0,0,0,.18)}
.kb-cell{vertical-align:top;padding:8px;min-width:230px;background:#f8f9fa;border-radius:6px}
</style>
""", unsafe_allow_html=True)

# 鮮度バナー
_push_log = get_push_log()
st.markdown(
    f'<div style="text-align:right;margin-bottom:4px;">{freshness_banner(_push_log)}</div>',
    unsafe_allow_html=True
)

st.title("✅ タスク管理")

tab1, tab2 = st.tabs(["🚨 要対応", "📋 タスクボード"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: 要対応
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    import re as _re

    # ── データ取得 ─────────────────────────────────────────────────────────────
    ks       = data_loader.kanban_summary()
    pl       = data_loader.pipeline_status()
    risk     = data_loader.risk_report()
    cx       = data_loader.cx_report()
    budget   = data_loader.api_budget()
    health   = data_loader.health_check()
    biz      = data_loader.business_status()
    sys_info = data_loader.system_info()
    ch       = data_loader.code_health()
    bt       = data_loader.bizdev_trend()

    # ── 集計・判定 ─────────────────────────────────────────────────────────────
    counts_pl = pl.get("counts", {}) if pl else {}
    fail_n    = counts_pl.get("failed", 0)
    tv        = ks.get("to_verify", 0) if ks else 0

    def _extract_count(text, *patterns):
        """レポート本文から「○○: N件」形式の件数を抽出する。見つからなければ 0。"""
        for pat in patterns:
            m = _re.search(pat, text or "")
            if m:
                try:
                    return int(m.group(1))
                except (ValueError, IndexError):
                    continue
        return 0

    risk_txt    = (risk.get("content", "") or "") if risk else ""
    cx_txt      = (cx.get("content", "") or "") if cx else ""
    risk_high_n = _extract_count(risk_txt, r"High[:：]\s*(\d+)\s*件", r"High[:：]\s*(\d+)")
    cx_fail_n   = _extract_count(cx_txt, r"fail（要改善）[:：]\s*(\d+)\s*件", r"要改善[:：]\s*(\d+)\s*件")
    risk_high   = risk_high_n > 0
    cx_issue    = cx_fail_n > 0

    used_api  = budget.get("used_usd", (budget.get("anthropic", {}) or {}).get("used_usd", 0)) if budget else 0
    lim_api   = budget.get("budget_usd", (budget.get("anthropic", {}) or {}).get("budget_usd", 0)) if budget else 0
    api_ratio = (used_api / lim_api) if lim_api else 0

    issues    = ch.get("issues", []) if ch else []
    high_iss  = [x for x in issues if isinstance(x, dict) and x.get("severity") in ("high", "critical")]
    health_ok = health and "error" not in (health.get("content", "") or "").lower()[:200]

    ssid  = str(sys_info.get("ssid", "")) if sys_info else ""
    is_co = "SWing" in ssid

    # 致命度の高い順に「要対応アラート」を組み立てる
    alerts = []   # (重要度: "critical"/"warn", 文言, 誘導先ページ)
    if is_co:
        alerts.append(("critical", "🏢 会社ネットワーク接続中 — エージェント・パイプラインは自動停止します", "📊 稼働状況"))
    if fail_n:
        alerts.append(("critical", f"⚙️ パイプライン失敗 {fail_n} 本 — ログを確認してください", "📊 稼働状況"))
    if risk_high:
        alerts.append(("critical", f"⚠️ Highリスク {risk_high_n} 件 — リスクレポートを確認してください", "😊 CX・品質"))
    if api_ratio > 0.8:
        alerts.append(("critical", f"💰 API予算 {api_ratio*100:.0f}% 消費 — 呼び出し削減が急務", "😊 CX・品質"))
    if high_iss:
        alerts.append(("warn", f"🔴 コード高度問題 {len(high_iss)} 件", "😊 CX・品質"))
    if cx_issue:
        alerts.append(("warn", f"🎯 CX要改善 {cx_fail_n} 件", "😊 CX・品質"))
    if api_ratio > 0.5 and api_ratio <= 0.8:
        alerts.append(("warn", f"💰 API予算 {api_ratio*100:.0f}% 消費", "😊 CX・品質"))

    n_critical = (risk_high_n if risk_high else 0) + fail_n + (1 if api_ratio > 0.8 else 0) + (1 if is_co else 0)
    n_warn     = cx_fail_n + len(high_iss) + (1 if 0.5 < api_ratio <= 0.8 else 0)
    hdr_status = "err" if n_critical else ("warn" if n_warn or tv >= 5 else "ok")

    style.page_header("🚨 要対応サマリー",
                      subtitle="今すぐ判断・対応が必要な項目だけを集約",
                      updated=data_loader.last_updated(),
                      status=hdr_status)

    # ── 要対応カウント ────────────────────────────────────────────────────────
    style.section_card_start("🚦 対応必要件数",
                             "要対応あり" if (n_critical or n_warn or tv >= 5) else "クリア",
                             "err" if n_critical else ("warn" if (n_warn or tv >= 5) else "ok"))
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        style.kpi_wrap_start("critical" if n_critical else "ok")
        st.metric("🔴 緊急（実件数）", n_critical)
        style.kpi_wrap_end()
    with c2:
        style.kpi_wrap_start("warn" if n_warn else "ok")
        st.metric("🟡 要確認（実件数）", n_warn)
        style.kpi_wrap_end()
    with c3:
        style.kpi_wrap_start("warn" if tv >= 5 else "ok")
        st.metric("👀 確認待ちタスク", tv)
        style.kpi_wrap_end()
    with c4:
        style.kpi_wrap_start("critical" if fail_n else "ok")
        st.metric("❌ 失敗パイプライン", fail_n)
        style.kpi_wrap_end()
    style.section_card_end()

    # ── アラート一覧 ──────────────────────────────────────────────────────────
    style.section_card_start("📣 アラート",
                             f"{len(alerts)}件" if alerts else "なし",
                             "err" if n_critical else ("warn" if (alerts or tv >= 5) else "ok"))
    if not alerts:
        st.success("✅ 現在、緊急の対応が必要な項目はありません。")
    else:
        crit  = [a for a in alerts if a[0] == "critical"][:3]
        warns = [a for a in alerts if a[0] == "warn"][:3]
        for _, msg, dest in crit:
            st.error(f"{msg}　→ **{dest}** ページへ")
        for _, msg, dest in warns:
            st.warning(f"{msg}　→ **{dest}** ページへ")
        extra = len(alerts) - len(crit) - len(warns)
        if extra > 0:
            st.caption(f"…他 {extra} 件（各ページで詳細を確認）")
    style.section_card_end()

    # ── 確認待ちタスク ────────────────────────────────────────────────────────
    verify_top5 = (ks.get("verify_top5") or []) if ks else []
    active_top5 = (ks.get("active_top5") or []) if ks else []
    lcol, rcol = st.columns(2)
    with lcol:
        style.section_card_start("👀 確認待ちタスク",
                                 "要対応" if tv >= 5 else "",
                                 "warn" if tv >= 5 else "info")
        if verify_top5:
            for t in verify_top5[:5]:
                st.write(f"• `{t.get('id','')}` {str(t.get('name',''))[:120]} — {t.get('assignee','')}")
            st.caption("→ 「📋 タスクボード」タブで承認・差し戻し")
        else:
            st.info("確認待ちのタスクはありません")
        style.section_card_end()
    with rcol:
        style.section_card_start("🔵 進行中タスク")
        if active_top5:
            for t in active_top5[:5]:
                st.write(f"• `{t.get('id','')}` {str(t.get('name',''))[:120]} — {t.get('assignee','')}")
        else:
            st.info("進行中のタスクはありません")
        style.section_card_end()

    # ── 収益・予算スナップショット ────────────────────────────────────────────
    monthly_actual = int(biz.get("monthly_actual", 0)) if biz else 0
    monthly_target = int(biz.get("monthly_target", 20000)) if biz else 20000
    prog = (monthly_actual / monthly_target) if monthly_target else 0
    style.section_card_start("📊 収益・予算スナップショット")
    m1, m2, m3 = st.columns(3)
    with m1:
        style.kpi_wrap_start("ok" if prog >= 0.8 else "warn" if prog >= 0.3 else "critical")
        st.metric("💰 今月収益", f"¥{monthly_actual:,}",
                  f"目標比 {round(prog*100)}%")
        style.kpi_wrap_end()
    with m2:
        style.kpi_wrap_start("critical" if api_ratio > 0.8 else "warn" if api_ratio > 0.5 else "ok")
        st.metric("🪙 API消費", f"${used_api:.3f}", help=f"予算 ${lim_api}")
        style.kpi_wrap_end()
    with m3:
        st.metric("🩺 ヘルス", "OK" if health_ok else "要確認")
    st.caption("詳細は「💼 事業状況」「😊 CX・品質」ページで確認できます")
    style.section_card_end()

    # ── Bizdevスコア推移 ──────────────────────────────────────────────────────
    entries = bt.get("entries", []) if bt else []
    style.section_card_start("📈 Bizdevスコア推移")
    if entries:
        import pandas as pd
        avg = round(sum(e.get("score", 0) for e in entries) / len(entries), 1)
        st.metric("平均スコア", f"{avg}/10", help=f"累計 {len(entries)} アイデア")
        df = pd.DataFrame(entries)
        if "date" in df.columns and "score" in df.columns:
            df_chart = df.groupby("date")["score"].mean().reset_index()
            df_chart.columns = ["日付", "平均スコア"]
            st.line_chart(df_chart.set_index("日付"))
        st.caption("→ 高スコア候補は「💡 BizDev」ページで確認")
    else:
        st.info("Bizdevスコアデータがありません")
    style.section_card_end()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: タスクボード
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    tasks = data_loader.kanban_tasks()
    for t in tasks:
        if not t.get("name"):
            t["name"] = t.get("title", "(無題)")

    PRIORITY_COLORS = {"high": "#6a1b9a", "medium": "#e65100", "low": "#2e7d32"}
    PRIORITY_ICONS  = {"high": "⚡", "medium": "🔴", "low": "⚪"}
    PRIORITY_ORDER  = {"high": 0, "medium": 1, "low": 2}
    STATUSES        = ["open", "in_progress", "to_verify", "closed"]

    # ── KPI 集計 ──────────────────────────────────────────────────────────────
    counts_kb = {s: 0 for s in STATUSES}
    counts_kb["cancel"] = 0
    for t in tasks:
        s = t.get("status", "open")
        if s in counts_kb:
            counts_kb[s] += 1
    tv_kb = counts_kb["to_verify"]

    # ── ヘッダー ──────────────────────────────────────────────────────────────
    style.page_header("🗂️ タスクボード（Kanban）",
                      updated=data_loader.last_updated(),
                      status="warn" if tv_kb >= 5 else "ok")

    # ── KPI ───────────────────────────────────────────────────────────────────
    style.section_card_start("📋 タスクサマリー")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("⬜ Open",    counts_kb["open"])
    with c2: st.metric("🔵 進行中",  counts_kb["in_progress"])
    with c3:
        style.kpi_wrap_start("warn" if tv_kb >= 5 else "ok")
        st.metric("👀 確認待ち", tv_kb, delta="要対応" if tv_kb >= 5 else None, delta_color="inverse" if tv_kb >= 5 else "normal")
        style.kpi_wrap_end()
    with c4: st.metric("✅ 完了",    counts_kb["closed"])
    with c5: st.metric("合計",       len(tasks))
    style.section_card_end()

    # ── セクション絞り込み ────────────────────────────────────────────────────
    sections = sorted({t.get("section", "") for t in tasks if t.get("section", "")})
    selected_section = st.pills("セクション", ["すべて"] + sections, default="すべて", key="kb_section")

    # ── フィルター適用 ────────────────────────────────────────────────────────
    active_kb = [t for t in tasks if t.get("status") not in ("closed", "cancel", "completed")]
    if selected_section and selected_section != "すべて":
        active_kb = [t for t in active_kb if t.get("section", "") == selected_section]
    closed_tasks = sorted(
        [t for t in tasks if t.get("status") in ("closed", "completed")],
        key=lambda t: t.get("updated_at", ""), reverse=True
    )

    st.caption(f"ボード表示: **{len(active_kb)} 件**（open/進行中/確認待ち） | 完了済み: {len(closed_tasks)} 件")

    # ── カードHTML生成 ────────────────────────────────────────────────────────
    def make_card(t: dict) -> str:
        tid      = t.get("id", "")
        title    = (t.get("name") or t.get("title") or "(無題)")
        created  = (t.get("created_at") or "")
        date_str = created[5:10] if len(created) >= 10 else ""
        section  = t.get("section", "")
        assignee = t.get("assignee", "")
        priority = t.get("priority", "")
        border   = PRIORITY_COLORS.get(priority, "#ddd")
        p_icon   = PRIORITY_ICONS.get(priority, "")
        return (
            f'<div class="kb-card" style="border-left-color:{border};border-left-width:4px">'
            f'<div style="font-size:11px;font-weight:700;color:#333;margin-bottom:3px;word-break:break-all">{title}</div>'
            f'<div style="display:flex;justify-content:space-between;align-items:center">'
            f'<span style="font-size:10px;color:#aaa">{tid} · {date_str}</span>'
            f'<span style="font-size:10px">{p_icon}</span></div>'
            f'<div style="font-size:9px;color:#999;margin-top:2px">{section}</div>'
            f'<div style="font-size:9px;margin-top:2px;color:#2e7d32;font-weight:600">👤 {assignee}</div>'
            f'</div>'
        )

    # ── ボードHTML生成 ────────────────────────────────────────────────────────
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
                [t for t in active_kb if t.get("assignee") == assignee and t.get("status") == status],
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

    # ── タブ ──────────────────────────────────────────────────────────────────
    tab_board, tab_list, tab_new = st.tabs(["📌 ボード", "✏️ 編集・詳細", "➕ 新規起票"])

    def _show_task_detail(t: dict, all_assignees: list, form_prefix: str = "bd"):
        """タスク詳細表示＋編集フォーム（board/listタブ共用）"""
        task_id  = t.get("id", "")
        status   = t.get("status", "open")
        priority = t.get("priority", "")
        assignee = t.get("assignee", "-")
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
        if not task_id: return
        st.markdown("---"); st.markdown("**✏️ 更新**")
        opts = all_assignees if all_assignees else ["社長", "会長"]
        with st.form(f"{form_prefix}_edit_{task_id}", clear_on_submit=False):
            ec1, ec2, ec3 = st.columns(3)
            with ec1:
                new_status = st.selectbox("ステータス", STATUSES,
                                          index=STATUSES.index(status) if status in STATUSES else 0,
                                          key=f"{form_prefix}_st_{task_id}")
            with ec2:
                priorities = ["high", "medium", "low"]
                new_priority = st.selectbox("優先度", priorities,
                                            index=priorities.index(priority) if priority in priorities else 1,
                                            key=f"{form_prefix}_pr_{task_id}")
            with ec3:
                new_assignee = st.selectbox("担当者", opts,
                                            index=opts.index(assignee) if assignee in opts else 0,
                                            key=f"{form_prefix}_as_{task_id}")
            new_result  = st.text_area("結果（上書き）", value=t.get("result") or "", key=f"{form_prefix}_re_{task_id}", height=80)
            new_comment = st.text_area("コメント追加", placeholder="新しいコメントを入力", key=f"{form_prefix}_co_{task_id}", height=60)
            if st.form_submit_button("💾 更新する", use_container_width=True):
                ok = data_loader.update_task(task_id, {"status": new_status, "priority": new_priority,
                                                       "assignee": new_assignee, "result": new_result})
                if new_comment.strip() and ok:
                    ok = data_loader.add_task_comment(task_id, "ダッシュボード", new_comment.strip(), comments)
                if ok:
                    st.success("✅ 更新しました"); st.rerun()
                else:
                    st.error("❌ 更新失敗（Firebase接続を確認）")

    _all_assignees_global = sorted({t.get("assignee","") for t in tasks if t.get("assignee","")})

    with tab_board:
        st.markdown(board_html, unsafe_allow_html=True)

        # ── タスク詳細パネル ──────────────────────────────────────────────────
        st.divider()
        st.markdown("#### 🔍 タスク詳細を開く")
        board_opts_map = {
            f"{t.get('id','')} [{t.get('status','')}] {(t.get('name') or t.get('title',''))[:80]}": t
            for t in sorted(active_kb, key=lambda x: (x.get("assignee",""), x.get("status",""), PRIORITY_ORDER.get(x.get("priority",""),3)))
        }
        sel_label = st.selectbox("タスクを選択", ["（選択してください）"] + list(board_opts_map.keys()), key="bd_sel_task")
        if sel_label != "（選択してください）" and sel_label in board_opts_map:
            with st.container(border=True):
                _show_task_detail(board_opts_map[sel_label], _all_assignees_global, form_prefix="bd")

        with st.expander(f"✅ 完了済み（{len(closed_tasks)} 件）", expanded=False):
            for t in closed_tasks[:50]:
                st.markdown(make_card(t), unsafe_allow_html=True)
            if len(closed_tasks) > 50:
                st.caption(f"…他 {len(closed_tasks)-50} 件")

    with tab_list:
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
        with col1: sf = st.selectbox("ステータス", ["すべて"] + STATUSES, key="lf_st")
        with col2: pf = st.selectbox("優先度",    ["すべて", "high", "medium", "low"], key="lf_pr")
        with col3:
            all_assignees = _all_assignees_global
            af = st.selectbox("担当者", ["すべて"] + all_assignees, key="lf_as")
        with col4: kw = st.text_input("キーワード", placeholder="タイトル・説明", key="lf_kw")
        with col5: sort_by = st.selectbox("ソート", ["優先度", "セクション", "作成日↑", "作成日↓", "更新日↓"], key="lf_sort")

        list_tasks = tasks[:]
        if sf != "すべて": list_tasks = [t for t in list_tasks if t.get("status") == sf]
        if pf != "すべて": list_tasks = [t for t in list_tasks if t.get("priority") == pf]
        if af != "すべて": list_tasks = [t for t in list_tasks if t.get("assignee") == af]
        if kw:
            kw_l = kw.lower()
            list_tasks = [t for t in list_tasks if kw_l in (t.get("name","") + " " + (t.get("description") or "")).lower()]

        if sort_by == "セクション":
            list_tasks = sorted(list_tasks, key=lambda t: (t.get("section",""), PRIORITY_ORDER.get(t.get("priority",""), 3)))
        elif sort_by == "作成日↑":
            list_tasks = sorted(list_tasks, key=lambda t: t.get("created_at",""))
        elif sort_by == "作成日↓":
            list_tasks = sorted(list_tasks, key=lambda t: t.get("created_at",""), reverse=True)
        elif sort_by == "更新日↓":
            list_tasks = sorted(list_tasks, key=lambda t: t.get("updated_at",""), reverse=True)
        else:  # 優先度（デフォルト）
            list_tasks = sorted([t for t in list_tasks if t.get("status") != "closed"],
                                key=lambda t: PRIORITY_ORDER.get(t.get("priority",""), 3)) + \
                         sorted([t for t in list_tasks if t.get("status") == "closed"],
                                key=lambda t: t.get("updated_at",""), reverse=True)
        st.caption(f"表示: **{len(list_tasks)} 件**")

        prev_section = None
        for t in list_tasks:
            status   = t.get("status", "open")
            priority = t.get("priority", "")
            name     = t.get("name", "(無題)")
            assignee = t.get("assignee", "-")
            task_id  = t.get("id", "")
            section  = t.get("section", "")
            s_icon   = {"open":"⬜","in_progress":"🔵","to_verify":"👀","closed":"✅"}.get(status,"⬜")
            p_icon   = PRIORITY_ICONS.get(priority, "⚪")
            if sort_by == "セクション" and section != prev_section:
                st.markdown(f"##### 📂 {section or '未分類'}")
                prev_section = section
            with st.expander(f"{s_icon} {p_icon} **{name}** — 👤 {assignee}", expanded=False):
                _show_task_detail(t, all_assignees, form_prefix="ls")

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
