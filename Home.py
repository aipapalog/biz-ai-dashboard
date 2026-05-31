import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import data_loader, firebase_client

st.set_page_config(page_title="AI Agent Dashboard", page_icon="🤖", layout="wide")
st_autorefresh(interval=60_000, key="home_refresh")

# ── ヘッダー ──────────────────────────────────────────────────────────────────
st.title("🤖 AI Agent Dashboard")
fb_ok   = firebase_client.is_available()
last_upd = data_loader.last_updated()
h1, h2 = st.columns([1, 3])
with h1:
    st.success("Firebase 接続中", icon="🔥") if fb_ok else st.warning("ローカルデータ", icon="⚠️")
with h2:
    st.caption(f"最終更新: {last_upd}" if last_upd else "データ未取得")
st.divider()

# ── セクション1: PCシステム状態 ───────────────────────────────────────────────
sys_info = data_loader.system_info()
st.subheader("🖥️ PCシステム状態")
if sys_info:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    bat = sys_info.get("battery_percent", 0)
    chg = sys_info.get("charging", False)
    with c1: st.metric("🔋 バッテリー", f"{bat}%" + (" ⚡" if chg else ""))
    with c2: st.metric("💻 CPU",         f"{sys_info.get('cpu_percent', 0):.0f}%")
    with c3: st.metric("🧠 メモリ",      f"{sys_info.get('memory_percent', 0):.0f}%")
    with c4: st.metric("💾 ディスク",    f"{sys_info.get('disk_percent', 0):.0f}%")
    with c5: st.metric("🌐 NW",          sys_info.get("ssid", "不明"))
    with c6:
        budget = data_loader.api_budget()
        used = budget.get("used_usd", budget.get("anthropic", {}).get("used_usd", 0)) if budget else 0
        st.metric("💰 API消費",   f"${used:.3f}")
else:
    st.info("システム情報取得中...")
st.divider()

# ── セクション2: 概要KPI（8項目） ─────────────────────────────────────────────
st.subheader("📊 概要KPI")
ks       = data_loader.kanban_summary()
pl       = data_loader.pipeline_logs()
risk     = data_loader.risk_report()
cx       = data_loader.cx_report()
mem      = data_loader.mempalace()
bt       = data_loader.bizdev_trend()
health   = data_loader.health_check()

# 集計
logs_map    = pl.get("logs", pl) if isinstance(pl, dict) else {}
fail_count  = sum(1 for v in logs_map.values() if isinstance(v, dict) and v.get("status") == "failed")
mem_rows    = mem.get("rows", []) if mem else []
mem_latest  = mem_rows[-1] if mem_rows else {}
mem_ent     = mem_latest.get("entities", "-")
entries     = bt.get("entries", []) if bt else []
avg_score   = round(sum(e.get("score", 0) for e in entries) / len(entries), 1) if entries else 0
idea_count  = len(entries)
# リスク・CX は簡易判定
risk_high   = "HIGH" in (risk.get("content", "") or "").upper()
cx_issue    = "要改善" in (cx.get("content", "") or "") or "改善" in (cx.get("content", "") or "")

k1, k2, k3, k4 = st.columns(4)
k5, k6, k7, k8 = st.columns(4)
with k1:
    st.metric("⚙️ パイプライン異常", fail_count,
              delta="要確認" if fail_count > 0 else None,
              delta_color="inverse" if fail_count > 0 else "normal")
with k2:
    st.metric("⚠️ Highリスク", "あり" if risk_high else "なし")
with k3:
    st.metric("🎯 CX要改善", "あり" if cx_issue else "なし")
with k4:
    budget = data_loader.api_budget()
    used = budget.get("used_usd", budget.get("anthropic", {}).get("used_usd", 0)) if budget else 0
    limit = budget.get("budget_usd", budget.get("anthropic", {}).get("budget_usd", 0)) if budget else 0
    st.metric("💰 追加課金", f"${used:.3f}", help=f"予算: ${limit}")
with k5:
    st.metric("🧠 mempalace記憶", f"{mem_ent} entities")
with k6:
    st.metric("📈 Bizdev平均スコア", f"{avg_score}/10")
