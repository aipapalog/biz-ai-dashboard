import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import data_loader, firebase_client

st.set_page_config(page_title="経営ダッシュボード", page_icon="🏠", layout="wide")

st.markdown("""
<style>
  .block-container { padding-top: 1.8rem; }
  div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px;
    padding: 12px 16px;
  }
  div[data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

st.title("🏠 経営ダッシュボード")

# ── 接続状態 ───────────────────────────────────────────────────────────────────
fb_ok    = firebase_client.is_available()
last_upd = data_loader.last_updated()
if fb_ok:
    st.success(f"🔥 Firebase 接続中　｜　最終更新: {last_upd or '不明'}")
else:
    st.warning("⚠️ ローカルデータ使用中")
st.divider()

# ── 全データ取得 ───────────────────────────────────────────────────────────────
biz      = data_loader.business_status() or {}
ks       = data_loader.kanban_summary()  or {}
pl       = data_loader.pipeline_logs()   or {}
sys_info = data_loader.system_info()     or {}
budget   = data_loader.api_budget()      or {}

# ── システム状態 ───────────────────────────────────────────────────────────────
st.subheader("🖥️ システム状態")
if sys_info:
    bat  = int(sys_info.get("battery_percent") or 0)
    chg  = bool(sys_info.get("charging"))
    cpu  = float(sys_info.get("cpu_percent") or 0)
    mem  = float(sys_info.get("memory_percent") or 0)
    disk = float(sys_info.get("disk_percent") or 0)
    ssid = str(sys_info.get("ssid") or "不明")
    is_co = "SWing" in ssid
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🔋 バッテリー", f"{bat}%" + (" ⚡" if chg else ""))
    c2.metric("💻 CPU", f"{cpu:.0f}%")
    c3.metric("🧠 メモリ", f"{mem:.0f}%")
    c4.metric("💾 ディスク", f"{disk:.0f}%")
    c5.metric("🏠 NW" if not is_co else "🏢 会社NW", ssid)
    if is_co:
        st.error("⛔ 会社ネットワーク接続中")
else:
    st.info("システム情報取得中...")
st.divider()

# ── 主要KPI ────────────────────────────────────────────────────────────────────
st.subheader("📊 主要KPI")

monthly_actual = int(biz.get("monthly_actual") or 0)
monthly_target = int(biz.get("monthly_target") or 20000)
products       = biz.get("products") or []
active_p       = sum(1 for p in products if isinstance(p, dict)
                     and p.get("status") in ("公開中", "active"))

total_tasks  = int(ks.get("total") or 0)
closed_tasks = int(ks.get("closed") or 0)
to_verify    = int(ks.get("to_verify") or 0)
completion   = round(closed_tasks / total_tasks * 100) if total_tasks else 0

logs_map = {}
if isinstance(pl, dict):
    tmp = pl.get("logs") or pl
    logs_map = tmp if isinstance(tmp, dict) else {}
pl_total = sum(1 for v in logs_map.values() if isinstance(v, dict))
pl_fail  = sum(1 for v in logs_map.values()
               if isinstance(v, dict) and v.get("status") == "failed")
pl_rate  = round((pl_total - pl_fail) / pl_total * 100) if pl_total else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("💰 今月収益",
          f"¥{monthly_actual:,}",
          f"目標比 {round(monthly_actual/monthly_target*100) if monthly_target else 0}%")
k2.metric("📦 稼働製品", f"{active_p} / {len(products)}")
k3.metric("✅ タスク完了率", f"{completion}%",
          f"確認待ち {to_verify}件" if to_verify >= 5 else None)
k4.metric("⚙️ パイプライン稼働", f"{pl_rate}%",
          f"失敗 {pl_fail}本" if pl_fail else None)
st.divider()

# ── タスクボード ───────────────────────────────────────────────────────────────
st.subheader("📋 タスクボード")
t1, t2, t3, t4, t5 = st.columns(5)
t1.metric("⬜ Open",     str(ks.get("open") or 0))
t2.metric("🔵 進行中",   str(ks.get("in_progress") or 0))
t3.metric("🟡 確認待ち", str(to_verify))
t4.metric("✅ 完了",     str(closed_tasks))
t5.metric("📦 合計",     str(total_tasks))

active_top = list(ks.get("active_top5") or [])[:3]
verify_top = list(ks.get("verify_top5") or [])[:3]
ta1, ta2 = st.columns(2)
with ta1:
    st.markdown("**🔵 進行中（上位3件）**")
    for t in active_top:
        if isinstance(t, dict):
            st.write(f"• {t.get('id','')}  {str(t.get('name',''))[:40]}")
    if not active_top:
        st.caption("（なし）")
with ta2:
    st.markdown("**🟡 確認待ち（上位3件）**")
    for t in verify_top:
        if isinstance(t, dict):
            st.write(f"• {t.get('id','')}  {str(t.get('name',''))[:40]}")
    if not verify_top:
        st.caption("（なし）")
if to_verify >= 5:
    st.warning(f"⚠️ 確認待ち {to_verify} 件 — タスクボードページで対応してください")
st.divider()

# ── パイプライン（サマリーのみ・詳細は「稼働状況」ページへ）──────────────────────
st.subheader("⚙️ パイプライン")
pl_s = data_loader.pipeline_status()
counts = pl_s.get("counts", {})
if counts:
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("✅ 正常",   counts.get("ok", 0))
    c2.metric("❌ 失敗",   counts.get("failed", 0))
    c3.metric("🆕 未実行", counts.get("never_ran", 0) + counts.get("not_registered", 0))
    c4.metric("⏸ 停止",   counts.get("stopped", 0))
    st.caption("詳細は「📊 稼働状況」ページで確認できます")
elif logs_map:
    # フォールバック: pipeline_status 未取得時
    ok  = sum(1 for v in logs_map.values() if isinstance(v,dict) and v.get("status")=="success")
    ng  = sum(1 for v in logs_map.values() if isinstance(v,dict) and v.get("status")=="failed")
    st.metric("✅ 正常 / ❌ 失敗", f"{ok} / {ng}")
else:
    st.info("パイプラインデータ取得中...")
st.divider()

# ── API使用量 ──────────────────────────────────────────────────────────────────
st.subheader("💰 API使用量")
used  = float(budget.get("used_usd") or
              (budget.get("anthropic") or {}).get("used_usd") or 0)
limit = float(budget.get("budget_usd") or
              (budget.get("anthropic") or {}).get("budget_usd") or 0)
icon  = "🔴" if (limit and used/limit > 0.8) else "🟡" if (limit and used/limit > 0.5) else "🟢"
a1, a2 = st.columns(2)
a1.metric(f"{icon} API消費", f"${used:.3f}", help=f"予算: ${limit:.1f}")
if limit:
    a1.progress(min(used/limit, 1.0), text=f"{used/limit*100:.1f}%")
a2.info("⚠️ 2026-06-15 から claude -p が従量課金へ移行。パイプライン呼び出し削減が急務。")

st.caption(
    f"📡 Firebase Pusher 30分毎自動実行  ｜  "
    f"最終Push: {(firebase_client.get_doc('dashboard','meta') or {}).get('last_updated','-')}"
)
