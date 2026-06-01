import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import data_loader, firebase_client, style

st.set_page_config(page_title="🏠 ダッシュボード", page_icon="🏠", layout="wide")
st_autorefresh(interval=60_000, key="home_refresh")
style.inject()

st.title("🏠 経営ダッシュボード")
fb_ok    = firebase_client.is_available()
last_upd = data_loader.last_updated()
h1, h2 = st.columns([1, 3])
with h1:
    st.success("Firebase 接続中", icon="🔥") if fb_ok else st.warning("ローカルデータ", icon="⚠️")
with h2:
    st.caption(f"最終更新: {last_upd}" if last_upd else "データ未取得")

# ── 全データ取得 ───────────────────────────────────────────────────────────────
biz    = data_loader.business_status()
ks     = data_loader.kanban_summary()
pl     = data_loader.pipeline_logs()
budget = data_loader.api_budget()

# ── 主要KPI（収益・製品・タスク完了率・パイプライン稼働率）────────────────────
monthly_actual = biz.get("monthly_actual", 0) if biz else 0
monthly_target = biz.get("monthly_target", 20000) if biz else 20000
products       = biz.get("products", []) if biz else []
active_products = sum(1 for p in products if p.get("status") in ("公開中", "active"))

total_tasks  = ks.get("total", 0) if ks else 0
closed_tasks = ks.get("closed", 0) if ks else 0
to_verify    = ks.get("to_verify", 0) if ks else 0
completion   = round(closed_tasks / total_tasks * 100) if total_tasks else 0

logs_map = pl.get("logs", pl) if isinstance(pl, dict) else {}
pl_total = len([v for v in logs_map.values() if isinstance(v, dict)])
pl_ok    = sum(1 for v in logs_map.values() if isinstance(v, dict) and v.get("status") == "success")
pl_rate  = round(pl_ok / pl_total * 100) if pl_total else 0

st.subheader("📌 主要KPI")
k1, k2, k3, k4 = st.columns(4)
with k1:
    rev_pct = round(monthly_actual / monthly_target * 100) if monthly_target else 0
    st.metric("💰 今月収益", f"¥{monthly_actual:,}", delta=f"目標比 {rev_pct}%",
              delta_color="normal" if rev_pct >= 50 else "off")
with k2:
    st.metric("📦 稼働製品", f"{active_products} / {len(products)}")
with k3:
    st.metric("✅ タスク完了率", f"{completion}%",
              delta=f"確認待ち {to_verify}件" if to_verify >= 5 else None,
              delta_color="inverse" if to_verify >= 5 else "normal")
with k4:
    pl_icon = "🟢" if pl_rate >= 80 else "🟡" if pl_rate >= 50 else "🔴"
    st.metric(f"{pl_icon} パイプライン稼働率", f"{pl_rate}%", help=f"{pl_ok} / {pl_total} 成功")

st.divider()

# ── システム状態（バッテリー・CPU・メモリ・NW）─────────────────────────────────
st.subheader("🖥️ システム状態")
sys_info = data_loader.system_info()
if sys_info:
    bat = sys_info.get("battery_percent", 0)
    chg = sys_info.get("charging", False)
    bat_icon = "⚡" if chg else ("🔋" if bat > 20 else "🪫")
    ssid = sys_info.get("ssid", "不明")
    is_company = "SWing" in ssid or "SWingS" in ssid
    nw_icon = "🏢" if is_company else "🏠"
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric(f"{bat_icon} バッテリー", f"{bat}%")
    with c2: st.metric("💻 CPU", f"{sys_info.get('cpu_percent', 0):.0f}%")
    with c3: st.metric("🧠 メモリ", f"{sys_info.get('memory_percent', 0):.0f}%")
    with c4:
        disk_p = sys_info.get("disk_percent", 0)
        st.metric("💾 ディスク(C:)", f"{disk_p:.0f}%",
                  help=f"{sys_info.get('disk_used_gb', 0)}GB / {sys_info.get('disk_total_gb', 0)}GB")
    with c5: st.metric(f"{nw_icon} NW", ssid)
    if is_company:
        st.error("⛔ 会社ネットワーク（SWing/SWingS）接続中 — Claudeの動作を停止します")
