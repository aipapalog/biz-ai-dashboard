import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, style

st.set_page_config(page_title="💼 事業状況", page_icon="💼", layout="wide")
style.inject()

biz          = data_loader.business_status()
pf           = data_loader.pf_watch()
funnel       = data_loader.funnel()
pdca_data    = data_loader.pdca()
pdca_reports = data_loader.biz_pdca_reports()

# ── ヘッダー（収益進捗で色分け）────────────────────────────────────────────────
_monthly_actual = biz.get("monthly_actual", 0) if biz else 0
_monthly_target = biz.get("monthly_target", 20000) if biz else 20000
_prog = (_monthly_actual / _monthly_target) if _monthly_target else 0
_hdr_status = "ok" if _prog >= 0.8 else "warn" if _prog >= 0.3 else "err"
style.page_header("💼 事業状況・経営目標・利益予測", updated=data_loader.last_updated(), status=_hdr_status)

# ── タブ構成（事業状況／ファネル／PDCA）────────────────────────────────────────
tab_biz, tab_funnel, tab_pdca = st.tabs(["💼 事業状況", "🔀 ファネル", "🔄 PDCA"])

# ══════════════════════════════════════════════════════════════════════════════
# 💼 事業状況
# ══════════════════════════════════════════════════════════════════════════════
with tab_biz:
    if not biz:
        st.info("business_status.json が読み込めていません。")
    else:
        goal           = biz.get("management_goal", {})
        forecast       = biz.get("management_forecast", {})
        products       = biz.get("products", [])
        web_assets     = biz.get("web_assets", [])
        expenses       = biz.get("expenses", [])
        monthly_actual = biz.get("monthly_actual", 0)
        monthly_target = biz.get("monthly_target", 20000)
        annual_target  = biz.get("annual_target", 300000)
        biz_note       = biz.get("note", "")

        # ── 経営目標 ──────────────────────────────────────────────────────────
        style.section_card_start("🎯 経営目標")
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("**短期目標**")
            st.write(goal.get("short", "未設定"))
        with g2:
            st.markdown("**長期目標**")
            st.write(goal.get("long", "未設定"))
        style.section_card_end()

        # ── 収益進捗・予測 ────────────────────────────────────────────────────
        prog_pct = min(monthly_actual / monthly_target * 100, 100) if monthly_target else 0
        prog_icon = "🟢" if prog_pct >= 80 else "🟡" if prog_pct >= 30 else "🔴"
        prog_prio = "ok" if prog_pct >= 80 else "warn" if prog_pct >= 30 else "critical"
        style.section_card_start("📈 収益進捗・予測")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            style.kpi_wrap_start(prog_prio)
            st.metric("今月実績", f"¥{monthly_actual:,}", help=f"目標: ¥{monthly_target:,}")
            style.kpi_wrap_end()
        with c2: st.metric("月次目標", f"¥{monthly_target:,}")
        with c3: st.metric("年次目標", f"¥{annual_target:,}")
        with c4:
            fixed  = sum(e.get("amount_jpy", 0) for e in expenses if e.get("cycle") == "monthly")
            profit = monthly_actual - fixed
            style.kpi_wrap_start("ok" if profit >= 0 else "critical")
            st.metric("利益（今月）", f"¥{profit:,}", help=f"固定費: ¥{fixed:,}")
            style.kpi_wrap_end()
        st.progress(prog_pct / 100, text=f"{prog_icon} 月次進捗: {prog_pct:.1f}%")

        fc_monthly = forecast.get("monthly_forecast_jpy", 0)
        fc_annual  = forecast.get("annual_forecast_jpy", 0)
        fc_note    = forecast.get("note", "")
        if fc_monthly or fc_annual:
            p1, p2 = st.columns(2)
            with p1: st.metric("月次収益予測", f"¥{fc_monthly:,}" if isinstance(fc_monthly, (int, float)) else str(fc_monthly))
            with p2: st.metric("年次収益予測", f"¥{fc_annual:,}"  if isinstance(fc_annual,  (int, float)) else str(fc_annual))
            if fc_note: st.caption(fc_note)
        if biz_note: st.info(biz_note)
        style.section_card_end()

        # ── 製品一覧 ──────────────────────────────────────────────────────────
        style.section_card_start("📦 製品一覧")
        if products:
            for p in products:
                status = p.get("status", "?")
                icon   = "🟢" if status in ("公開中", "active") else ("🟡" if status in ("審査中", "審査待ち", "pending") else "🔴")
                rev    = p.get("monthly_revenue", 0)
                with st.expander(f"{icon} **{p.get('name','?')}** — {p.get('platform','-')}  ¥{rev:,}/月"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        price = p.get("price_jpy", 0)
                        st.metric("価格", f"¥{price:,}" if isinstance(price, (int, float)) else str(price))
                    with c2:
                        st.metric("月次収益", f"¥{rev:,}" if isinstance(rev, (int, float)) else str(rev))
                    with c3:
                        st.write(f"**ステータス:** {status}")
                    if p.get("blocker"): st.warning(f"⏳ {p['blocker']}")
                    if p.get("todo"):    st.info(f"★ {p['todo']}")
        else:
            st.info("製品データなし")
        style.section_card_end()

        # ── ウェブ資産 ────────────────────────────────────────────────────────
        if web_assets:
            style.section_card_start("🌐 ウェブ資産")
            for a in web_assets:
                s    = a.get("status", "")
                icon = "🟢" if s == "公開中" else "🔴"
                url  = a.get("url", "")
                note = a.get("note", "")
                line = f"{icon} **{a.get('name','')}** ({a.get('platform','')}) — {s}"
                if url:  line += f"  [{url}]({url})"
                if note: line += f"  _{note}_"
                st.markdown(line)
            style.section_card_end()

        # ── 経費一覧 ──────────────────────────────────────────────────────────
        if expenses:
            style.section_card_start("💸 経費一覧")
            for e in expenses:
                cycle = {"monthly": "月額固定", "per_sale": "売上時のみ"}.get(e.get("cycle", ""), e.get("cycle", ""))
                amt   = e.get("amount_jpy", 0)
                st.write(f"• **{e.get('name','')}** {cycle} ¥{amt:,}  {e.get('note','')}")
            style.section_card_end()

        # ── プラットフォーム監視 ──────────────────────────────────────────────
        style.section_card_start("🔍 プラットフォーム監視（待ち状態）")
        if pf:
            # pf_watch ドキュメントは services リストを持つ（watches は旧キー）
            watches = pf.get("services") or pf.get("watches") or []
            if isinstance(watches, dict): watches = list(watches.values())
            if isinstance(watches, list) and watches:
                def _pf_icon(s):
                    return "✅" if s in ("ok", "active", "normal", "completed") else "⏳" if s == "pending" else "❌"
                cols = st.columns(min(len(watches), 4))
                for i, item in enumerate(watches[:4]):
                    if not isinstance(item, dict): continue
                    plat   = item.get("platform", item.get("name", "?"))
                    status = item.get("status", "?")
                    with cols[i % 4]:
                        st.metric(f"{_pf_icon(status)} {plat}", status)
                for item in watches[4:]:
                    if isinstance(item, dict):
                        plat   = item.get("platform", item.get("name", "?"))
                        status = item.get("status", "?")
                        st.write(f"{_pf_icon(status)} **{plat}**: {status}")
            else:
                for k, v in (pf.items() if isinstance(pf, dict) else []):
                    if isinstance(v, dict):
                        st.write(f"• **{k}**: {v.get('status', '?')}")
        else:
            st.info("プラットフォームデータなし")
        style.section_card_end()

# ══════════════════════════════════════════════════════════════════════════════
# 🔀 ファネル（旧 5_ファネル.py の内容）
# ══════════════════════════════════════════════════════════════════════════════
with tab_funnel:
    if not funnel:
        st.info("ファネルデータがありません。funnel_metrics.json の実データ収集パイプライン未稼働。")
    else:
        st.caption(f"最終更新: {funnel.get('last_updated', '-')[:16]}")
        warn = funnel.get("warning")
        if warn:
            # warning は dict（message/implementation_status 等）または文字列
            if isinstance(warn, dict):
                msg = warn.get("message", "ファネルメトリクスは参考値です")
                st.info(f"ℹ️ {msg}")
                details = warn.get("details", "")
                if details:
                    st.caption(details)
                impl = warn.get("implementation_status", {})
                if isinstance(impl, dict) and impl:
                    with st.expander("📋 各メトリクスのデータ収集状況", expanded=False):
                        LABELS = {
                            "note_views":          "note記事ビュー数",
                            "purchase_data":       "購入データ",
                            "checkout_data":       "チェックアウトデータ",
                            "product_page_clicks": "製品ページクリック",
                        }
                        for k, v in impl.items():
                            # 「❌ 取得不可」等を「近日対応予定」に置換してユーザーを不安にさせない
                            label = LABELS.get(k, k)
                            state = "🟡 近日対応予定（外部API連携待ち）" if "❌" in str(v) else str(v)
                            st.write(f"• **{label}**: {state}")
            else:
                st.info(f"ℹ️ {warn}")

        # ── ステップ別メトリクス ───────────────────────────────────────────────
        metrics = funnel.get("metrics", {})
        if metrics:
            style.section_card_start("🎯 ファネルステップ")
            step_names = {
                "note_article_views":   "①記事閲覧",
                "product_page_clicks":  "②製品ページCTR",
                "product_page_views":   "③製品ページ閲覧",
                "checkout_page_views":  "④チェックアウト",
                "purchase_completed":   "⑤購入完了",
            }
            cols = st.columns(len(step_names))
            for col, (key, label) in zip(cols, step_names.items()):
                with col:
                    val = metrics.get(key, 0)
                    st.metric(label, f"{val:,}")
            style.section_card_end()

        # ── 脱落率 ────────────────────────────────────────────────────────────
        dropoff = funnel.get("dropoff_analysis", {})
        if dropoff:
            style.section_card_start("📉 ステップ間 脱落率")
            DROPOFF_LABELS = {
                "note_to_product":      "①記事 → ②製品ページ",
                "product_to_checkout":  "②製品ページ → ③チェックアウト",
                "checkout_to_purchase": "③チェックアウト → ④購入完了",
            }
            for step, rate in dropoff.items():
                pct = rate if isinstance(rate, (int, float)) else 0
                color = "🔴" if pct > 80 else "🟡" if pct > 50 else "🟢"
                label = DROPOFF_LABELS.get(step, step)
                st.write(f"{color} **{label}**: {pct:.1f}% 脱落")
            style.section_card_end()

        # ── プラットフォーム別 ────────────────────────────────────────────────
        platform = funnel.get("platform_breakdown", {})
        if platform:
            style.section_card_start("🛒 プラットフォーム別")
            import pandas as pd
            rows = []
            for p_name, p_data in platform.items():
                if isinstance(p_data, dict):
                    rows.append({"プラットフォーム": p_name, **p_data})
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True)
            style.section_card_end()

        # ── 日次推移 ──────────────────────────────────────────────────────────
        daily = funnel.get("daily_records", [])
        if daily:
            style.section_card_start("📅 日次推移（直近14日）")
            import pandas as pd
            rows = []
            for d in daily:
                if isinstance(d, dict):
                    steps = d.get("steps", d)
                    rows.append({
                        "日付": d.get("date", ""),
                        "記事閲覧": steps.get("note_article_views", 0),
                        "製品ページ": steps.get("product_page_views", 0),
                        "購入": steps.get("purchase_completed", 0),
                    })
            if rows:
                df = pd.DataFrame(rows)
                st.line_chart(df.set_index("日付"))
                st.dataframe(df, use_container_width=True)
            style.section_card_end()

