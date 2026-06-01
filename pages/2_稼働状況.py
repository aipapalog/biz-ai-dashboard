import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, style

st.set_page_config(page_title="📊 稼働状況", page_icon="📊", layout="wide")
style.inject()
st.title("📊 稼働状況")
st.caption(f"🔄 30秒毎自動更新  ｜  最終Push: {data_loader.last_updated()}")

sys_info   = data_loader.system_info()
pl_status  = data_loader.pipeline_status()   # PIPELINES_DEF×スケジューラ×ログ統合
loop_data  = data_loader.autonomous_loop()
ds         = data_loader.datasource()

# ── システムリソース ───────────────────────────────────────────────────────────
if sys_info:
    c1,c2,c3,c4,c5 = st.columns(5)
    bat = sys_info.get("battery_percent", 0)
    chg = sys_info.get("charging", False)
    with c1: st.metric("🔋 バッテリー",   f"{bat}%" + (" ⚡" if chg else ""))
    with c2: st.metric("💻 CPU",          f"{sys_info.get('cpu_percent', 0):.1f}%")
    with c3: st.metric("🧠 メモリ",       f"{sys_info.get('memory_percent', 0):.1f}%")
    with c4:
        d_p = sys_info.get("disk_percent", 0)
        d_u = sys_info.get("disk_used_gb", 0)
        d_t = sys_info.get("disk_total_gb", 0)
        st.metric("💾 ディスク(C:)", f"{d_p:.0f}%", help=f"{d_u}GB / {d_t}GB")
    with c5: st.metric("🌐 NW",           sys_info.get("ssid", "不明"))
else:
    st.info("システム情報がありません")
st.divider()

# ── 実施中タスク・Claude Code処理状況 ─────────────────────────────────────────
st.subheader("🔄 実施中タスク・処理")
realtime = ds.get("realtime", {}) if ds else {}
claude   = ds.get("claude_code_status", {}) if ds else {}
if realtime and realtime.get("execution_status"):
    st.info(f"**実行状態:** {realtime.get('execution_status','-')}  ｜  **詳細:** {realtime.get('running_detail','-')}")
elif claude and claude.get("cpu_percent", 0) > 0:
    st.info(f"**Claude Code:** CPU {claude.get('cpu_percent',0):.1f}%  ｜  メモリ {claude.get('memory_mb',0):.0f}MB")
else:
    st.success("✓ 実施中タスクなし（待機中）")
st.divider()

# ── パイプライン統合ステータス（PIPELINES_DEF×スケジューラ×ログ自動突合）────────
st.subheader("⚙️ パイプライン稼働状況")
pipelines = pl_status.get("pipelines", [])
counts    = pl_status.get("counts", {})
upd       = pl_status.get("updated_at", "")
if upd:
    st.caption(f"自動突合: {upd[:16]}  ｜  PIPELINES_DEF定義数: {pl_status.get('total',0)}")

if counts:
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("✅ 正常",    counts.get("ok", 0))
    c2.metric("❌ 失敗",    counts.get("failed", 0))
    c3.metric("🆕 未実行",  counts.get("never_ran", 0) + counts.get("not_registered", 0))
    c4.metric("⏸ 停止中",  counts.get("stopped", 0))
st.divider()

ICON = {"ok":"✅","failed":"❌","never_ran":"🆕","not_registered":"⚠️",
        "stopped":"⏸","integrated":"🔗","unknown":"❓"}

# カテゴリ絞り込み
categories = sorted({p.get("category","") for p in pipelines if p.get("category")})
sel_cat = st.selectbox("カテゴリ絞込", ["すべて"] + categories, key="pl_cat")
filtered = [p for p in pipelines if sel_cat == "すべて" or p.get("category") == sel_cat]
filtered_sorted = sorted(filtered,
    key=lambda p: p.get("log_last_run") or p.get("sched_last_run") or "", reverse=True)

