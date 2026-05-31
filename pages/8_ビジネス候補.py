import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader

st.set_page_config(page_title="新規ビジネス候補", page_icon="💡", layout="wide")
st_autorefresh(interval=120_000, key="biz_idea_refresh")
st.title("💡 新規ビジネス候補・スコア分析")

trend    = data_loader.bizdev_trend()
insights = data_loader.agent_insights()

tab1, tab2, tab3 = st.tabs(["📈 スコア推移", "💡 新規候補", "🎰 MAB評価"])

# ── スコア推移 ─────────────────────────────────────────────────────────────────
with tab1:
    entries = trend.get("entries", []) if trend else []
    if entries:
        import pandas as pd
        df = pd.DataFrame(entries)
        st.subheader(f"📊 Bizdevスコア推移（直近{len(entries)}件）")
        cats = trend.get("categories", [])
        st.caption(f"カテゴリ: {', '.join(cats)}  ｜  累計 {trend.get('total',0)} アイデア")

        if "date" in df.columns:
            df_chart = df.groupby("date")["score"].mean().reset_index()
            df_chart.columns = ["日付", "平均スコア"]
            st.line_chart(df_chart.set_index("日付"))

        st.subheader("アイデア一覧")
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

# ── 新規候補（高スコア） ────────────────────────────────────────────────────────
with tab2:
    patterns = insights.get("success_patterns", {}) if insights else {}
    all_ideas = []
    if isinstance(patterns, dict):
        for cat, items in patterns.items():
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        all_ideas.append({
                            "category": cat,
                            "score":    item.get("score", 0),
                            "date":     (item.get("ts") or "")[:10],
                            "summary":  item.get("summary", ""),
                        })
    all_ideas.sort(key=lambda x: x.get("score", 0), reverse=True)

    if all_ideas:
        st.subheader(f"💡 高スコアビジネス候補（{len(all_ideas)}件）")
        for idea in all_ideas[:15]:
            score   = idea.get("score", 0)
            cat     = idea.get("category", "")
            date    = idea.get("date", "")
            summary = idea.get("summary", "")
            color   = "🟢" if score >= 8 else "🟡" if score >= 6 else "🔴"
            with st.expander(f"{color} スコア **{score}/10** — {cat}  ({date})"):
                st.write(summary[:500])
    else:
        st.info("ビジネス候補データがありません")

# ── MAB 評価 ──────────────────────────────────────────────────────────────────
with tab3:
    mab = insights.get("mab_report", {}) if insights else {}
    if mab:
        st.subheader("🎰 多腕バンディット（MAB）ビジネスアイデア評価")
        st.caption(f"分析日時: {mab.get('timestamp','')[:16]}  ｜  分析数: {mab.get('ideas_analyzed',0)}")
        recs = mab.get("recommendation", [])
        if recs:
            for r in recs:
                rank      = r.get("rank", 0)
                arm_id    = r.get("arm_id", "?")
                rate      = r.get("success_rate", 0)
                trials    = r.get("total_trials", 0)
                verdict   = r.get("verdict", "")
                pct_icon  = "🟢" if rate > 0.5 else "🟡" if rate > 0.2 else "🔴"
                with st.expander(f"#{rank} {pct_icon} 成功率 {rate*100:.0f}% — {arm_id[:50]}"):
                    st.write(f"**試行回数:** {trials}")
                    st.write(f"**判定:** {verdict}")
    else:
        st.info("MAB評価データがありません")
