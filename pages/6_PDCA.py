import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, style

st.set_page_config(page_title="🔄 PDCA", page_icon="🔄", layout="wide")
style.inject()
st.title("🔄 ビジネスPDCA")
st.caption("戦略立案 — 施策立案→評価→task_queue追加→自律ループが実行")

pdca_data = data_loader.pdca()
pdca_reports = data_loader.biz_pdca_reports()

# ── 月次PDCA最新 ──────────────────────────────────────────────────────────────
st.subheader("📈 月次PDCA（最新）")
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
st.divider()

# ── 先行指標 ──────────────────────────────────────────────────────────────────
if pdca_data:
    snapshots = pdca_data.get("leading_indicators", [])
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
        st.divider()

    # ── 実験台帳 ──────────────────────────────────────────────────────────────
    experiments = pdca_data.get("experiments", [])
    if experiments:
        st.subheader("🧪 実験台帳")
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
        st.divider()

# ── PDCA週次レポート ──────────────────────────────────────────────────────────
st.subheader("📋 PDCA週次レポート")
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
