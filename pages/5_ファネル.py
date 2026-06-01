import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, style

st.set_page_config(page_title="🔀 ファネル", page_icon="🔀", layout="wide")
style.inject()
st.title("🔀 ユーザー獲得ファネル")

funnel = data_loader.funnel()
if not funnel:
    st.info("ファネルデータがありません。funnel_metrics.json の実データ収集パイプライン未稼働。")
    st.stop()

st.caption(f"最終更新: {funnel.get('last_updated', '-')[:16]}")
if funnel.get("warning"):
    st.warning(funnel["warning"])

# ── ステップ別メトリクス ───────────────────────────────────────────────────────
metrics = funnel.get("metrics", {})
if metrics:
    st.subheader("🎯 ファネルステップ")
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

# ── 脱落率 ────────────────────────────────────────────────────────────────────
dropoff = funnel.get("dropoff_analysis", {})
if dropoff:
    st.subheader("📉 ステップ間 脱落率")
    for step, rate in dropoff.items():
        pct = rate if isinstance(rate, (int, float)) else 0
        color = "🔴" if pct > 80 else "🟡" if pct > 50 else "🟢"
        st.write(f"{color} **{step}**: {pct:.1f}% 脱落")
    st.divider()

# ── プラットフォーム別 ────────────────────────────────────────────────────────
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
    st.divider()

# ── 日次推移 ──────────────────────────────────────────────────────────────────
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
        st.dataframe(df, use_container_width=True)
