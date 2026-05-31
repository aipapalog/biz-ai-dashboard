import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader

st.set_page_config(page_title="📊 概要KPI", page_icon="📊", layout="wide")
st_autorefresh(interval=60_000, key="kpi_refresh")
st.title("📊 概要KPI")

ks     = data_loader.kanban_summary()
pl     = data_loader.pipeline_logs()
risk   = data_loader.risk_report()
cx     = data_loader.cx_report()
mem    = data_loader.mempalace()
bt     = data_loader.bizdev_trend()
health = data_loader.health_check()
budget = data_loader.api_budget()

# ── 集計 ─────────────────────────────────────────────────────────────────────
logs_map   = pl.get("logs", pl) if isinstance(pl, dict) else {}
fail_count = sum(1 for v in logs_map.values() if isinstance(v, dict) and v.get("status") == "failed")
mem_rows   = mem.get("rows", []) if mem else []
mem_latest = mem_rows[-1] if mem_rows else {}
mem_ent    = mem_latest.get("entities", "-")
entries    = bt.get("entries", []) if bt else []
avg_score  = round(sum(e.get("score", 0) for e in entries) / len(entries), 1) if entries else 0
idea_count = len(entries)
risk_high  = "HIGH" in (risk.get("content", "") or "").upper()
cx_issue   = "要改善" in (cx.get("content", "") or "") or "改善" in (cx.get("content", "") or "")
used_api   = budget.get("used_usd", budget.get("anthropic", {}).get("used_usd", 0)) if budget else 0
lim_api    = budget.get("budget_usd", budget.get("anthropic", {}).get("budget_usd", 0)) if budget else 0
health_ok  = health and "error" not in (health.get("content", "") or "").lower()[:200]
tv         = ks.get("to_verify", 0) if ks else 0

# ── KPI グリッド ──────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k5, k6, k7, k8 = st.columns(4)
with k1:
    st.metric("⚙️ パイプライン異常", fail_count, delta="要確認" if fail_count > 0 else None, delta_color="inverse" if fail_count > 0 else "normal")
with k2: st.metric("⚠️ Highリスク",      "あり" if risk_high else "なし")
with k3: st.metric("🎯 CX要改善",        "あり" if cx_issue else "なし")
with k4: st.metric("💰 追加課金",        f"${used_api:.3f}", help=f"予算: ${lim_api}")
with k5: st.metric("🧠 mempalace記憶",   f"{mem_ent} entities")
with k6: st.metric("📈 Bizdev平均スコア", f"{avg_score}/10")
with k7: st.metric("💡 推奨アイデア累計", idea_count)
with k8:
    st.metric("🟡 確認待ちタスク", tv, delta="要対応" if tv >= 5 else None, delta_color="inverse" if tv >= 5 else "normal")
st.divider()

# ── タスクサマリー ─────────────────────────────────────────────────────────────
st.subheader("📋 タスクサマリー")
c1, c2, c3, c4, c5 = st.columns(5)
with c1: st.metric("⬜ Open",    ks.get("open", "-") if ks else "-")
with c2: st.metric("🔵 進行中",  ks.get("in_progress", "-") if ks else "-")
with c3: st.metric("🟡 確認待ち", ks.get("to_verify", "-") if ks else "-")
with c4: st.metric("✅ 完了",    ks.get("closed", "-") if ks else "-")
with c5: st.metric("📦 合計",    ks.get("total", "-") if ks else "-")

active_top5 = (ks.get("active_top5") or []) if ks else []
verify_top5 = (ks.get("verify_top5") or []) if ks else []
ta1, ta2 = st.columns(2)
with ta1:
    st.markdown("**🔵 進行中タスク**")
    for t in active_top5: st.write(f"• `{t.get('id','')}` {t.get('name','')[:40]} — {t.get('assignee','')}")
    if not active_top5: st.caption("（なし）")
with ta2:
    st.markdown("**🟡 確認待ちタスク**")
    for t in verify_top5: st.write(f"• `{t.get('id','')}` {t.get('name','')[:40]} — {t.get('assignee','')}")
    if not verify_top5: st.caption("（なし）")
    if tv >= 5: st.warning(f"⚠️ 確認待ち {tv} 件 — 「タスクボード」ページで対応してください")
st.divider()

# ── パイプライン異常 ───────────────────────────────────────────────────────────
st.subheader("⚙️ パイプライン状況")
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

# ── Bizdevスコア推移 ──────────────────────────────────────────────────────────
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

# ── ヘルス状態 ────────────────────────────────────────────────────────────────
st.subheader("🩺 ヘルス状態")
code_health = data_loader.code_health()
issues = code_health.get("issues", []) if code_health else []
high_issues = [x for x in issues if isinstance(x,dict) and x.get("severity") in ("high","critical")]
ha1, ha2, ha3 = st.columns(3)
with ha1:
    fail_pct = round(fail_count / max(len(logs_map), 1) * 100)
    st.metric("❌ パイプライン失敗率", f"{fail_pct}%")
with ha2: st.metric("🔴 コード高度問題", len(high_issues))
with ha3: st.metric("🩺 ヘルス", "OK" if health_ok else "要確認")
