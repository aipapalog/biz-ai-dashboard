import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader

st.set_page_config(page_title="詳細分析", page_icon="🔬", layout="wide")
st_autorefresh(interval=120_000, key="detail_refresh")
st.title("🔬 詳細分析")

tab_loop, tab_pdca, tab_funnel, tab_mem, tab_note, tab_agent = st.tabs([
    "🔄 自律ループ", "📊 PDCA/実験", "🎯 ファネル", "🧠 Mempalace", "📝 Note記事", "💡 成功パターン"
])

# ── 自律ループ ────────────────────────────────────────────────────────────────
with tab_loop:
    loop = data_loader.autonomous_loop()
    if loop:
        total = loop.get("total_lines", 0)
        updated = loop.get("updated_at", "")
        last = loop.get("last_entry", "")
        st.caption(f"累計ログ行数: **{total:,}** 行  ｜  取得時刻: {updated[:16]}")
        if last:
            st.info(f"**最終エントリ:** {last}")
        lines_text = loop.get("lines", "")
        if lines_text:
            st.subheader("最新150行")
            st.code(lines_text, language=None)
    else:
        st.info("自律ループログがありません。")

# ── PDCA / 実験 ───────────────────────────────────────────────────────────────
with tab_pdca:
    pdca = data_loader.pdca()
    if not pdca:
        st.info("PDCAデータがありません。")
    else:
        # 月次PDCA
        latest = pdca.get("pdca_latest", {})
        if latest:
            st.subheader("📈 月次PDCA（最新）")
            c1, c2, c3 = st.columns(3)
            with c1:
                rev = latest.get("monthly_revenue", 0)
                goal = latest.get("goal", 0)
                st.metric("月次収益", f"¥{rev:,}", help=f"目標: ¥{goal:,}")
            with c2:
                prods = latest.get("active_products", 0)
                st.metric("アクティブ製品", prods)
            with c3:
                st.write(f"**日付:** {latest.get('date', '-')}")

        # 先行指標
        snapshots = pdca.get("leading_indicators", [])
        if snapshots:
            st.subheader("📊 先行指標（直近14日）")
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

        # 実験一覧
        experiments = pdca.get("experiments", [])
        if experiments:
            st.subheader("🧪 実験台帳")
            for e in reversed(experiments[-10:]):
                if not isinstance(e, dict):
                    continue
                status = e.get("status", "unknown")
                icon = "✅" if status == "success" else "❌" if status == "failed" else "🔵"
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
                        if rev:
                            st.write(f"**期待収益変化:** ¥{rev:,}/月")
                    tasks = e.get("tasks", [])
                    if tasks:
                        st.write("**タスク:**")
                        for t in tasks[:5]:
                            st.write(f"- {t}")

# ── ファネル ──────────────────────────────────────────────────────────────────
with tab_funnel:
    funnel = data_loader.funnel()
    if not funnel:
        st.info("ファネルデータがありません。")
    else:
        st.caption(f"最終更新: {funnel.get('last_updated', '-')[:16]}")
        if funnel.get("warning"):
            st.warning(funnel["warning"])

        # ステップ別メトリクス
        metrics = funnel.get("metrics", {})
        if metrics:
            st.subheader("🎯 ファネルステップ")
            step_names = {
                "note_article_views":    "①記事閲覧",
                "product_page_clicks":   "②製品ページCTR",
                "product_page_views":    "③製品ページ閲覧",
                "checkout_page_views":   "④チェックアウト",
                "purchase_completed":    "⑤購入完了",
            }
            cols = st.columns(len(step_names))
            for col, (key, label) in zip(cols, step_names.items()):
                with col:
                    val = metrics.get(key, 0)
                    st.metric(label, f"{val:,}")

        # 脱落率
        dropoff = funnel.get("dropoff_analysis", {})
        if dropoff:
            st.subheader("📉 ステップ間 脱落率")
            for step, rate in dropoff.items():
                pct = rate if isinstance(rate, (int, float)) else 0
                color = "🔴" if pct > 80 else "🟡" if pct > 50 else "🟢"
                st.write(f"{color} **{step}**: {pct:.1f}% 脱落")

        # プラットフォーム別
        platform = funnel.get("platform_breakdown", {})
        if platform:
            st.subheader("🛒 プラットフォーム別")
            import pandas as pd
            rows = []
            for p_name, p_data in platform.items():
                if isinstance(p_data, dict):
                    rows.append({"プラットフォーム": p_name, **p_data})
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True)

        # 日次推移
        daily = funnel.get("daily_records", [])
        if daily:
            st.subheader("📅 日次推移（直近14日）")
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

