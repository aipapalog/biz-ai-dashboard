import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import data_loader, firebase_client

st.set_page_config(page_title="📡 API使用量", page_icon="📡", layout="wide")
st_autorefresh(interval=60_000, key="home_refresh")

st.title("📡 API使用量モニター")
fb_ok = firebase_client.is_available()
last_upd = data_loader.last_updated()
h1, h2 = st.columns([1, 3])
with h1:
    st.success("Firebase 接続中", icon="🔥") if fb_ok else st.warning("ローカルデータ", icon="⚠️")
with h2:
    st.caption(f"最終更新: {last_upd}" if last_upd else "データ未取得")

# ── バッテリー・システムリソース（常時上部表示）─────────────────────────────────
sys_info = data_loader.system_info()
if sys_info:
    bat = sys_info.get("battery_percent", 0)
    chg = sys_info.get("charging", False)
    bat_icon = "⚡" if chg else ("🔋" if bat > 20 else "🪫")
    bat_col = "normal" if bat > 20 else "inverse"
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric(f"{bat_icon} バッテリー", f"{bat}%")
    with c2: st.metric("💻 CPU", f"{sys_info.get('cpu_percent', 0):.0f}%")
    with c3: st.metric("🧠 メモリ", f"{sys_info.get('memory_percent', 0):.0f}%")
    with c4:
        disk_p = sys_info.get("disk_percent", 0)
        disk_u = sys_info.get("disk_used_gb", 0)
        disk_t = sys_info.get("disk_total_gb", 0)
        st.metric("💾 ディスク(C:)", f"{disk_p:.0f}%", help=f"{disk_u}GB / {disk_t}GB")
    with c5:
        ssid = sys_info.get("ssid", "不明")
        is_company = "SWing" in ssid or "SWingS" in ssid
        nw_icon = "🏢" if is_company else "🏠"
        st.metric(f"{nw_icon} NW", ssid)
    if is_company:
        st.error("⛔ 会社ネットワーク接続中 — Claude動作停止中")

st.divider()

# ── API使用量・予算 ────────────────────────────────────────────────────────────
st.subheader("💰 API使用量・予算")
budget = data_loader.api_budget()
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

st.divider()

# ── claude -p 課金移行（2026-06-15） ──────────────────────────────────────────
st.subheader("🔴 claude -p 従量課金移行（2026-06-15〜）")
st.warning("2026-06-15 から claude -p がAPIクレジット課金に切り替わります。全パイプラインの claude -p 呼び出し削減が急務です。")
strategies = [
    ("✅ Haiku委譲（閾値9）",         "スコア≤9のタスクは全てHaiku。Sonnetは複雑実装のみ"),
    ("✅ WebSearch/WebFetch はHaiku限定", "HTML全文がコンテキストに積まれるのを防ぐ"),
    ("✅ 同一ファイルを2回読まない",    "初回読み込みで記憶。以降はメモリ参照"),
    ("✅ バッチ委譲原則",               "複数確認作業は1回のHaiku agentにまとめる"),
    ("✅ コードブロック全体を出力しない", "変更差分と結果だけ伝える"),
]
for s, d in strategies:
    st.markdown(f"**{s}**  \n　{d}")

st.divider()

# ── Pusher実行状況 ─────────────────────────────────────────────────────────────
st.subheader("🔄 Firebase Pusher（30分毎自動実行）")
meta = firebase_client.get_doc("dashboard", "meta")
if meta:
    st.caption(f"最終Push: {meta.get('last_updated', '-')}")
else:
    st.caption("Pusherが未実行またはFirebase接続エラー")
st.code("cd .claude/scripts/agents && python firebase_dashboard_pusher.py", language="bash")
