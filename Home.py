import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import data_loader, firebase_client, style
from utils.data_loader import get_push_log
from utils.style import freshness_banner

st.set_page_config(page_title="BizDash", page_icon="🏠", layout="wide")

# ── 共通スタイル適用 ───────────────────────────────────────────────────────────
style.inject()

# ── 鮮度バナー ─────────────────────────────────────────────────────────────────
_push_log = get_push_log()
st.markdown(
    f'<div style="text-align:right;margin-bottom:4px;">{freshness_banner(_push_log)}</div>',
    unsafe_allow_html=True
)

# ── 全データ取得 ───────────────────────────────────────────────────────────────
fb_ok    = firebase_client.is_available()
last_upd = data_loader.last_updated()
biz      = data_loader.business_status() or {}
ks       = data_loader.kanban_summary()  or {}
pl       = data_loader.pipeline_logs()   or {}
sys_info = data_loader.system_info()     or {}
budget   = data_loader.api_budget()      or {}

# ── 集計（先に算出してヘッダーのステータス判定に使う）─────────────────────────
logs_map = {}
if isinstance(pl, dict):
    tmp = pl.get("logs") or pl
    logs_map = tmp if isinstance(tmp, dict) else {}
pl_total = sum(1 for v in logs_map.values() if isinstance(v, dict))
pl_fail  = sum(1 for v in logs_map.values()
               if isinstance(v, dict) and v.get("status") == "failed")
pl_rate  = round((pl_total - pl_fail) / pl_total * 100) if pl_total else 0

ssid  = str(sys_info.get("ssid") or "不明")
is_co = "SWing" in ssid

# ── ページヘッダー（会社NW or 失敗時に右端ステータスバッジ）───────────────────
hdr_status = "err" if (is_co or pl_fail) else "ok"
style.page_header("🏠 経営ダッシュボード", status=hdr_status)

# ── Firebase接続バナー（横1行・コンパクト）─────────────────────────────────────
if fb_ok:
    st.success(f"🔥 Firebase 接続中　｜　最終更新: {last_upd or '不明'}")
else:
    st.warning("⚠️ ローカルデータ使用中")

# ── システム状態カード ─────────────────────────────────────────────────────────
style.section_card_start("🖥️ システム状態",
                         "会社NW" if is_co else "正常",
                         "err" if is_co else "ok")
if sys_info:
    bat  = int(sys_info.get("battery_percent") or 0)
    chg  = bool(sys_info.get("charging"))
    cpu  = float(sys_info.get("cpu_percent") or 0)
    mem  = float(sys_info.get("memory_percent") or 0)
    disk = float(sys_info.get("disk_percent") or 0)
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
style.section_card_end()

# ── 主要KPI算出 ────────────────────────────────────────────────────────────────
monthly_actual = int(biz.get("monthly_actual") or 0)
monthly_target = int(biz.get("monthly_target") or 20000)
products       = biz.get("products") or []
active_p       = sum(1 for p in products if isinstance(p, dict)
                     and p.get("status") in ("公開中", "active"))

total_tasks  = int(ks.get("total") or 0)
closed_tasks = int(ks.get("closed") or 0)
to_verify    = int(ks.get("to_verify") or 0)
completion   = round(closed_tasks / total_tasks * 100) if total_tasks else 0

# ── 3カラムレイアウト（左4: KPI+タスク / 右2: API+パイプライン）──────────────────
left, right = st.columns([4, 2])

# ── 左カラム: 主要KPI + タスクサマリー（1カードに統合して重複排除）─────────────
with left:
    style.section_card_start("📊 主要KPI ＆ タスクボード")

    # KPI 4指標（重要度クラス適用）
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        style.kpi_wrap_start("info")  # 収益は info
        k1.metric("💰 今月収益", f"¥{monthly_actual:,}",
                  f"目標比 {round(monthly_actual/monthly_target*100) if monthly_target else 0}%")
        style.kpi_wrap_end()
    with k2:
        style.kpi_wrap_start("ok")
        k2.metric("📦 稼働製品", f"{active_p} / {len(products)}")
        style.kpi_wrap_end()
    with k3:
        style.kpi_wrap_start("ok")  # タスク完了は ok
        k3.metric("✅ タスク完了率", f"{completion}%",
                  f"確認待ち {to_verify}件" if to_verify >= 5 else None)
        style.kpi_wrap_end()
    with k4:
        # パイプライン失敗時は err、正常時は ok
        style.kpi_wrap_start("err" if pl_fail else "ok")
        k4.metric("⚙️ パイプライン稼働", f"{pl_rate}%",
                  f"失敗 {pl_fail}本" if pl_fail else None)
        style.kpi_wrap_end()

    # タスクボード（5指標を同じカード内に統合 = 重複排除）
    style.section_title("📋 タスクボード")
    t1, t2, t3, t4, t5 = st.columns(5)
    t1.metric("⬜ Open",     str(ks.get("open") or 0))
    t2.metric("🔵 進行中",   str(ks.get("in_progress") or 0))
    t3.metric("🟡 確認待ち", str(to_verify))
    t4.metric("✅ 完了",     str(closed_tasks))
    t5.metric("📦 合計",     str(total_tasks))

    # 進行中・確認待ち上位リスト
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
    style.section_card_end()