cols = st.columns(3)
for i, p in enumerate(filtered_sorted):
    overall = p.get("overall", "unknown")
    icon    = ICON.get(overall, "❓")
    last    = p.get("log_last_run") or p.get("sched_last_run") or "-"
    with cols[i % 3]:
        with st.expander(f"{icon} **{p['name']}**  🕐{last}", expanded=False):
            st.caption(f"カテゴリ: {p.get('category','')}  ｜  スケジュール: {p.get('schedule','')}")
            # スクリプト・スケジューラ状態
            script_ok = "✅" if p.get("script_exists") else "❌"
            sched_ok  = {"ok":"✅","never":"🆕","not_registered":"⚠️","integrated":"🔗"}.get(
                         p.get("sched_status",""), "❓")
            log_ok    = {"success":"✅","failed":"❌","no_log":"—","unknown":"❓"}.get(
                         p.get("log_status",""), "❓")
            st.write(f"スクリプト{script_ok}  スケジューラ{sched_ok}({p.get('sched_state','')})  ログ{log_ok}")
            if p.get("next_run"):
                st.caption(f"次回: {p['next_run']}")
            if p.get("stop_reason"):
                st.warning(p["stop_reason"])
            if p.get("last_lines"):
                st.code(p["last_lines"][-300:], language=None)
if not filtered:
    st.info("該当するパイプラインがありません")
st.divider()

# ── 自律ループ実行ログ ─────────────────────────────────────────────────────────
st.subheader("🔄 自律ループ実行ログ")
if loop_data:
    total  = loop_data.get("total_lines", 0)
    upd    = loop_data.get("updated_at", "")
    last_e = loop_data.get("last_entry", "")
    st.caption(f"累計ログ行数: **{total:,}** 行  ｜  取得時刻: {upd[:16]}")
    if last_e: st.info(f"**最終エントリ:** {last_e}")
    lines_text = loop_data.get("lines", "")
    if lines_text:
        st.subheader("最新150行")
        st.code(lines_text, language=None)
else:
    st.info("自律ループログがありません")
st.divider()

# ── ディスク使用率 ─────────────────────────────────────────────────────────────
st.subheader("💾 ディスク使用率")
if ds:
    disk_info = ds.get("disk_usage", {})
    if disk_info:
        for drive, info in disk_info.items() if isinstance(disk_info, dict) else []:
            if isinstance(info, dict):
                pct = info.get("percent", 0)
                col = "🔴" if pct > 85 else "🟡" if pct > 70 else "🟢"
                st.write(f"{col} **{drive}**: {pct:.0f}%  ({info.get('used_gb',0):.1f}GB / {info.get('total_gb',0):.1f}GB)")
    else:
        if sys_info:
            d_p = sys_info.get("disk_percent", 0)
            d_u = sys_info.get("disk_used_gb", 0)
            d_t = sys_info.get("disk_total_gb", 0)
            col = "🔴" if d_p > 85 else "🟡" if d_p > 70 else "🟢"
            st.write(f"{col} **C:** {d_p:.0f}%  ({d_u:.1f}GB / {d_t:.1f}GB)")
        else:
            st.info("ディスク情報なし")
else:
    st.info("datasourceデータがありません")
st.divider()

# ── ネットワーク情報 ───────────────────────────────────────────────────────────
st.subheader("🌐 ネットワーク状況")
if sys_info:
    ssid = sys_info.get("ssid", "不明")
    is_company = "SWing" in ssid or "SWingS" in ssid
    icon = "🏢" if is_company else "🏠"
    nw_type = "会社" if is_company else "私用"
    type_col = "red" if is_company else "blue"
    st.metric(f"{icon} 現在のNW", ssid, help=f"種別: {nw_type}")
    if is_company:
        st.error("⛔ 会社ネットワーク（SWing/SWingS）接続中 — Claudeの動作を停止します")
    st.caption("会社NW（swing / 43.x.x.x）接続中はエージェント・パイプラインを自動停止。ネットワーク未接続時も同様。")
else:
    st.info("ネットワーク情報がありません")
