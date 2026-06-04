import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, style

st.set_page_config(page_title="📊 概要KPI", page_icon="📊", layout="wide")
style.inject()

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
api_ratio  = (used_api / lim_api) if lim_api else 0
health_ok  = health and "error" not in (health.get("content", "") or "").lower()[:200]
tv         = ks.get("to_verify", 0) if ks else 0

# ── ヘッダー（致命的問題ありで err）────────────────────────────────────────────
_any_critical = fail_count > 0 or risk_high or api_ratio > 0.8
style.page_header("📊 概要KPI", status="err" if _any_critical else "ok")

# ── KPI グリッド（1行8列・各 metric に優先度クラス）────────────────────────────
style.section_card_start("📊 重要指標")
kc = st.columns(8)

# 各 KPI の優先度を判定
api_prio = "critical" if api_ratio > 0.8 else "warn" if api_ratio > 0.5 else "ok"
kpi_defs = [
    ("⚙️ パイプライン異常", fail_count, "critical" if fail_count > 0 else "ok"),
    ("⚠️ Highリスク",      "あり" if risk_high else "なし", "critical" if risk_high else "ok"),
    ("🎯 CX要改善",        "あり" if cx_issue else "なし", "warn" if cx_issue else "ok"),
    ("💰 追加課金",        f"${used_api:.3f}", api_prio),
    ("🧠 mempalace記憶",   f"{mem_ent} entities", "info"),
    ("📈 Bizdev平均",      f"{avg_score}/10", "info"),
    ("💡 推奨アイデア累計", idea_count, "info"),
    ("🟡 確認待ちタスク",   tv, "warn" if tv >= 5 else "ok"),
]
for col, (label, value, prio) in zip(kc, kpi_defs):
    with col:
        style.kpi_wrap_start(prio)
        if label == "💰 追加課金":
            st.metric(label, value, help=f"予算: ${lim_api}")
        else:
            st.metric(label, value)
        style.kpi_wrap_end()
style.section_card_end()

# ── タスクサマリー（2カラム section_card）──────────────────────────────────────
active_top5 = (ks.get("active_top5") or []) if ks else []
verify_top5 = (ks.get("verify_top5") or []) if ks else []

style.section_card_start("📋 タスクサマリー")
c1, c2, c3, c4, c5 = st.columns(5)
with c1: st.metric("⬜ Open",     ks.get("open", "-") if ks else "-")
with c2: st.metric("🔵 進行中",   ks.get("in_progress", "-") if ks else "-")
with c3: st.metric("🟡 確認待ち", ks.get("to_verify", "-") if ks else "-")
with c4: st.metric("✅ 完了",     ks.get("closed", "-") if ks else "-")
with c5: st.metric("📦 合計",     ks.get("total", "-") if ks else "-")
style.section_card_end()

lcol, rcol = st.columns(2)
with lcol:
    style.section_card_start("🔵 進行中タスク")
    for t in active_top5:
        st.write(f"• `{t.get('id','')}` {t.get('name','')[:40]} — {t.get('assignee','')}")
    if not active_top5:
        st.caption("（なし）")
    style.section_card_end()
with rcol:
    style.section_card_start("🟡 確認待ちタスク",
                             "要対応" if tv >= 5 else "",
                             "warn")
    for t in verify_top5:
        st.write(f"• `{t.get('id','')}` {t.get('name','')[:40]} — {t.get('assignee','')}")
    if not verify_top5:
        st.caption("（なし）")
    if tv >= 5:
        st.warning(f"⚠️ 確認待ち {tv} 件 — 「タスクボード」ページで対応してください")
    style.section_card_end()

# ── パイプライン状況（タブで 全件/失敗のみ に絞り込み）─────────────────────────
style.section_card_start("⚙️ パイプライン状況",
                         "失敗あり" if fail_count else "正常",
                         "err" if fail_count else "ok")
if logs_map:
    sorted_logs = sorted(logs_map.items(),
                         key=lambda x: x[1].get("last_run","") if isinstance(x[1], dict) else "",
                         reverse=True)
    tab_all, tab_fail = st.tabs([f"全件 ({len(sorted_logs)})", f"失敗のみ ({fail_count})"])

    def _render(items):
        if not items:
            st.caption("（該当なし）")
            return
        cols = st.columns(3)
        for i, (name, info) in enumerate(items):
            if not isinstance(info, dict):
                continue
            status = info.get("status", "unknown")
            icon   = "✅" if status == "success" else "❌" if status == "failed" else "❓"
            with cols[i % 3]:
                st.markdown(f"{icon} **{name}**  \n🕐 {info.get('last_run', '-')}")

    with tab_all:
        _render(sorted_logs)
    with tab_fail:
        _render([(n, i) for n, i in sorted_logs
                 if isinstance(i, dict) and i.get("status") == "failed"])
else:
    st.info("パイプラインログ取得中...")
style.section_card_end()

# ── Bizdevスコア推移 ──────────────────────────────────────────────────────────
style.section_card_start("📈 Bizdevスコア推移")
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
style.section_card_end()

# ── ヘルス状態 ────────────────────────────────────────────────────────────────
code_health = data_loader.code_health()
issues = code_health.get("issues", []) if code_health else []
high_issues = [x for x in issues if isinstance(x, dict) and x.get("severity") in ("high", "critical")]
style.section_card_start("🩺 ヘルス状態",
                         "OK" if health_ok else "要確認",
                         "ok" if health_ok else "warn")
ha1, ha2, ha3 = st.columns(3)
with ha1:
    fail_pct = round(fail_count / max(len(logs_map), 1) * 100)
    st.metric("❌ パイプライン失敗率", f"{fail_pct}%")
with ha2:
    st.metric("🔴 コード高度問題", len(high_issues))
with ha3:
    st.metric("🩺 ヘルス", "OK" if health_ok else "要確認")
style.section_card_end()