else:
    st.info("システム情報がありません")

st.divider()

# ── 今日のタスク上位 ───────────────────────────────────────────────────────────
st.subheader("🎯 注目タスク")
t1, t2 = st.columns(2)
with t1:
    st.markdown("**🔵 進行中（上位3件）**")
    active_top = (ks.get("active_top5") or [])[:3] if ks else []
    for t in active_top:
        st.write(f"• `{t.get('id','')}` {t.get('name','')[:36]} — {t.get('assignee','')}")
    if not active_top:
        st.caption("（進行中タスクなし）")
with t2:
    st.markdown("**🟡 確認待ち（上位3件）**")
    verify_top = (ks.get("verify_top5") or [])[:3] if ks else []
    for t in verify_top:
        st.write(f"• `{t.get('id','')}` {t.get('name','')[:36]} — {t.get('assignee','')}")
    if not verify_top:
        st.caption("（確認待ちタスクなし）")
if to_verify >= 5:
    st.warning(f"⚠️ 確認待ち {to_verify} 件 — 「タスクボード」ページで対応してください")

st.divider()

# ── API使用量・予算 ────────────────────────────────────────────────────────────
st.subheader("💰 API使用量・予算")
if budget:
    providers = [(k, v) for k, v in budget.items() if isinstance(v, dict)]
    if providers:
        cols = st.columns(len(providers))
        for i, (name, info) in enumerate(providers):
            used  = info.get("used_usd", 0)
            limit = info.get("budget_usd", 0)
            pct   = (used / limit * 100) if limit else 0
            col   = "🔴" if pct > 80 else "🟡" if pct > 50 else "🟢"
            with cols[i]:
                st.metric(f"{col} {name}", f"${used:.3f}", help=f"予算: ${limit}")
                st.progress(min(pct / 100, 1.0), text=f"{pct:.1f}%")
    else:
        used  = budget.get("used_usd", 0)
        limit = budget.get("budget_usd", 0)
        pct   = (used / limit * 100) if limit else 0
        icon  = "🔴" if pct > 80 else "🟡" if pct > 50 else "🟢"
        st.metric(f"{icon} API消費", f"${used:.3f}", help=f"予算: ${limit}")
        st.progress(min(pct / 100, 1.0), text=f"{pct:.1f}%")
else:
    st.info("API予算データがありません")

# ── claude -p 課金移行警告 ─────────────────────────────────────────────────────
with st.expander("🔴 claude -p 従量課金移行（2026-06-15〜）", expanded=False):
    st.warning("2026-06-15 から claude -p がAPIクレジット課金に切り替わります。全パイプラインの claude -p 呼び出し削減が急務です。")
    strategies = [
        ("✅ Haiku委譲（閾値9）",            "スコア≤9のタスクは全てHaiku。Sonnetは複雑実装のみ"),
        ("✅ WebSearch/WebFetch はHaiku限定", "HTML全文がコンテキストに積まれるのを防ぐ"),
        ("✅ 同一ファイルを2回読まない",     "初回読み込みで記憶。以降はメモリ参照"),
        ("✅ バッチ委譲原則",                "複数確認作業は1回のHaiku agentにまとめる"),
        ("✅ コードブロック全体を出力しない", "変更差分と結果だけ伝える"),
    ]
    for s, d in strategies:
        st.markdown(f"**{s}**  \n　{d}")

st.divider()
st.caption("📡 Firebase Pusher（30分毎自動実行）  ｜  " +
           f"最終Push: {(firebase_client.get_doc('dashboard', 'meta') or {}).get('last_updated', '-')}")