with k7:
    st.metric("💡 推奨アイデア累計", idea_count)
with k8:
    tv = ks.get("to_verify", 0) if ks else 0
    st.metric("🟡 確認待ちタスク", tv,
              delta="要対応" if tv >= 5 else None,
              delta_color="inverse" if tv >= 5 else "normal")
st.divider()

# ── セクション3: タスクボード ─────────────────────────────────────────────────
st.subheader("📋 タスクボード")
c1, c2, c3, c4, c5 = st.columns(5)
with c1: st.metric("⬜ Open",    ks.get("open", "-") if ks else "-")
with c2: st.metric("🔵 進行中",  ks.get("in_progress", "-") if ks else "-")
with c3: st.metric("🟡 確認待ち", ks.get("to_verify", "-") if ks else "-")
with c4: st.metric("✅ 完了",    ks.get("closed", "-") if ks else "-")
with c5: st.metric("📦 合計",    ks.get("total", "-") if ks else "-")

active_top5  = (ks.get("active_top5") or []) if ks else []
verify_top5  = (ks.get("verify_top5") or []) if ks else []
ta1, ta2 = st.columns(2)
with ta1:
    st.markdown("**🔵 進行中タスク**")
    for t in active_top5:
        st.write(f"• `{t.get('id','')}` {t.get('name','')[:40]} — {t.get('assignee','')}")
    if not active_top5: st.caption("（なし）")
with ta2:
    st.markdown("**🟡 確認待ちタスク**")
    for t in verify_top5:
        st.write(f"• `{t.get('id','')}` {t.get('name','')[:40]} — {t.get('assignee','')}")
    if not verify_top5: st.caption("（なし）")
    if tv >= 5:
        st.warning(f"⚠️ 確認待ち {tv} 件 — 「タスク」ページで対応してください")
st.divider()

# ── セクション4: パイプライン実行状況 ─────────────────────────────────────────
st.subheader("⚙️ パイプライン実行状況")
if logs_map:
    sorted_logs = sorted(logs_map.items(), key=lambda x: x[1].get("last_run","") if isinstance(x[1],dict) else "", reverse=True)
    cols = st.columns(3)
    for i, (name, info) in enumerate(sorted_logs[:12]):
        if not isinstance(info, dict): continue
        status = info.get("status", "unknown")
        icon   = "✅" if status == "success" else "❌" if status == "failed" else "❓"
        with cols[i % 3]:
            st.markdown(f"{icon} **{name}**  \n🕐 {info.get('last_run', '-')}")
else:
    st.info("パイプラインログ取得中...")
st.divider()

# ── セクション5: ビジネス目標・利益予測 ──────────────────────────────────────
st.subheader("💼 事業状況・経営目標・利益予測")
biz = data_loader.business_status()
if biz:
    goal     = biz.get("management_goal", {})
    forecast = biz.get("management_forecast", {})
    products = biz.get("products", [])
    b1, b2, b3 = st.columns(3)
    with b1:
        st.markdown("**🎯 経営目標**")
        st.write(f"短期: {goal.get('short','未設定')}")
        st.write(f"長期: {goal.get('long','未設定')}")
    with b2:
        monthly = forecast.get("monthly_forecast_jpy", 0)
        st.metric("月次収益予測", f"¥{monthly:,}" if isinstance(monthly,(int,float)) else str(monthly))
    with b3:
        annual = forecast.get("annual_forecast_jpy", 0)
        st.metric("年次収益予測", f"¥{annual:,}" if isinstance(annual,(int,float)) else str(annual))
    if products:
        st.markdown("**📦 製品一覧**")
        for p in products:
            s = p.get("status","?")
            icon = "🟢" if s == "active" else "🟡" if s in ("pending","公開中") else "🔴"
            rev  = p.get("monthly_revenue", 0)
            st.write(f"{icon} **{p.get('name','')}** — {p.get('platform','')} ¥{rev:,}/月")
st.divider()

