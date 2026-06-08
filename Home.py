import streamlit as st
from utils import style
from utils.data_loader_v2 import (
    get_system_health, get_tasks, get_finance, get_meta, get_push_log
)

st.set_page_config(page_title="BizDash", page_icon="📊", layout="wide")
style.inject()

# --- 鮮度バナー ---
push_log = get_push_log()
freshness_html = style.freshness_banner(push_log)
st.markdown(
    f'<div style="text-align:right;margin-bottom:8px;">{freshness_html}</div>',
    unsafe_allow_html=True
)

# --- ヘッダー ---
st.markdown('<h1 style="color:#cba6f7;margin-bottom:4px;">📊 BizDash</h1>', unsafe_allow_html=True)

# --- アラートバナー ---
health = get_system_health()
alerts = health.get("alerts", [])
tasks = get_tasks()
high = tasks.get("high_priority", [])

if alerts or high:
    items = alerts + [f"High: {t}" for t in high[:3]]
    alert_text = " &nbsp;|&nbsp; ".join(str(x) for x in items[:5])
    st.markdown(f'<div class="glass-alert-red">🔴 {alert_text}</div>', unsafe_allow_html=True)

# --- KPIカード ---
finance = get_finance()
meta = get_meta()
flows = health.get("flows", {})
ok_flows = sum(1 for v in flows.values() if isinstance(v, dict) and v.get("status") == "ok")
total_flows = len(flows)
budget = finance.get("api_budget", {})
budget_pct = budget.get("remaining_pct", 0) if isinstance(budget, dict) else 0
eval_s = meta.get("eval_status", {})
success_rate = eval_s.get("success_rate", 0) if isinstance(eval_s, dict) else 0
in_progress = tasks.get("in_progress", 0)

kpi_color = {"pipeline": "#a6e3a1", "kanban": "#89b4fa", "budget": "#f9e2af", "eval": "#cba6f7"}

col1, col2, col3, col4 = st.columns(4)
for col, label, value, unit, color in [
    (col1, "パイプライン", f"{ok_flows}/{total_flows}", "稼働中", kpi_color["pipeline"]),
    (col2, "Kanban",      str(in_progress),              "進行中", kpi_color["kanban"]),
    (col3, "API予算",     f"{int(budget_pct)}%",          "残余",   kpi_color["budget"]),
    (col4, "Eval成功率",  f"{int(success_rate)}%",        "",       kpi_color["eval"]),
]:
    with col:
        st.markdown(
            f'<div class="glass-kpi">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value" style="color:{color};">{value}</div>'
            f'<div class="kpi-label">{unit}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

# --- System Health ---
st.markdown("---")
st.markdown("**⚙️ System Health**")
badges_html = ""
for name, info in flows.items():
    status = info.get("status", "unknown") if isinstance(info, dict) else "unknown"
    css = "flow-badge-ok" if status == "ok" else ("flow-badge-err" if status == "error" else "flow-badge-warn")
    icon = "✓" if status == "ok" else "✗"
    badges_html += f'<span class="{css}">{name} {icon}</span>'
if badges_html:
    st.markdown(
        f'<div class="glass-card" style="margin-top:8px;">{badges_html}</div>',
        unsafe_allow_html=True
    )
else:
    st.markdown(
        '<div class="glass-alert-yellow">⬜ フロー情報なし — pusherを実行してください</div>',
        unsafe_allow_html=True
    )