# ── 右カラム: API使用量 + パイプラインサマリー ─────────────────────────────────
with right:
    # API使用量（progress + metric コンパクト表示）
    used  = float(budget.get("used_usd") or
                  (budget.get("anthropic") or {}).get("used_usd") or 0)
    limit = float(budget.get("budget_usd") or
                  (budget.get("anthropic") or {}).get("budget_usd") or 0)
    ratio = (used / limit) if limit else 0
    api_status = "err" if ratio > 0.8 else "warn" if ratio > 0.5 else "ok"
    api_badge  = "高負荷" if ratio > 0.8 else "中" if ratio > 0.5 else "正常"
    style.section_card_start("💰 API使用量", api_badge, api_status)
    st.metric("API消費", f"${used:.3f}", f"予算 ${limit:.1f}")
    if limit:
        st.progress(min(ratio, 1.0), text=f"{ratio*100:.1f}%")
    st.caption("⚠️ 2026-06-15 から claude -p が従量課金へ移行。呼び出し削減が急務。")
    style.section_card_end()

    # パイプラインサマリー（counts の4指標のみ・詳細はリンク）
    pl_s   = data_loader.pipeline_status()
    counts = pl_s.get("counts", {}) if pl_s else {}
    pl_badge_status = "err" if counts.get("failed", 0) else "ok"
    style.section_card_start("⚙️ パイプライン",
                             "失敗あり" if counts.get("failed", 0) else "正常",
                             pl_badge_status)
    if counts:
        p1, p2 = st.columns(2)
        p1.metric("✅ 正常", counts.get("ok", 0))
        p2.metric("❌ 失敗", counts.get("failed", 0))
        p3, p4 = st.columns(2)
        p3.metric("🆕 未実行",
                  counts.get("never_ran", 0) + counts.get("not_registered", 0))
        p4.metric("⏸ 停止", counts.get("stopped", 0))
        st.caption("詳細は「📊 稼働状況」ページで確認できます")
    elif logs_map:
        ok = sum(1 for v in logs_map.values()
                 if isinstance(v, dict) and v.get("status") == "success")
        ng = sum(1 for v in logs_map.values()
                 if isinstance(v, dict) and v.get("status") == "failed")
        st.metric("✅ 正常 / ❌ 失敗", f"{ok} / {ng}")
    else:
        st.info("パイプラインデータ取得中...")
    style.section_card_end()

# ── SYSTEM HEALTH（フローステータス）──────────────────────────────────────────
@st.fragment(run_every=60)
def _system_health_section():
    st.subheader("🖥️ SYSTEM HEALTH")
    try:
        from utils.flow_status_reader import get_flow_status, format_last_run, status_icon
        import pandas as pd
        flow_data = get_flow_status(firebase_client)
        rows = [
            {"フロー": "MaintenanceFlow", "スケジュール": "毎日 21:00",   **flow_data.get("maintenance", {})},
            {"フロー": "StrategyFlow",    "スケジュール": "月・木 21:22", **flow_data.get("strategy",    {})},
            {"フロー": "ContentFlow",     "スケジュール": "火・金 21:22", **flow_data.get("content",     {})},
            {"フロー": "DailyFlow",       "スケジュール": "毎日 21:23",   **flow_data.get("daily",       {})},
        ]
        df = pd.DataFrame([{
            "フロー":       r["フロー"],
            "スケジュール": r["スケジュール"],
            "ステータス":   f'{status_icon(r.get("status"))} {r.get("status", "unknown")}',
            "最終実行":     format_last_run(r.get("last_run")),
            "所要時間":     f'{r.get("duration_seconds")}秒' if r.get("duration_seconds") else "--",
        } for r in rows])
        st.dataframe(df, hide_index=True, use_container_width=True)
        import datetime as _dt
        st.caption(f"最終更新: {_dt.datetime.now().strftime('%H:%M:%S')} (60秒ごと自動更新)")
    except Exception as e:
        st.warning(f"System Health 読み込みエラー: {e}")

_system_health_section()

# ── フッター ───────────────────────────────────────────────────────────────────
st.caption(
    f"📡 Firebase Pusher 30分毎自動実行  ｜  "
    f"最終Push: {(firebase_client.get_doc('dashboard','meta') or {}).get('last_updated','-')}"
)