# ── セクション6: Bizdevスコア推移 ────────────────────────────────────────────
st.subheader("📈 Bizdevスコア推移")
if entries:
    import pandas as pd
    df = pd.DataFrame(entries)
    if "date" in df.columns and "score" in df.columns:
        df_chart = df.groupby("date")["score"].mean().reset_index()
        df_chart.columns = ["日付", "平均スコア"]
        st.line_chart(df_chart.set_index("日付"))
    st.caption(f"累計 {idea_count} アイデア・平均スコア {avg_score}/10")
else:
    st.info("Bizdevスコアデータがありません")
st.divider()

# ── セクション7: ネットワーク状況 ─────────────────────────────────────────────
st.subheader("🌐 ネットワーク状況")
if sys_info:
    n1, n2 = st.columns(2)
    with n1:
        ssid = sys_info.get("ssid", "不明")
        is_company = "SWing" in ssid or "SWingS" in ssid
        icon = "🏢" if is_company else "🏠"
        st.metric(f"{icon} 接続NW", ssid)
        if is_company:
            st.error("⛔ 会社ネットワーク接続中 — Claude動作停止中")
    with n2:
        st.write(f"**CPU:** {sys_info.get('cpu_percent',0):.1f}%")
        st.write(f"**メモリ:** {sys_info.get('memory_percent',0):.1f}%")
        st.write(f"**ディスク(C:):** {sys_info.get('disk_percent',0):.0f}% "
                 f"({sys_info.get('disk_used_gb',0):.1f}GB / {sys_info.get('disk_total_gb',0):.1f}GB)")
st.divider()

# ── セクション8: mempalace × ナレッジ成長 ─────────────────────────────────────
st.subheader("🧠 mempalace × ナレッジ成長")
if mem_rows:
    import pandas as pd
    df_m = pd.DataFrame(mem_rows)
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("ルーム数",      mem_latest.get("rooms", "-"))
    with m2: st.metric("エンティティ数", mem_latest.get("entities", "-"))
    with m3: st.metric("トリプル数",     mem_latest.get("triples", "-"))
    if "date" in df_m.columns:
        num_cols = [c for c in df_m.columns if c != "date"]
        try:
            for c in num_cols: df_m[c] = pd.to_numeric(df_m[c], errors="coerce")
            st.line_chart(df_m.set_index("date")[num_cols])
        except Exception: pass
else:
    st.info("Mempalaceデータなし")
st.divider()

# ── セクション9: エージェント・パイプライン健全性 ────────────────────────────
st.subheader("🩺 エージェント・パイプライン健全性")
health_content = health.get("content","") if health else ""
hc = data_loader.code_health()
issues = hc.get("issues", []) if hc else []
high_issues = [x for x in issues if isinstance(x,dict) and x.get("severity") in ("high","critical")]
ha1, ha2, ha3 = st.columns(3)
with ha1:
    fail_pct = round(fail_count / max(len(logs_map), 1) * 100)
    st.metric("❌ パイプライン失敗率", f"{fail_pct}%")
with ha2: st.metric("🔴 コード高度問題", len(high_issues))
with ha3:
    health_ok = health and "error" not in health_content.lower()[:200]
    st.metric("🩺 ヘルス", "OK" if health_ok else "要確認")
if health_content:
    with st.expander("ヘルスチェック詳細", expanded=False):
        st.markdown(health_content[:1000])
st.divider()

# ── セクション10: プラットフォーム監視 ───────────────────────────────────────
st.subheader("🔍 プラットフォーム監視（待ち状態）")
pf = data_loader.pf_watch()
if pf:
    watches = pf.get("watches", pf) if isinstance(pf,dict) else []
    if isinstance(watches, dict): watches = list(watches.values())
    if isinstance(watches, list) and watches:
        cols = st.columns(min(len(watches), 4))
        for i, item in enumerate(watches[:4]):
            if not isinstance(item,dict): continue
            plat   = item.get("platform", item.get("name","?"))
            status = item.get("status","?")
            icon   = "✅" if status in ("ok","active","normal") else "⚠️" if status == "pending" else "❌"
            with cols[i % 4]:
                st.metric(f"{icon} {plat}", status)
    else:
        for k, v in (pf.items() if isinstance(pf,dict) else []):
            if isinstance(v,dict):
                st.write(f"• **{k}**: {v.get('status','?')}")
else:
    st.info("プラットフォームデータなし")
