import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, style

st.set_page_config(page_title="💡 BizDev", page_icon="💡", layout="wide")
style.inject()

trend      = data_loader.bizdev_trend()
insights   = data_loader.agent_insights()
report     = data_loader.bizdev_report()
freelance  = data_loader.freelance_report()
biz_status = data_loader.business_status()

style.page_header("💡 ビジネスアイデア・BizDev", updated=data_loader.last_updated(), status="info")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 スコア推移", "💡 新規候補", "🎰 MAB評価", "📊 レポート", "🔍 案件リサーチ"
])

# ── スコア推移 ────────────────────────────────────────────────────────────────
with tab1:
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

# ── 新規候補 ──────────────────────────────────────────────────────────────────
with tab2:
    # ── business_status.json の idea_candidates（手動管理・TOEIC UP等） ──
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

    # AIエージェント提案履歴（bizdev_trend.records）
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

    # note記事
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

# ── MAB評価 ───────────────────────────────────────────────────────────────────
with tab3:
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

# ── Bizdevレポート ────────────────────────────────────────────────────────────
with tab4:
    style.section_card_start("📊 Bizdev レポート（最新）")
    if report:
        st.caption(f"📅 {report.get('date','')}  ｜  📁 {report.get('filename','')}  ｜  🔄 {report.get('updated_at','')[:16]}")
        content = report.get("content", "")
        if content: st.markdown(content[:3000])
    else:
        st.info("Bizdevレポートがありません。daily_bizdevパイプライン実行後に更新されます。")
    style.section_card_end()

# ── 案件リサーチ（旧 11_案件リサーチ.py の内容）──────────────────────────────
with tab5:
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
