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
