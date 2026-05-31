import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import data_loader, firebase_client

st.set_page_config(page_title="AI Agent Dashboard", page_icon="🤖", layout="wide")
st_autorefresh(interval=60_000, key="home_refresh")

# ── ヘッダー ──────────────────────────────────────────────────────────────────
st.title("🤖 AI Agent Dashboard")

fb_ok = firebase_client.is_available()
last_upd = data_loader.last_updated()
col_fb, col_upd = st.columns([1, 3])
with col_fb:
    if fb_ok:
        st.success("Firebase 接続中", icon="🔥")
    else:
        st.warning("ローカルデータ使用中", icon="⚠️")
with col_upd:
    if last_upd:
        st.caption(f"最終更新: {last_upd}")

st.divider()

# ── システム状態（バッテリー・ネットワーク）────────────────────────────────────
sys_info = data_loader.system_info()
if sys_info:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        battery = sys_info.get("battery_percent", 0)
        charging = sys_info.get("charging", False)
        icon = "⚡" if charging else ("🔋" if battery > 20 else "🪫")
        st.metric(f"{icon} バッテリー", f"{battery}%", delta="充電中" if charging else None)
    with c2:
        st.metric("🌐 ネットワーク", sys_info.get("ssid", "不明"))
    with c3:
        st.metric("💻 CPU", f"{sys_info.get('cpu_percent', 0):.0f}%")
    with c4:
        st.metric("🧠 メモリ", f"{sys_info.get('memory_percent', 0):.0f}%")
    st.divider()

# ── Kanban KPI ────────────────────────────────────────────────────────────────
tasks = data_loader.kanban_tasks()
status_counts = {"open": 0, "in_progress": 0, "to_verify": 0, "closed": 0}
for t in tasks:
    s = t.get("status", "open")
    if s in status_counts:
        status_counts[s] += 1

st.subheader("📋 タスク状況")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Open", status_counts["open"])
with c2:
    st.metric("進行中", status_counts["in_progress"])
with c3:
    tv = status_counts["to_verify"]
    delta_color = "inverse" if tv >= 5 else "normal"
    st.metric("確認待ち", tv, delta="⚠️ 多い" if tv >= 5 else None, delta_color=delta_color)
with c4:
    st.metric("完了", status_counts["closed"])

# ── 直近の in_progress タスク ────────────────────────────────────────────────
in_progress = [t for t in tasks if t.get("status") == "in_progress"]
if in_progress:
    st.subheader("🚀 進行中タスク")
    for t in in_progress[:5]:
        priority = t.get("priority", "")
        p_icon = "🔴" if priority == "high" else ("🟡" if priority == "medium" else "⚪")
        st.markdown(f"{p_icon} **{t.get('title', '(タイトルなし)')}**  \n"
                    f"担当: {t.get('assignee', '-')} ／ 期限: {t.get('due_date', '-')}")

# ── to_verify タスク（5件以上で警告）────────────────────────────────────────
to_verify = [t for t in tasks if t.get("status") == "to_verify"]
if len(to_verify) >= 5:
    st.warning(f"⚠️ 確認待ちタスクが {len(to_verify)} 件あります。「タスク」ページで確認してください。", icon="🔔")

# ── ビジネス目標サマリー ──────────────────────────────────────────────────────
biz = data_loader.business_status()
if biz:
    st.divider()
    st.subheader("💼 経営目標")
    forecast = biz.get("management_forecast", {})
    goal = biz.get("management_goal", {})
    c1, c2 = st.columns(2)
    with c1:
        monthly = forecast.get("monthly_forecast_jpy", 0)
        due = forecast.get("monthly_due", "-")
        st.metric("月次収益予測", f"¥{monthly:,}" if monthly else "未設定", help=f"期限: {due}")
    with c2:
        st.caption("短期目標")
        st.write(goal.get("short", "未設定"))

# ── パイプラインログ（直近5件）────────────────────────────────────────────────
pl = data_loader.pipeline_logs()
if pl:
    st.divider()
    st.subheader("⚙️ 最近のパイプライン実行")
    recent = sorted(pl.items(), key=lambda x: x[1].get("last_run", ""), reverse=True)[:5]
    for name, info in recent:
        status = info.get("status", "unknown")
        icon = "✅" if status == "success" else ("❌" if status == "failed" else "⏸")
        st.markdown(f"{icon} **{name}** — {info.get('last_run', '-')}")
