import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import data_loader, firebase_client

st.set_page_config(page_title="経営ダッシュボード", page_icon="🏠", layout="wide")
st_autorefresh(interval=60_000, key="home_refresh")

# ── 共通CSS ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .block-container { padding-top: 1.8rem; padding-bottom: 2rem; }
  div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px;
    padding: 12px 16px;
  }
  div[data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 700; }
  div[data-testid="stMetricLabel"] p { font-size: 0.8rem; opacity: 0.75; }
</style>
""", unsafe_allow_html=True)

# ── ヘッダー ──────────────────────────────────────────────────────────────────
st.title("🏠 経営ダッシュボード")
fb_ok    = firebase_client.is_available()
last_upd = data_loader.last_updated()
h1, h2 = st.columns([1, 3])
with h1:
    st.success("Firebase 接続中", icon="🔥") if fb_ok else st.warning("ローカルデータ", icon="⚠️")
with h2:
    st.caption(f"最終更新: {last_upd}" if last_upd else "データ未取得")
st.divider()

# ── データ取得（全て安全にフォールバック）─────────────────────────────────────
biz    = data_loader.business_status() or {}
ks     = data_loader.kanban_summary()  or {}
pl     = data_loader.pipeline_logs()   or {}
budget = data_loader.api_budget()      or {}
sys_info = data_loader.system_info()   or {}

# ── PCシステム状態 ─────────────────────────────────────────────────────────────
st.subheader("🖥️ システム状態")
if sys_info:
    bat = int(sys_info.get("battery_percent") or 0)
    chg = bool(sys_info.get("charging"))
    ssid = str(sys_info.get("ssid") or "不明")
    is_company = "SWing" in ssid or "SWingS" in ssid
    nw_icon = "🏢" if is_company else "🏠"
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("🔋 バッテリー", f"{bat}%" + (" ⚡" if chg else ""))
    with c2: st.metric("💻 CPU",   f"{float(sys_info.get('cpu_percent') or 0):.0f}%")
    with c3: st.metric("🧠 メモリ", f"{float(sys_info.get('memory_percent') or 0):.0f}%")
    with c4:
        disk = float(sys_info.get("disk_percent") or 0)
        st.metric("💾 ディスク", f"{disk:.0f}%")
    with c5: st.metric(f"{nw_icon} NW", ssid)
    if is_company:
        st.error("⛔ 会社ネットワーク（SWing/SWingS）接続中")
else:
    st.info("システム情報取得中...")
st.divider()

# ── 主要KPI ────────────────────────────────────────────────────────────────────
st.subheader("📊 主要KPI")

# 収益
monthly_actual = int(biz.get("monthly_actual") or 0)
monthly_target = int(biz.get("monthly_target") or 20000)
products = biz.get("products") or []
active_products = sum(1 for p in products if isinstance(p, dict)
                      and p.get("status") in ("公開中", "active"))

# タスク
total_tasks  = int(ks.get("total") or 0)
closed_tasks = int(ks.get("closed") or 0)
to_verify    = int(ks.get("to_verify") or 0)
in_progress  = int(ks.get("in_progress") or 0)
completion   = round(closed_tasks / total_tasks * 100) if total_tasks else 0

# パイプライン
logs_map = {}
if isinstance(pl, dict):
    logs_map = pl.get("logs") or pl
    if not isinstance(logs_map, dict):
        logs_map = {}
pl_total = len([v for v in logs_map.values() if isinstance(v, dict)])
pl_fail  = sum(1 for v in logs_map.values() if isinstance(v, dict) and v.get("status") == "failed")
pl_ok    = pl_total - pl_fail
pl_rate  = round(pl_ok / pl_total * 100) if pl_total else 0

# API予算
used_usd  = float(budget.get("used_usd") or budget.get("anthropic", {}).get("used_usd") or 0)
limit_usd = float(budget.get("budget_usd") or budget.get("anthropic", {}).get("budget_usd") or 0)

k1, k2, k3, k4 = st.columns(4)
with k1:
    rev_pct = round(monthly_actual / monthly_target * 100) if monthly_target else 0
    rev_delta = f"目標比 {rev_pct}%"
    st.metric("💰 今月収益", f"¥{monthly_actual:,}", delta=rev_delta,
              delta_color="normal" if rev_pct >= 50 else "inverse")
with k2:
    st.metric("📦 稼働製品", f"{active_products} / {len(products)} 件")
with k3:
    tv_delta = f"確認待ち {to_verify}件" if to_verify >= 5 else None
    st.metric("✅ タスク完了率", f"{completion}%", delta=tv_delta,
              delta_color="inverse" if to_verify >= 5 else "normal")
with k4:
    pl_icon = "🟢" if pl_rate >= 80 else "🟡" if pl_rate >= 50 else "🔴"
    st.metric(f"{pl_icon} パイプライン稼働", f"{pl_rate}%",
              delta=f"失敗 {pl_fail}本" if pl_fail > 0 else None,
              delta_color="inverse" if pl_fail > 0 else "normal")
st.divider()

# ── タスクボード ───────────────────────────────────────────────────────────────
st.subheader("📋 タスクボード")
c1, c2, c3, c4, c5 = st.columns(5)
with c1: st.metric("⬜ Open",     str(ks.get("open") or "-"))
with c2: st.metric("🔵 進行中",   str(in_progress or "-"))
with c3: st.metric("🟡 確認待ち", str(to_verify or "-"))
with c4: st.metric("✅ 完了",     str(closed_tasks or "-"))
with c5: st.metric("📦 合計",     str(total_tasks or "-"))

active_top5 = list(ks.get("active_top5") or [])[:3]
verify_top5 = list(ks.get("verify_top5") or [])[:3]
ta1, ta2 = st.columns(2)
with ta1:
    st.markdown("**🔵 進行中（上位3件）**")
    for t in active_top5:
        if isinstance(t, dict):
            st.write(f"• {t.get('id','')}  {str(t.get('name',''))[:40]} — {t.get('assignee','')}")
    if not active_top5:
        st.caption("（なし）")
with ta2:
    st.markdown("**🟡 確認待ち（上位3件）**")
    for t in verify_top5:
        if isinstance(t, dict):
            st.write(f"• {t.get('id','')}  {str(t.get('name',''))[:40]} — {t.get('assignee','')}")
    if not verify_top5:
        st.caption("（なし）")
if to_verify >= 5:
    st.warning(f"⚠️ 確認待ち {to_verify} 件 — 「タスクボード」ページで対応してください")
st.divider()

# ── パイプライン実行状況 ───────────────────────────────────────────────────────
st.subheader("⚙️ パイプライン実行状況")
if logs_map:
    sorted_logs = sorted(
        logs_map.items(),
        key=lambda x: (x[1].get("last_run", "") if isinstance(x[1], dict) else ""),
        reverse=True
    )
    cols = st.columns(3)
    for i, (name, info) in enumerate(sorted_logs[:12]):
        if not isinstance(info, dict):
            continue
        status = info.get("status", "unknown")
        icon = "✅" if status == "success" else "❌" if status == "failed" else "❓"
        with cols[i % 3]:
            st.markdown(f"{icon} **{name}**  \n🕐 {info.get('last_run', '-')}")
else:
    st.info("パイプラインログ取得中...")
st.divider()

# ── 事業状況 ───────────────────────────────────────────────────────────────────
st.subheader("💼 事業状況・利益予測")
if biz:
    goal = biz.get("management_goal") or {}
    forecast = biz.get("management_forecast") or {}
    b1, b2, b3 = st.columns(3)
    with b1:
        st.markdown("**🎯 経営目標**")
        st.write(f"短期: {goal.get('short') or '未設定'}")
        st.write(f"長期: {goal.get('long') or '未設定'}")
    with b2:
        monthly = forecast.get("monthly_forecast_jpy") or 0
        try:
            st.metric("月次収益予測", f"¥{int(monthly):,}")
        except Exception:
            st.metric("月次収益予測", str(monthly))
    with b3:
        annual = forecast.get("annual_forecast_jpy") or 0
        try:
            st.metric("年次収益予測", f"¥{int(annual):,}")
        except Exception:
            st.metric("年次収益予測", str(annual))
st.divider()

# ── API使用量・課金状況 ────────────────────────────────────────────────────────
st.subheader("💰 API使用量")
budget_icon = "🔴" if (limit_usd and used_usd / limit_usd > 0.8) else \
              "🟡" if (limit_usd and used_usd / limit_usd > 0.5) else "🟢"
a1, a2 = st.columns(2)
with a1:
    st.metric(f"{budget_icon} API消費", f"${used_usd:.3f}",
              help=f"予算: ${limit_usd:.1f}")
    if limit_usd:
        st.progress(min(used_usd / limit_usd, 1.0),
                    text=f"{used_usd/limit_usd*100:.1f}%")
with a2:
    st.info("⚠️ 2026-06-15 から claude -p が従量課金へ移行。パイプラインの呼び出し削減が急務。")
st.divider()

st.caption(
    f"📡 Firebase Pusher（30分毎）  |  "
    f"最終Push: {(firebase_client.get_doc('dashboard','meta') or {}).get('last_updated','-')}"
)
