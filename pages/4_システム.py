import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader

st.set_page_config(page_title="システム監視", page_icon="🖥️", layout="wide")
st_autorefresh(interval=60_000, key="sys_refresh")
st.title("🖥️ システム監視")

sys_info = data_loader.system_info()
ds = data_loader.datasource()
scheduler = data_loader.scheduler_tasks()
levelup = data_loader.levelup_history()

tab1, tab2, tab3 = st.tabs(["システム状態", "スケジューラ", "レベルアップ履歴"])

# ── システム状態 ──────────────────────────────────────────────────────────────
with tab1:
    if sys_info:
        st.subheader("📊 リソース")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            battery = sys_info.get("battery_percent", 0)
            charging = sys_info.get("charging", False)
            icon = "⚡" if charging else ("🔋" if battery > 20 else "🪫")
            st.metric(f"{icon} バッテリー", f"{battery}%")
        with c2:
            cpu = sys_info.get("cpu_percent", 0)
            color = "🔴" if cpu > 80 else ("🟡" if cpu > 50 else "🟢")
            st.metric(f"{color} CPU使用率", f"{cpu:.1f}%")
        with c3:
            mem = sys_info.get("memory_percent", 0)
            color = "🔴" if mem > 85 else ("🟡" if mem > 70 else "🟢")
            st.metric(f"{color} メモリ使用率", f"{mem:.1f}%")
        with c4:
            st.metric("🌐 ネットワーク", sys_info.get("ssid", "不明"))

        # プロセス情報
        procs = sys_info.get("processes", [])
        if procs:
            st.subheader("🔄 実行中プロセス")
            import pandas as pd
            df = pd.DataFrame(procs)
            st.dataframe(df, use_container_width=True)

    # datasource.json の realtime セクション
    realtime = ds.get("realtime", {})
    if realtime:
        st.subheader("⚡ リアルタイム状態")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**実行状態:** {realtime.get('execution_status', '-')}")
            st.write(f"**実行中スクリプト:** {realtime.get('running_script', '-')}")
        with col2:
            st.write(f"**詳細:** {realtime.get('running_detail', '-')}")
            st.caption(f"更新: {realtime.get('last_updated', '-')}")

    claude_status = ds.get("claude_code_status", {})
    if claude_status:
        st.subheader("🤖 Claude Code状態")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("CPU", f"{claude_status.get('cpu_percent', 0):.1f}%")
        with c2:
            st.metric("メモリ", f"{claude_status.get('memory_mb', 0):.0f} MB")
        with c3:
            st.metric("プロセス数", claude_status.get("process_count", 0))

    if not sys_info and not realtime:
        st.info("システム情報がありません。firebase_dashboard_pusher.py を実行してデータをFirebaseに送信してください。")

# ── スケジューラ ──────────────────────────────────────────────────────────────
with tab2:
    if scheduler:
        st.subheader(f"⏰ 登録タスク ({len(scheduler)} 件)")
        import pandas as pd
        df = pd.DataFrame(scheduler)
        display_cols = [c for c in ["name", "schedule", "last_run", "next_run", "status"] if c in df.columns]
        if display_cols:
            st.dataframe(df[display_cols], use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
    else:
        st.info("スケジューラ情報がありません。firebase_dashboard_pusher.py を実行してください。")

        # ローカルでのスケジューラ情報取得を試みる
        st.subheader("📋 既知のスケジュール（定義ベース）")
        schedule_data = [
            {"タスク": "ProductResearcher", "時刻": "毎日 21:00", "種別": "AI"},
            {"タスク": "DailyLoopImprover", "時刻": "毎日 21:01", "種別": "AI"},
            {"タスク": "DailyBizDev", "時刻": "毎日 21:12", "種別": "AI"},
            {"タスク": "ProcessMonitor", "時刻": "毎日 21:15", "種別": "システム"},
            {"タスク": "GDriveBackup", "時刻": "毎日 21:21", "種別": "システム"},
            {"タスク": "AutonomousLoop", "時刻": "週次（日）21:23", "種別": "AI"},
            {"タスク": "PipelineImprover", "時刻": "週次（日）21:29", "種別": "AI"},
        ]
        import pandas as pd
        st.dataframe(pd.DataFrame(schedule_data), use_container_width=True)

# ── レベルアップ履歴 ──────────────────────────────────────────────────────────
with tab3:
    if levelup:
        st.subheader(f"🏆 エージェントレベルアップ履歴 ({len(levelup)} 件)")
        for entry in levelup[:20]:
            if isinstance(entry, dict):
                date = entry.get("date", entry.get("timestamp", "-"))
                agent = entry.get("agent", entry.get("name", "-"))
                skill = entry.get("skill", entry.get("improvement", "-"))
                st.markdown(f"**{date[:10] if len(str(date)) > 10 else date}** — {agent}: {skill}")
            elif isinstance(entry, str):
                st.markdown(f"- {entry}")
    else:
        st.info("レベルアップ履歴がありません。levelup_logsフォルダを確認してください。")
