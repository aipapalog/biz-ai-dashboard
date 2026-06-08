import streamlit as st
from utils import style
from utils.data_loader_v2 import get_business, get_bizdev, get_cx_quality, get_meta, get_push_log

st.set_page_config(page_title="ビジネス | BizDash", layout="wide")
style.inject()

push_log = get_push_log()
st.markdown(f'<div style="text-align:right;">{style.freshness_banner(push_log)}</div>', unsafe_allow_html=True)
st.markdown('<h2 style="color:#cba6f7;">📈 ビジネス</h2>', unsafe_allow_html=True)

business = get_business()
bizdev = get_bizdev()
cx = get_cx_quality()
meta = get_meta()

tab1, tab2, tab3, tab4 = st.tabs(["📊 事業状況", "🚀 BizDev", "🎯 CX品質", "🔄 PDCA"])

with tab1:
    biz_status = business.get("business_status", {})
    if biz_status:
        for k, v in list(biz_status.items())[:20]:
            st.markdown(
                f'<div class="glass-card"><span style="color:#6c7086;">{k}</span><br>'
                f'<span style="color:#cdd6f4;">{v}</span></div>',
                unsafe_allow_html=True
            )
    else:
        st.info("データなし — pusherを実行してください")

with tab2:
    report = bizdev.get("report", {})
    if report:
        for k, v in list(report.items())[:20]:
            st.markdown(
                f'<div class="glass-card"><span style="color:#6c7086;">{k}</span><br>'
                f'<span style="color:#cdd6f4;">{str(v)[:200]}</span></div>',
                unsafe_allow_html=True
            )
    else:
        st.info("BizDevデータなし")

with tab3:
    cx_report = cx.get("cx_report", {})
    levelup = cx.get("levelup_status", {})
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**CXレポート**")
        for k, v in list(cx_report.items())[:10]:
            st.markdown(f'<div class="glass-card"><b>{k}</b>: {v}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("**LevelUp状況**")
        for k, v in list(levelup.items())[:10]:
            st.markdown(f'<div class="glass-card"><b>{k}</b>: {v}</div>', unsafe_allow_html=True)

with tab4:
    pdca = meta.get("pdca", {})
    biz_pdca = meta.get("biz_pdca", {})
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**PDCA**")
        for k, v in list(pdca.items())[:10]:
            st.markdown(f'<div class="glass-card"><b>{k}</b>: {str(v)[:100]}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("**Biz PDCA**")
        for k, v in list(biz_pdca.items())[:10]:
            st.markdown(f'<div class="glass-card"><b>{k}</b>: {str(v)[:100]}</div>', unsafe_allow_html=True)
