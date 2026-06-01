import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, style

st.set_page_config(page_title="💡 BizDev", page_icon="💡", layout="wide")
st_autorefresh(interval=120_000, key="bizdev_refresh")
style.inject()
st.title("💡 ビジネスアイデア・BizDev")

trend    = data_loader.bizdev_trend()
insights = data_loader.agent_insights()
report   = data_loader.bizdev_report()

tab1, tab2, tab3, tab4 = st.tabs(["📈 スコア推移", "💡 新規候補", "🎰 MAB評価", "📊 レポート"])

# ── スコア推移 ────────────────────────────────────────────────────────────────
with tab1:
    entries = trend.get("entries", []) if trend else []
    if entries:
        import pandas as pd
        df = pd.DataFrame(entries)
        st.subheader(f"📊 Bizdevスコア推移（直近{len(entries)}件）")
        cats = trend.get("categories", [])
        st.caption(f"カテゴリ: {', '.join(cats)}  ｜  累計 {trend.get('total',0)} アイデア")
        if "date" in df.columns and "score" in df.columns:
            df_chart = df.groupby("date")["score"].mean().reset_index()
            df_chart.columns = ["日付", "平均スコア"]
            st.line_chart(df_chart.set_index("日付"))
        st.subheader("アイデア一覧（直近20件）")
        for e in reversed(entries[-20:]):
            date     = e.get("date", "?")
            score    = e.get("score", 0)
            category = e.get("category", "")
            summary  = e.get("summary", "")
            color    = "🟢" if score >= 8 else "🟡" if score >= 6 else "🔴"
            with st.expander(f"{color} スコア **{score}/10** — {date}  [{category}]"):
                st.write(summary)
    else:
        st.info("Bizdevスコアデータがありません")

# ── 新規候補 ──────────────────────────────────────────────────────────────────
with tab2:
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
        st.subheader(f"💡 高スコア候補（{len(top_ideas)}件）")
        for idea in top_ideas:
            score = idea.get("score", 0)
            color = "🟢" if score >= 8 else "🟡" if score >= 6 else "🔴"
            cat   = idea.get("category", "")
            ts    = (idea.get("ts") or "")[:10]
            summary = idea.get("summary", "")
            with st.expander(f"{color} スコア **{score}/10**  [{cat}]  {ts}"):
                st.write(summary)
    else:
        st.info("成功パターンデータがありません")

    # note記事
    note_articles = insights.get("note_articles", []) if insights else []
    if note_articles:
        st.divider()
        st.subheader(f"📝 note記事（{len(note_articles)}件）")
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

# ── MAB評価 ───────────────────────────────────────────────────────────────────
with tab3:
    mab = insights.get("mab_report", {}) if insights else {}
    if mab:
        st.subheader("🎰 MAB ビジネスアイデア評価")
        st.caption(f"分析日時: {mab.get('timestamp', '-')[:16]}  ｜  分析アイデア数: {mab.get('ideas_analyzed', 0)}")
        recs = mab.get("recommendation", [])
        if recs:
            import pandas as pd
            df_mab = pd.DataFrame(recs)
            if not df_mab.empty:
                st.dataframe(df_mab, use_container_width=True)
    else:
        st.info("MABデータがありません")

# ── Bizdevレポート ────────────────────────────────────────────────────────────
with tab4:
    st.subheader("📊 Bizdev レポート（最新）")
    if report:
        st.caption(f"📅 {report.get('date','')}  ｜  📁 {report.get('filename','')}  ｜  🔄 {report.get('updated_at','')[:16]}")
        content = report.get("content", "")
        if content: st.markdown(content[:3000])
    else:
        st.info("Bizdevレポートがありません。daily_bizdevパイプライン実行後に更新されます。")
