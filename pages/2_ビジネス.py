import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, style
from utils.data_loader import get_push_log
from utils.style import freshness_banner

st.set_page_config(page_title="ビジネス | BizDash", page_icon="📈", layout="wide")
style.inject()

_push_log = get_push_log()
st.markdown(
    f'<div style="text-align:right;margin-bottom:4px;">{freshness_banner(_push_log)}</div>',
    unsafe_allow_html=True
)

st.title("📈 ビジネス")

tab1, tab2, tab3 = st.tabs(["🏢 事業状況", "🚀 BizDev", "⭐ CX品質"])

# ══════════════════════════════════════════════════════════════════════════════
# 🏢 事業状況（旧 4_事業状況.py）
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    biz          = data_loader.business_status()
    pf           = data_loader.pf_watch()
    funnel       = data_loader.funnel()
    pdca_data    = data_loader.pdca()
    pdca_reports = data_loader.biz_pdca_reports()

    _monthly_actual = biz.get("monthly_actual", 0) if biz else 0
    _monthly_target = biz.get("monthly_target", 20000) if biz else 20000
    _prog = (_monthly_actual / _monthly_target) if _monthly_target else 0
    _hdr_status = "ok" if _prog >= 0.8 else "warn" if _prog >= 0.3 else "err"
    style.page_header("💼 事業状況・経営目標・利益予測", updated=data_loader.last_updated(), status=_hdr_status)

    inner_tab_biz, inner_tab_funnel, inner_tab_pdca = st.tabs(["💼 事業状況", "🔀 ファネル", "🔄 PDCA"])

    # ── 事業状況サブタブ ──────────────────────────────────────────────────────
    with inner_tab_biz:
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

            # ── 経営目標 ──────────────────────────────────────────────────────
            style.section_card_start("🎯 経営目標")
            g1, g2 = st.columns(2)
            with g1:
                st.markdown("**短期目標**")
                st.write(goal.get("short", "未設定"))
            with g2:
                st.markdown("**長期目標**")
                st.write(goal.get("long", "未設定"))
            style.section_card_end()

            # ── 収益進捗・予測 ────────────────────────────────────────────────
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

            # ── 製品一覧 ──────────────────────────────────────────────────────
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

            # ── ウェブ資産 ────────────────────────────────────────────────────
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

            # ── 経費一覧 ──────────────────────────────────────────────────────
            if expenses:
                style.section_card_start("💸 経費一覧")
                for e in expenses:
                    cycle = {"monthly": "月額固定", "per_sale": "売上時のみ"}.get(e.get("cycle", ""), e.get("cycle", ""))
                    amt   = e.get("amount_jpy", 0)
                    st.write(f"• **{e.get('name','')}** {cycle} ¥{amt:,}  {e.get('note','')}")
                style.section_card_end()

            # ── プラットフォーム監視 ──────────────────────────────────────────
            style.section_card_start("🔍 プラットフォーム監視（待ち状態）")
            if pf:
                watches = pf.get("services") or pf.get("watches") or []
                if isinstance(watches, dict): watches = list(watches.values())
                if isinstance(watches, list) and watches:
                    def _pf_icon(s):
                        return "✅" if s in ("ok", "active", "normal", "completed") else "⏳" if s == "pending" else "❌"
                    cols = st.columns(min(len(watches), 4))
                    for i, item in enumerate(watches[:15]):
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

    # ── ファネルサブタブ ──────────────────────────────────────────────────────
    with inner_tab_funnel:
        if not funnel:
            st.info("ファネルデータがありません。funnel_metrics.json の実データ収集パイプライン未稼働。")
        else:
            st.caption(f"最終更新: {funnel.get('last_updated', '-')[:16]}")
            warn = funnel.get("warning")
            if warn:
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
                                label = LABELS.get(k, k)
                                state = "🟡 近日対応予定（外部API連携待ち）" if "❌" in str(v) else str(v)
                                st.write(f"• **{label}**: {state}")
                else:
                    st.info(f"ℹ️ {warn}")

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
                    import pandas as pd
                    df = pd.DataFrame(rows)
                    st.line_chart(df.set_index("日付"))
                    st.dataframe(df, use_container_width=True)
                style.section_card_end()

    # ── PDCAサブタブ ──────────────────────────────────────────────────────────
    with inner_tab_pdca:
        st.caption("戦略立案 — 施策立案→評価→task_queue追加→自律ループが実行")

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


