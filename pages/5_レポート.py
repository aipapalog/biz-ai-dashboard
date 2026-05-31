import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader

st.set_page_config(page_title="レポート", page_icon="📄", layout="wide")
st_autorefresh(interval=120_000, key="report_refresh")
st.title("📄 レポート・分析")

tab_biz, tab_cx, tab_risk, tab_health, tab_freelance, tab_levelup = st.tabs([
    "📊 Bizdev", "🎯 CX分析", "⚠️ リスク", "🩺 ヘルスチェック", "💼 フリーランス", "🚀 レベルアップ"
])

def show_report(report: dict, title: str):
    if not report:
        st.info(f"{title} レポートがまだありません。パイプライン実行後に更新されます。")
        return
    date = report.get("date", "")
    filename = report.get("filename", "")
    content = report.get("content", "")
    updated = report.get("updated_at", "")
    st.caption(f"📅 {date}  ｜  📁 {filename}  ｜  🔄 {updated[:16]}")
    if content:
        st.markdown(content)

with tab_biz:
    st.subheader("📊 Bizdev レポート（最新）")
    show_report(data_loader.bizdev_report(), "Bizdev")

with tab_cx:
    st.subheader("🎯 CX（顧客体験）分析レポート")
    show_report(data_loader.cx_report(), "CX")

with tab_risk:
    st.subheader("⚠️ リスク評価レポート")
    show_report(data_loader.risk_report(), "リスク")

with tab_health:
    st.subheader("🩺 システムヘルスチェック")
    show_report(data_loader.health_check(), "ヘルスチェック")

with tab_freelance:
    st.subheader("💼 フリーランス案件調査")
    show_report(data_loader.freelance_report(), "フリーランス")

with tab_levelup:
    st.subheader("🚀 エージェント レベルアップ状況")
    status = data_loader.levelup_status()
    if not status:
        st.info("レベルアップ状況データがありません。")
    else:
        # levelup_status.json の構造に合わせて表示
        if isinstance(status, dict):
            for key, val in status.items():
                if isinstance(val, dict):
                    with st.expander(f"**{key}**", expanded=False):
                        for k2, v2 in val.items():
                            st.write(f"**{k2}:** {v2}")
                elif isinstance(val, list):
                    st.markdown(f"**{key}**")
                    for item in val[:10]:
                        st.write(f"- {item}")
                else:
                    st.write(f"**{key}:** {val}")

    st.divider()
    st.subheader("📜 レベルアップ履歴")
    history = data_loader.levelup_history()
    if history:
        for h in sorted(history, key=lambda x: x.get("date", ""), reverse=True):
            date = h.get("date", "?")
            content = h.get("content", "")
            with st.expander(f"📅 {date}", expanded=False):
                st.markdown(content)
    else:
        st.info("レベルアップ履歴がありません。")