# ── Mempalace ─────────────────────────────────────────────────────────────────
with tab_mem:
    mem = data_loader.mempalace()
    if not mem:
        st.info("Mempalaceデータがありません。")
    else:
        rows = mem.get("rows", [])
        headers = mem.get("headers", [])
        if rows:
            import pandas as pd
            df = pd.DataFrame(rows)
            # 最新行を強調
            last = rows[-1] if rows else {}
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("ルーム数",      last.get("rooms", "-"))
            with c2: st.metric("エンティティ数", last.get("entities", "-"))
            with c3: st.metric("トリプル数",     last.get("triples", "-"))
            st.subheader("📊 推移")
            if "date" in df.columns:
                num_cols = [c for c in df.columns if c != "date"]
                try:
                    for c in num_cols:
                        df[c] = pd.to_numeric(df[c], errors="coerce")
                    st.line_chart(df.set_index("date")[num_cols])
                except Exception:
                    pass
            st.dataframe(df, use_container_width=True)

# ── Note 記事 ─────────────────────────────────────────────────────────────────
with tab_note:
    insights = data_loader.agent_insights()
    articles = insights.get("note_articles", [])
    if not articles:
        st.info("note記事データがありません。")
    else:
        st.subheader(f"📝 note 記事一覧（{len(articles)} 件）")
        total_views = sum(a.get("views", 0) for a in articles if isinstance(a, dict))
        total_likes = sum(a.get("likes", 0) for a in articles if isinstance(a, dict))
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("総記事数", len(articles))
        with c2: st.metric("総Views", total_views)
        with c3: st.metric("総Likes", total_likes)
        st.divider()
        for a in articles:
            if not isinstance(a, dict): continue
            title  = a.get("title", "?")
            views  = a.get("views", 0)
            likes  = a.get("likes", 0)
            price  = a.get("price", 0)
            status = a.get("status", "-")
            url    = a.get("url", "")
            pub    = (a.get("published_at") or "")[:10]
            price_str = f"¥{price}" if price else "無料"
            with st.expander(f"📄 **{title}** — {price_str}  👁️{views}  ❤️{likes}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**公開日:** {pub}")
                    st.write(f"**ステータス:** {status}")
                    st.write(f"**価格:** {price_str}")
                with col2:
                    st.write(f"**Views:** {views}")
                    st.write(f"**Likes:** {likes}")
                    st.write(f"**コメント:** {a.get('comments', 0)}")
                tags = a.get("tags", [])
                if tags:
                    st.write(f"**タグ:** {', '.join(tags)}")
                if url:
                    st.write(f"**URL:** {url}")

# ── 成功パターン ──────────────────────────────────────────────────────────────
with tab_agent:
    insights = data_loader.agent_insights()

    # MAB レポート
    mab = insights.get("mab_report", {})
    if mab:
        st.subheader("🎰 MAB ビジネスアイデア評価")
        st.caption(f"分析日時: {mab.get('timestamp', '-')[:16]}")
        st.write(f"分析アイデア数: **{mab.get('ideas_analyzed', 0)}**")
        recs = mab.get("recommendation", [])
        if recs:
            import pandas as pd
            df_mab = pd.DataFrame(recs)
            if not df_mab.empty:
                st.dataframe(df_mab, use_container_width=True)

    st.divider()

    # 成功パターン
    patterns = insights.get("success_patterns", {})
    if patterns:
        st.subheader("💡 エージェント成功パターン")
        if isinstance(patterns, dict):
            for category, items in patterns.items():
                if not items:
                    continue
                st.markdown(f"**{category}**")
                items_list = items if isinstance(items, list) else [items]
                for item in items_list[-5:]:
                    if isinstance(item, dict):
                        ts      = (item.get("ts") or "")[:10]
                        score   = item.get("score", "")
                        summary = item.get("summary", str(item))[:200]
                        st.markdown(f"- **スコア {score}** ({ts}): {summary}")
                    else:
                        st.write(f"- {str(item)[:150]}")
    else:
        st.info("成功パターンデータがありません。")