# ══════════════════════════════════════════════════════════════════════════════
# 🚀 BizDev（旧 5_BizDev.py）
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    trend      = data_loader.bizdev_trend()
    insights   = data_loader.agent_insights()
    report     = data_loader.bizdev_report()
    freelance  = data_loader.freelance_report()
    biz_status = data_loader.business_status()

    style.page_header("💡 ビジネスアイデア・BizDev", updated=data_loader.last_updated(), status="info")

    biz_tab1, biz_tab2, biz_tab3, biz_tab4, biz_tab5 = st.tabs([
        "📈 スコア推移", "💡 新規候補", "🎰 MAB評価", "📊 レポート", "🔍 案件リサーチ"
    ])

    # ── スコア推移 ────────────────────────────────────────────────────────────
    with biz_tab1:
        entries = trend.get("entries", []) if trend else []
        if entries:
            import pandas as pd
            df = pd.DataFrame(entries)
            style.section_card_start(f"📊 Bizdevスコア推移（直近{len(entries)}件）")
            cats = trend.get("categories", [])
            st.caption(f"カテゴリ: {', '.join(cats)}  ｜  累計 {trend.get('total',0)} アイデア")
            if "date" in df.columns and "score" in df.columns:
                df_chart = df.groupby("date")["score"].mean().reset_index()
                df_chart.columns = ["日付", "平均スコア"]
                st.line_chart(df_chart.set_index("日付"))
            style.section_card_end()

            style.section_card_start("アイデア一覧（直近20件）")
            for e in reversed(entries[-20:]):
                date     = e.get("date", "?")
                score    = e.get("score", 0)
                category = e.get("category", "")
                summary  = e.get("summary", "")
                color    = "🟢" if score >= 8 else "🟡" if score >= 6 else "🔴"
                with st.expander(f"{color} スコア **{score}/10** — {date}  [{category}]"):
                    st.write(summary)
            style.section_card_end()
        else:
            st.info("Bizdevスコアデータがありません")

    # ── 新規候補 ──────────────────────────────────────────────────────────────
    with biz_tab2:
        idea_candidates = biz_status.get("idea_candidates", []) if biz_status else []
        status_col = {"検討中": "blue", "検証中": "orange", "開発中": "green", "保留": "gray", "未着手": "gray"}
        if idea_candidates:
            style.section_card_start(f"💡 新規ビジネス候補（{len(idea_candidates)}件）")
            for c in idea_candidates:
                sc     = c.get("bizdev_score")
                st_val = c.get("status", "未着手")
                sc_str = f"AI評価 {sc}/10 " if sc else ""
                prog   = c.get("progress", 0)
                col    = status_col.get(st_val, "gray")
                with st.expander(f"{'🤖' if c.get('micro_saas') else '👤'} **{c['title']}** — {sc_str}[:{col}[{st_val}]]"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.metric("自動化率", f"{c.get('automation_rate', 0)}%")
                        st.caption(c.get("automation_note", "")[:80])
                    with c2:
                        st.metric("進捗", f"{prog}%")
                        st.progress(prog / 100)
                    st.write(f"**実現性:** {c.get('feasibility','')}  ｜  **リスク:** {c.get('risk','')[:80]}")
                    st.write(f"**次のアクション:** {c.get('next_action','')}")
                    if c.get("revenue_model"):
                        st.caption(f"収益モデル: {c['revenue_model'][:100]}")
            style.section_card_end()
        else:
            st.info("business_status.json に idea_candidates がありません")

        patterns = insights.get("success_patterns", {}) if insights else {}
        all_ideas = []
        if isinstance(patterns, dict):
            for cat, items in patterns.items():
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict):
                            all_ideas.append({**item, "category": cat})
        top_ideas = sorted(all_ideas, key=lambda x: x.get("score", 0), reverse=True)[:20]
        if top_ideas:
            style.section_card_start(f"💡 高スコア候補（{len(top_ideas)}件）")
            for idea in top_ideas:
                score = idea.get("score", 0)
                color = "🟢" if score >= 8 else "🟡" if score >= 6 else "🔴"
                cat   = idea.get("category", "")
                ts    = (idea.get("ts") or "")[:10]
                summary = idea.get("summary", "")
                with st.expander(f"{color} スコア **{score}/10**  [{cat}]  {ts}"):
                    st.write(summary)
            style.section_card_end()
        else:
            st.info("成功パターンデータがありません")

        records = trend.get("records", []) if trend else []
        if records:
            with st.expander(f"📋 AIエージェント提案履歴（直近{len(records)}日）"):
                import pandas as pd
                rows = []
                for r in records:
                    sc = r.get("score")
                    verdict = r.get("verdict", "?")
                    v_color = {"推奨": "🟢", "保留": "🟡", "却下": "🔴"}.get(verdict, "⚪")
                    rows.append({
                        "日付":         r.get("date", ""),
                        "最優秀アイデア": (r.get("idea") or "")[:60],
                        "スコア":       f"{sc}/10" if sc else "?",
                        "判定":         f"{v_color} {verdict}",
                        "なぜ今":       (r.get("why_now") or "")[:80],
                    })
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True)

        note_articles = insights.get("note_articles", []) if insights else []
        if note_articles:
            style.section_card_start(f"📝 note記事（{len(note_articles)}件）")
            total_views = sum(a.get("views", 0) for a in note_articles if isinstance(a, dict))
            total_likes = sum(a.get("likes", 0) for a in note_articles if isinstance(a, dict))
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("総記事数", len(note_articles))
            with c2: st.metric("総Views", total_views)
            with c3: st.metric("総Likes", total_likes)
            for a in note_articles:
                if not isinstance(a, dict): continue
                title  = a.get("title", "?")
                views  = a.get("views", 0)
                likes  = a.get("likes", 0)
                price  = a.get("price", 0)
                pub    = (a.get("published_at") or "")[:10]
                url    = a.get("url", "")
                price_str = f"¥{price}" if price else "無料"
                with st.expander(f"📄 **{title}** — {price_str}  👁️{views}  ❤️{likes}"):
                    st.write(f"**公開日:** {pub}  **価格:** {price_str}  **Views:** {views}  **Likes:** {likes}")
                    tags = a.get("tags", [])
                    if tags: st.write(f"**タグ:** {', '.join(tags)}")
                    if url:  st.write(f"**URL:** {url}")
            style.section_card_end()

    # ── MAB評価 ───────────────────────────────────────────────────────────────
    with biz_tab3:
        mab = insights.get("mab_report", {}) if insights else {}
        if mab:
            style.section_card_start("🎰 MAB ビジネスアイデア評価")
            st.caption(f"分析日時: {mab.get('timestamp', '-')[:16]}  ｜  分析アイデア数: {mab.get('ideas_analyzed', 0)}")
            recs = mab.get("recommendation", [])
            if recs:
                import pandas as pd
                df_mab = pd.DataFrame(recs)
                if not df_mab.empty:
                    st.dataframe(df_mab, use_container_width=True)
            style.section_card_end()
        else:
            st.info("MABデータがありません")

    # ── Bizdevレポート ────────────────────────────────────────────────────────
    with biz_tab4:
        style.section_card_start("📊 Bizdev レポート（最新）")
        if report:
            st.caption(f"📅 {report.get('date','')}  ｜  📁 {report.get('filename','')}  ｜  🔄 {report.get('updated_at','')[:16]}")
            content = report.get("content", "")
            if content: st.markdown(content[:3000])
        else:
            st.info("Bizdevレポートがありません。daily_bizdevパイプライン実行後に更新されます。")
        style.section_card_end()

    # ── 案件リサーチ ──────────────────────────────────────────────────────────
    with biz_tab5:
        style.section_card_start("🔍 フリーランス案件リサーチ（AI自動化率 Top5）")
        if freelance:
            st.caption(f"📅 {freelance.get('date','')}  ｜  📁 {freelance.get('filename','')}  ｜  🔄 {freelance.get('updated_at','')[:16]}")
            content = freelance.get("content", "")
            if content:
                st.markdown(content[:4000])
            else:
                st.info("レポートの内容がありません")
        else:
            st.info("フリーランス案件レポートがありません。freelance_researcherパイプライン実行後に更新されます。")
            st.markdown("""
**対象プラットフォーム:**
- クラウドワークス
- ランサーズ
- Coconala

**調査対象スキル:**
- QAエンジニア
- テスト自動化
- Playwright / Selenium
- Python自動化
- AI活用コンサルティング
""")
        style.section_card_end()


