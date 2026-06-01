import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, style

st.set_page_config(page_title="💼 事業状況", page_icon="💼", layout="wide")
style.inject()
st.title("💼 事業状況・経営目標・利益予測")

biz = data_loader.business_status()
pf  = data_loader.pf_watch()

if not biz:
    st.info("business_status.json が読み込めていません。")
    st.stop()

goal           = biz.get("management_goal", {})
forecast       = biz.get("management_forecast", {})
products       = biz.get("products", [])
web_assets     = biz.get("web_assets", [])
expenses       = biz.get("expenses", [])
monthly_actual = biz.get("monthly_actual", 0)
monthly_target = biz.get("monthly_target", 20000)
annual_target  = biz.get("annual_target", 300000)
biz_note       = biz.get("note", "")

# ── 経営目標 ──────────────────────────────────────────────────────────────────
st.subheader("🎯 経営目標")
g1, g2 = st.columns(2)
with g1:
    st.markdown("**短期目標**")
    st.write(goal.get("short", "未設定"))
with g2:
    st.markdown("**長期目標**")
    st.write(goal.get("long", "未設定"))
st.divider()

# ── 収益進捗・予測 ────────────────────────────────────────────────────────────
st.subheader("📈 収益進捗・予測")
prog_pct = min(monthly_actual / monthly_target * 100, 100) if monthly_target else 0
prog_icon = "🟢" if prog_pct >= 80 else "🟡" if prog_pct >= 30 else "🔴"
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("今月実績", f"¥{monthly_actual:,}", help=f"目標: ¥{monthly_target:,}")
with c2: st.metric("月次目標", f"¥{monthly_target:,}")
with c3: st.metric("年次目標", f"¥{annual_target:,}")
with c4:
    fixed  = sum(e.get("amount_jpy", 0) for e in expenses if e.get("cycle") == "monthly")
    profit = monthly_actual - fixed
    st.metric("利益（今月）", f"¥{profit:,}", help=f"固定費: ¥{fixed:,}")
st.progress(prog_pct / 100, text=f"{prog_icon} 月次進捗: {prog_pct:.1f}%")

fc_monthly = forecast.get("monthly_forecast_jpy", 0)
fc_annual  = forecast.get("annual_forecast_jpy", 0)
fc_note    = forecast.get("note", "")
if fc_monthly or fc_annual:
    p1, p2 = st.columns(2)
    with p1: st.metric("月次収益予測", f"¥{fc_monthly:,}" if isinstance(fc_monthly, (int, float)) else str(fc_monthly))
    with p2: st.metric("年次収益予測", f"¥{fc_annual:,}"  if isinstance(fc_annual,  (int, float)) else str(fc_annual))
    if fc_note: st.caption(fc_note)
if biz_note: st.info(biz_note)
st.divider()

# ── 製品一覧 ──────────────────────────────────────────────────────────────────
st.subheader("📦 製品一覧")
if products:
    for p in products:
        status = p.get("status", "?")
        icon   = "🟢" if status in ("公開中", "active") else ("🟡" if status in ("審査中", "審査待ち", "pending") else "🔴")
        rev    = p.get("monthly_revenue", 0)
        with st.expander(f"{icon} **{p.get('name','?')}** — {p.get('platform','-')}  ¥{rev:,}/月"):
            c1, c2, c3 = st.columns(3)
            with c1:
                price = p.get("price_jpy", 0)
                st.metric("価格", f"¥{price:,}" if isinstance(price, (int, float)) else str(price))
            with c2:
                st.metric("月次収益", f"¥{rev:,}" if isinstance(rev, (int, float)) else str(rev))
            with c3:
                st.write(f"**ステータス:** {status}")
            if p.get("blocker"): st.warning(f"⏳ {p['blocker']}")
            if p.get("todo"):    st.info(f"★ {p['todo']}")
else:
    st.info("製品データなし")

# ── ウェブ資産 ────────────────────────────────────────────────────────────────
if web_assets:
    st.divider()
    st.subheader("🌐 ウェブ資産")
    for a in web_assets:
        s    = a.get("status", "")
        icon = "🟢" if s == "公開中" else "🔴"
        url  = a.get("url", "")
        note = a.get("note", "")
        line = f"{icon} **{a.get('name','')}** ({a.get('platform','')}) — {s}"
        if url:  line += f"  [{url}]({url})"
        if note: line += f"  _{note}_"
        st.markdown(line)

# ── 経費一覧 ──────────────────────────────────────────────────────────────────
if expenses:
    st.divider()
    st.subheader("💸 経費一覧")
    for e in expenses:
        cycle = {"monthly": "月額固定", "per_sale": "売上時のみ"}.get(e.get("cycle", ""), e.get("cycle", ""))
        amt   = e.get("amount_jpy", 0)
        st.write(f"• **{e.get('name','')}** {cycle} ¥{amt:,}  {e.get('note','')}")

st.divider()

# ── プラットフォーム監視 ──────────────────────────────────────────────────────
st.subheader("🔍 プラットフォーム監視（待ち状態）")
if pf:
    watches = pf.get("watches", pf) if isinstance(pf, dict) else []
    if isinstance(watches, dict): watches = list(watches.values())
    if isinstance(watches, list) and watches:
        cols = st.columns(min(len(watches), 4))
        for i, item in enumerate(watches[:4]):
            if not isinstance(item, dict): continue
            plat   = item.get("platform", item.get("name", "?"))
            status = item.get("status", "?")
            icon   = "✅" if status in ("ok", "active", "normal") else "⚠️" if status == "pending" else "❌"
            with cols[i % 4]:
                st.metric(f"{icon} {plat}", status)
        for item in watches[4:]:
            if isinstance(item, dict):
                plat   = item.get("platform", item.get("name", "?"))
                status = item.get("status", "?")
                icon   = "✅" if status in ("ok", "active", "normal") else "⚠️" if status == "pending" else "❌"
                st.write(f"{icon} **{plat}**: {status}")
    else:
        for k, v in (pf.items() if isinstance(pf, dict) else []):
            if isinstance(v, dict):
                st.write(f"• **{k}**: {v.get('status', '?')}")
else:
    st.info("プラットフォームデータなし")
