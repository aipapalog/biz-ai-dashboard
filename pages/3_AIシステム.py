import streamlit as st
from utils import style
from utils.data_loader_v2 import get_ai_ops, get_meta, get_content, get_system_health, get_push_log

st.set_page_config(page_title="AI・システム | BizDash", layout="wide")
style.inject()

push_log = get_push_log()
st.markdown(f'<div style="text-align:right;">{style.freshness_banner(push_log)}</div>', unsafe_allow_html=True)
st.markdown('<h2 style="color:#cba6f7;">🤖 AI・システム</h2>', unsafe_allow_html=True)

ai_ops = get_ai_ops()
meta = get_meta()
content = get_content()
health = get_system_health()

tab1, tab2, tab3, tab4 = st.tabs(["🔄 自律ループ", "📊 Eval品質", "🧠 Brain同期", "🏢 システム"])

with tab1:
    loop = ai_ops.get("autonomous_loop", {})
    stats = ai_ops.get("agent_run_stats", {})
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**AutonomousLoop**")
        for k, v in list(loop.items())[:15]:
            st.markdown(f'<div class="glass-card"><b>{k}</b>: {str(v)[:100]}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("**エージェント実行統計**")
        for k, v in list(stats.items())[:15]:
            st.markdown(f'<div class="glass-card"><b>{k}</b>: {v}</div>', unsafe_allow_html=True)

with tab2:
    eval_s = meta.get("eval_status", {})
    failure = meta.get("failure_patterns", {})
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Eval状況**")
        for k, v in list(eval_s.items())[:15]:
            st.markdown(f'<div class="glass-card"><b>{k}</b>: {v}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("**障害パターン**")
        for k, v in list(failure.items())[:10]:
            st.markdown(f'<div class="glass-card"><b>{k}</b>: {str(v)[:100]}</div>', unsafe_allow_html=True)

with tab3:
    brain = content.get("sync_brain", {})
    mp = content.get("mempalace", {})
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Brain同期**")
        for k, v in list(brain.items())[:10]:
            st.markdown(f'<div class="glass-card"><b>{k}</b>: {str(v)[:100]}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("**Mempalace**")
        for k, v in list(mp.items())[:10]:
            st.markdown(f'<div class="glass-card"><b>{k}</b>: {str(v)[:100]}</div>', unsafe_allow_html=True)

with tab4:
    flows = health.get("flows", {})
    scheduler = health.get("scheduler", {})
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**フロー一覧**")
        for name, info in flows.items():
            status = info.get("status", "?") if isinstance(info, dict) else str(info)
            css = "flow-badge-ok" if status == "ok" else "flow-badge-err"
            st.markdown(f'<span class="{css}">{name}: {status}</span>', unsafe_allow_html=True)
    with col2:
        st.markdown("**スケジューラ**")
        entries = scheduler.get("entries", [])
        for entry in entries[:20]:
            st.markdown(f'<div class="glass-card" style="font-size:10px;">{str(entry)[:80]}</div>',
                        unsafe_allow_html=True)