# ══════════════════════════════════════════════════════════════════════════════
# ⭐ CX品質（旧 6_CX品質.py）
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    risk = data_loader.risk_report()
    _risk_high = "HIGH" in (risk.get("content", "") or "").upper() if risk else False
    style.page_header("😊 CX・品質・リスク", updated=data_loader.last_updated(), status="err" if _risk_high else "ok")

    cx_tab1, cx_tab2, cx_tab3, cx_tab4, cx_tab5 = st.tabs([
        "🎯 顧客体験(CX)", "⚠️ リスク", "🩺 ヘルスチェック", "🪙 トークン管理", "💬 コメント"
    ])

    # ── CX ────────────────────────────────────────────────────────────────────
    with cx_tab1:
        cx = data_loader.cx_report()
        style.section_card_start("🎯 顧客体験（CX）分析レポート")
        if cx:
            st.caption(f"📅 {cx.get('date','')}  ｜  🔄 {cx.get('updated_at','')[:16]}")
            content = cx.get("content", "")
            if content:
                st.markdown(content[:3000])
        else:
            st.info("CXレポートがありません。cx_improverパイプライン実行後に更新されます。")
        style.section_card_end()

    # ── リスク ────────────────────────────────────────────────────────────────
    with cx_tab2:
        style.section_card_start("⚠️ リスク評価レポート",
                                 "Highリスクあり" if _risk_high else "正常",
                                 "err" if _risk_high else "ok")
        if risk:
            st.caption(f"📅 {risk.get('date','')}  ｜  🔄 {risk.get('updated_at','')[:16]}")
            content = risk.get("content", "")
            if _risk_high:
                st.error("🔴 Highリスクあり")
            if content:
                st.markdown(content[:3000])
        else:
            st.info("リスクレポートがありません。risk_managerパイプライン実行後に更新されます。")
        style.section_card_end()

    # ── ヘルスチェック ────────────────────────────────────────────────────────
    with cx_tab3:
        health      = data_loader.health_check()
        code_health = data_loader.code_health()
        issues      = code_health.get("issues", []) if code_health else []
        highs       = [x for x in issues if isinstance(x, dict) and x.get("severity") in ("high", "critical")]
        _health_ok  = health and "error" not in (health.get("content", "") or "").lower()[:200]

        style.section_card_start("🩺 エージェント・パイプライン健全性",
                                 "OK" if _health_ok else "要確認",
                                 "ok" if _health_ok else "warn")
        if health:
            st.caption(f"📅 {health.get('date','')}  ｜  🔄 {health.get('updated_at','')[:16]}")
            content = health.get("content", "")
            if content:
                with st.expander("ヘルスチェック詳細", expanded=True):
                    st.markdown(content[:2000])
        else:
            st.info("ヘルスチェックデータがありません")
        style.section_card_end()

        if code_health:
            style.section_card_start("🔍 コードヘルス",
                                     "High問題あり" if highs else "正常",
                                     "err" if highs else "ok")
            date = (code_health.get("generated_at") or code_health.get("date") or "")[:10]
            st.caption(f"最終チェック: {date}")
            mids = [x for x in issues if isinstance(x, dict) and x.get("severity") == "medium"]
            lc1, lc2, lc3 = st.columns(3)
            with lc1:
                style.kpi_wrap_start("critical" if highs else "ok")
                st.metric("🔴 高度", len(highs))
                style.kpi_wrap_end()
            with lc2:
                style.kpi_wrap_start("warn" if mids else "ok")
                st.metric("🟡 中度", len(mids))
                style.kpi_wrap_end()
            with lc3:
                st.metric("📁 総件数", len(issues))
            for iss in highs[:5]:
                st.warning(f"**{iss.get('file','?')}** — {iss.get('message','')}")
            style.section_card_end()

    # ── トークン管理 ──────────────────────────────────────────────────────────
    with cx_tab4:
        budget = data_loader.api_budget()
        style.section_card_start("🪙 API使用量・トークン管理")
        if budget:
            providers = [(k, v) for k, v in budget.items() if isinstance(v, dict)]
            if providers:
                for name, info in providers:
                    used  = info.get("used_usd", 0)
                    limit = info.get("budget_usd", 0)
                    pct   = (used / limit * 100) if limit else 0
                    st.progress(min(pct / 100, 1.0), text=f"{name}: ${used:.3f} / ${limit:.2f}  ({pct:.1f}%)")
            else:
                used  = budget.get("used_usd", 0)
                limit = budget.get("budget_usd", 0)
                pct   = (used / limit * 100) if limit else 0
                st.progress(min(pct / 100, 1.0), text=f"API消費: ${used:.3f} / ${limit:.2f}  ({pct:.1f}%)")
        style.section_card_end()

        style.section_card_start("📋 1日の判断回数削減策")
        strategies = [
            ("✅ Haiku委譲（閾値9）",           "スコア≤9のタスクは全てHaiku。Sonnetは複雑実装のみ"),
            ("✅ WebSearch/WebFetch はHaiku限定", "HTML全文がコンテキストに積まれるのを防ぐ"),
            ("✅ 同一ファイルを2回読まない",     "初回読み込みで記憶。以降はメモリ参照"),
            ("✅ バッチ委譲原則",                "複数確認作業は1回のHaiku agentにまとめる"),
        ]
        for s, d in strategies:
            st.markdown(f"**{s}**  \n　{d}")
        style.section_card_end()

    # ── コメント ──────────────────────────────────────────────────────────────
    with cx_tab5:
        from datetime import datetime
        from utils import firebase_client
        data         = data_loader.comments()
        comment_list = data.get("comments", [])
        total        = data.get("total", 0)
        real_count   = data.get("real_count", 0)
        last_upd     = data.get("last_updated", "")

        style.section_card_start("💬 ダッシュボードコメント")
        st.caption(f"総コメント数: {total:,} 件  ｜  実コメント: {real_count} 件  ｜  最終更新: {last_upd[:16] if last_upd else '-'}")
        st.caption("※ AI返信は自律ループが自動生成します。")

        with st.expander("✏️ 新規コメントを投稿", expanded=False):
            with st.form("new_comment_form", clear_on_submit=True):
                nc_title   = st.text_input("タイトル（件名）")
                nc_section = st.text_input("セクション", placeholder="例: CX, タスク, ビジネス")
                nc_comment = st.text_area("コメント内容 *", height=80)
                if st.form_submit_button("📨 投稿する", use_container_width=True):
                    if not nc_comment.strip():
                        st.error("コメント内容を入力してください")
                    else:
                        now    = datetime.now().isoformat()
                        doc_id = f"comment_{datetime.now().timestamp():.0f}"
                        new_c  = {
                            "id": doc_id, "item_title": nc_title or "（無題）",
                            "section": nc_section or "general",
                            "user_comment": nc_comment.strip(),
                            "ai_reply": "", "timestamp": now,
                            "status": "pending", "source": "streamlit",
                        }
                        ok = firebase_client.patch_doc("dashboard_comments", doc_id, new_c)
                        if ok:
                            st.success("✅ 投稿しました。AI返信は自律ループが自動生成します。")
                            st.rerun()
                        else:
                            st.error("❌ 投稿に失敗しました（Firebase接続を確認）")

        if comment_list:
            for c in reversed(comment_list[-20:]):
                if not isinstance(c, dict):
                    continue
                ts    = (c.get("timestamp") or "")[:16]
                title = c.get("item_title", "")
                sec   = c.get("section", "")
                user  = c.get("user_comment", "")
                ai    = c.get("ai_reply", "")
                with st.expander(f"💬 {ts}  [{sec}] {title[:40]}"):
                    st.write(f"👤 **ユーザー:** {user}")
                    if ai:
                        st.write(f"🤖 **AI返信:** {ai}")
        else:
            st.info("コメントがありません")
        style.section_card_end()