# ══════════════════════════════════════════════════════════════════════════════
# 🔄 PDCA（旧 6_PDCA.py の内容）
# ══════════════════════════════════════════════════════════════════════════════
with tab_pdca:
    st.caption("戦略立案 — 施策立案→評価→task_queue追加→自律ループが実行")

    # ── 月次PDCA最新 ──────────────────────────────────────────────────────────
    style.section_card_start("📈 月次PDCA（最新）")
    if pdca_data:
        latest = pdca_data.get("pdca_latest", {})
        if latest:
            c1, c2, c3 = st.columns(3)
            with c1:
                rev  = latest.get("monthly_revenue", 0)
                goal = latest.get("goal", 0)
                st.metric("月次収益", f"¥{rev:,}", help=f"目標: ¥{goal:,}")
            with c2: st.metric("アクティブ製品", latest.get("active_products", 0))
            with c3: st.write(f"**日付:** {latest.get('date', '-')}")
        else:
            st.info("PDCAデータがありません")
    else:
        st.info("PDCAデータがありません")
    style.section_card_end()

    # ── 先行指標 ──────────────────────────────────────────────────────────────
    if pdca_data:
        snapshots = pdca_data.get("leading_indicators", [])
        if snapshots:
            style.section_card_start("📊 先行指標（直近14日）")
            import pandas as pd
            rows = []
            for s in snapshots:
                proc = s.get("process", {})
                rows.append({
                    "日付": s.get("date", ""),
                    "完了タスク": proc.get("tasks_completed", 0),
                    "追加タスク": proc.get("tasks_added", 0),
                    "完了率(%)": proc.get("completion_rate_pct", 0),
                })
            df = pd.DataFrame(rows)
            if not df.empty:
                st.line_chart(df.set_index("日付")[["完了タスク", "追加タスク"]])
                st.dataframe(df, use_container_width=True)
            style.section_card_end()

        # ── 実験台帳 ──────────────────────────────────────────────────────────
        experiments = pdca_data.get("experiments", [])
        if experiments:
            style.section_card_start("🧪 実験台帳")
            for e in reversed(experiments[-10:]):
                if not isinstance(e, dict): continue
                status = e.get("status", "unknown")
                icon   = "✅" if status == "success" else "❌" if status == "failed" else "🔵"
                action = e.get("action", e.get("id", "?"))
                with st.expander(f"{icon} **{action[:60]}**", expanded=False):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**仮説:** {e.get('hypothesis', '-')}")
                        st.write(f"**カテゴリ:** {e.get('category', '-')}")
                        st.write(f"**ステータス:** {status}")
                    with c2:
                        st.write(f"**開始:** {(e.get('started_at') or '')[:10]}")
                        st.write(f"**確認日:** {e.get('check_date', '-')}")
                        rev = e.get("expected_revenue_delta", 0)
                        if rev: st.write(f"**期待収益変化:** ¥{rev:,}/月")
            style.section_card_end()

    # ── PDCA週次レポート ──────────────────────────────────────────────────────
    style.section_card_start("📋 PDCA週次レポート")
    if pdca_reports:
        reports = pdca_reports.get("reports", []) if isinstance(pdca_reports, dict) else []
        if reports:
            for r in sorted(reports, key=lambda x: x.get("date",""), reverse=True):
                date     = r.get("date", "?")
                filename = r.get("filename", "")
                with st.expander(f"📅 {date}  {filename}", expanded=False):
                    content = r.get("content", "")
                    if content: st.markdown(content[:2000])
        else:
            st.info("PDCA週次レポートがありません")
    else:
        st.info("PDCA週次レポートがありません")
    style.section_card_end()
