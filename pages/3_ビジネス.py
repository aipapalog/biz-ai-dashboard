import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader

st.set_page_config(page_title="ビジネス", page_icon="💼", layout="wide")
st_autorefresh(interval=60_000, key="biz_refresh")
st.title("💼 ビジネス・事業分析")

biz = data_loader.business_status()
pf = data_loader.pf_watch()

tab1, tab2, tab3 = st.tabs(["経営目標・製品", "プラットフォーム監視", "Bizdev分析"])

# ── 経営目標・製品 ────────────────────────────────────────────────────────────
with tab1:
    if not biz:
        st.info("business_status.json が読み込めていません。Firebaseまたはローカルファイルを確認してください。")
    else:
        goal = biz.get("management_goal", {})
        forecast = biz.get("management_forecast", {})

        st.subheader("🎯 経営目標")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**短期目標**")
            st.write(goal.get("short", "未設定"))
        with col2:
            st.markdown("**長期目標**")
            st.write(goal.get("long", "未設定"))

        st.subheader("📈 収益予測")
        c1, c2, c3 = st.columns(3)
        with c1:
            monthly = forecast.get("monthly_forecast_jpy", 0)
            due = forecast.get("monthly_due", "-")
            st.metric("月次収益予測", f"¥{monthly:,}" if isinstance(monthly, (int, float)) else str(monthly),
                      help=f"期限: {due}")
        with c2:
            annual = forecast.get("annual_forecast_jpy", 0)
            due2 = forecast.get("annual_due", "-")
            st.metric("年次収益予測", f"¥{annual:,}" if isinstance(annual, (int, float)) else str(annual),
                      help=f"期限: {due2}")
        with c3:
            note = forecast.get("note", "")
            if note:
                st.caption(note)

        # 製品一覧
        products = biz.get("products", [])
        if products:
            st.subheader("📦 製品一覧")
            for p in products:
                status = p.get("status", "unknown")
                status_icon = "🟢" if status == "active" else ("🟡" if status == "pending" else "🔴")
                with st.expander(f"{status_icon} **{p.get('name', '?')}** — {p.get('platform', '-')}"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        price = p.get("price_jpy", 0)
                        st.metric("価格", f"¥{price:,}" if isinstance(price, (int, float)) else str(price))
                    with c2:
                        rev = p.get("monthly_revenue", 0)
                        st.metric("月次収益", f"¥{rev:,}" if isinstance(rev, (int, float)) else str(rev))
                    with c3:
                        st.write(f"**ステータス:** {status}")
                        ls_id = p.get("ls_id", "")
                        if ls_id:
                            st.caption(f"LS ID: {ls_id}")

# ── プラットフォーム監視 ──────────────────────────────────────────────────────
with tab2:
    if not pf:
        st.info("pf_watch.json が読み込めていません。")
    else:
        st.subheader("🔍 プラットフォーム状態")
        watches = pf.get("watches", pf) if isinstance(pf, dict) else []
        if isinstance(watches, dict):
            watches = list(watches.values())

        for item in (watches if isinstance(watches, list) else []):
            platform = item.get("platform", item.get("name", "?"))
            status = item.get("status", "unknown")
            msg = item.get("message", item.get("note", ""))
            last = item.get("last_checked", item.get("updated_at", "-"))

            icon = "✅" if status in ("ok", "active", "normal") else \
                   "⚠️" if status in ("warning", "pending") else "❌"
            with st.expander(f"{icon} **{platform}** — {status}"):
                if msg:
                    st.write(msg)
                st.caption(f"最終確認: {last}")

        if not watches:
            # pf_watchが単純な辞書の場合
            for k, v in (pf.items() if isinstance(pf, dict) else []):
                if isinstance(v, dict):
                    status = v.get("status", "?")
                    icon = "✅" if "ok" in str(status).lower() else "⚠️"
                    st.markdown(f"{icon} **{k}**: {status}")

# ── Bizdev分析 ────────────────────────────────────────────────────────────────
with tab3:
    report = data_loader.bizdev_report()

    if report:
        date_str = report.get("date", "")
        st.subheader(f"📊 最新 Bizdev レポート（{date_str}）")

        # パイプライン実行ステータス
        pl_logs = data_loader.pipeline_logs()
        bizdev_log = pl_logs.get("logs", {}).get("daily_bizdev", {})
        if bizdev_log:
            status = bizdev_log.get("status", "unknown")
            icon = "✅" if status == "success" else "❌" if status == "failed" else "❓"
            st.caption(f"{icon} 最終実行: {bizdev_log.get('last_run', '-')} — {status}")

        content = report.get("content", "")
        if content:
            st.markdown(content)
    else:
        st.info("Bizdevレポートがまだありません。\nパイプライン実行後にFirebaseから取得されます。")
