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

exec_times  = data_loader.execution_times()
budget      = data_loader.api_budget()
pl_logs     = data_loader.pipeline_logs()
kanban_sum  = data_loader.kanban_summary() if hasattr(data_loader, "kanban_summary") else {}
code_health = data_loader.code_health()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚡ リアルタイム", "🖥️ システム状態", "⏰ スケジューラ", "📈 実行統計", "🏆 レベルアップ"])

# ── リアルタイム（30秒更新） ──────────────────────────────────────────────────
with tab1:
    st_autorefresh(interval=30_000, key="realtime_refresh")
    st.caption(f"🔄 30秒毎自動更新  ｜  最終取得: {data_loader.last_updated()}")

    # システムリソース
    if sys_info:
        c1, c2, c3, c4, c5 = st.columns(5)
        bat = sys_info.get("battery_percent", 0)
        chg = sys_info.get("charging", False)
        with c1: st.metric("🔋 バッテリー",  f"{bat}%" + (" ⚡" if chg else ""))
        with c2: st.metric("💻 CPU",         f"{sys_info.get('cpu_percent', 0):.1f}%")
        with c3: st.metric("🧠 メモリ",      f"{sys_info.get('memory_percent', 0):.1f}%")
        with c4: st.metric("💾 ディスク(C:)", f"{sys_info.get('disk_percent', 0):.0f}%")
        with c5: st.metric("🌐 NW",          sys_info.get("ssid", "不明"))

    st.divider()

    # パイプライン状況
    st.subheader("⚙️ パイプライン最終実行")
    logs = pl_logs.get("logs", pl_logs) if isinstance(pl_logs, dict) else {}
    if logs:
        cols = st.columns(3)
        for i, (name, info) in enumerate(logs.items()):
            if not isinstance(info, dict):
                continue
            status = info.get("status", "unknown")
            icon   = "✅" if status == "success" else "❌" if status == "failed" else "❓"
            with cols[i % 3]:
                st.markdown(f"{icon} **{name}**  \n🕐 {info.get('last_run', '-')}")
    else:
        st.info("パイプラインログがありません")

    st.divider()

    # Kanban クイックサマリー
    st.subheader("📋 タスクサマリー")
    ks = data_loader.kanban_summary() if hasattr(data_loader, "kanban_summary") else {}
    if not ks:
        ks = {}
    kc1, kc2, kc3, kc4 = st.columns(4)
    with kc1: st.metric("⬜ Open",   ks.get("open", "-"))
    with kc2: st.metric("🔵 進行中", ks.get("in_progress", "-"))
    with kc3: st.metric("🟡 確認待ち", ks.get("to_verify", "-"))
    with kc4: st.metric("✅ 完了",   ks.get("closed", "-"))

    # コードヘルス
    if code_health:
        st.divider()
        st.subheader("🩺 コードヘルス")
        date = (code_health.get("generated_at") or code_health.get("date") or "")[:10]
        st.caption(f"最終チェック: {date}")
        issues = code_health.get("issues", [])
        highs  = [x for x in issues if isinstance(x, dict) and x.get("severity") in ("high", "critical")]
        mids   = [x for x in issues if isinstance(x, dict) and x.get("severity") == "medium"]
        lc1, lc2, lc3 = st.columns(3)
        with lc1: st.metric("🔴 高度",  len(highs))
        with lc2: st.metric("🟡 中度",  len(mids))
        with lc3: st.metric("📁 総件数", len(issues))
        for iss in highs[:5]:
            st.warning(f"**{iss.get('file','?')}** — {iss.get('message','')}")

# ── システム状態 ──────────────────────────────────────────────────────────────
with tab2:
    if sys_info:
        st.subheader("📊 リソース")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            battery = sys_info.get("battery_percent", 0)
            charging = sys_info.get("charging", False)
            icon = "⚡" if charging else ("🔋" if battery > 20 else "🪫")
            st.metric(f"{icon} バッテリー", f"{battery}%")
        with c2:
            cpu = sys_info.get("cpu_percent", 0)
            st.metric("💻 CPU", f"{cpu:.1f}%")
        with c3:
            mem = sys_info.get("memory_percent", 0)
            st.metric("🧠 メモリ", f"{mem:.1f}%")
        with c4:
            disk_p = sys_info.get("disk_percent", 0)
            disk_u = sys_info.get("disk_used_gb", 0)
            disk_t = sys_info.get("disk_total_gb", 0)
            st.metric("💾 ディスク(C:)", f"{disk_p:.0f}%", help=f"{disk_u}GB / {disk_t}GB")
        with c5:
            st.metric("🌐 ネットワーク", sys_info.get("ssid", "不明"))
        with c6:
            if budget:
                used = budget.get("anthropic", {}).get("used_usd", budget.get("used_usd", 0))
                total = budget.get("anthropic", {}).get("budget_usd", budget.get("budget_usd", 0))
                st.metric("💰 API予算", f"${used:.2f}", help=f"予算: ${total}")

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
with tab3:
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

# ── 実行統計 ─────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("⏱️ パイプライン実行統計")
    if exec_times:
        total_runs = exec_times.get("total_runs", 0)
        last_upd   = exec_times.get("last_updated", "")
        st.caption(f"累計実行回数: **{total_runs}** 回  ｜  最終更新: {last_upd[:16]}")
        pipelines = exec_times.get("pipelines", [])
        if pipelines:
            import pandas as pd
            df = pd.DataFrame(pipelines)
            df = df.rename(columns={
                "name": "パイプライン", "avg_seconds": "平均秒",
                "run_count": "実行回数", "last_run": "最終実行", "last_status": "最終状態"
            })
            st.dataframe(df, use_container_width=True)
    else:
        st.info("実行統計データがありません。")

    if budget:
        st.divider()
        st.subheader("💰 API予算")
        for provider, info in budget.items() if isinstance(budget, dict) else []:
            if isinstance(info, dict):
                used  = info.get("used_usd", 0)
                total = info.get("budget_usd", 0)
                pct   = (used / total * 100) if total else 0
                st.progress(min(pct / 100, 1.0), text=f"{provider}: ${used:.3f} / ${total:.2f} ({pct:.1f}%)")
            else:
                st.write(f"**{provider}:** {info}")

# ── レベルアップ履歴 ──────────────────────────────────────────────────────────
with tab5:
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
