import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, style

st.set_page_config(page_title="🚨 要対応", page_icon="🚨", layout="wide")

# ── データ取得 ─────────────────────────────────────────────────────────────────
ks       = data_loader.kanban_summary()
pl       = data_loader.pipeline_status()
risk     = data_loader.risk_report()
cx       = data_loader.cx_report()
budget   = data_loader.api_budget()
health   = data_loader.health_check()
biz      = data_loader.business_status()
sys_info = data_loader.system_info()
ch       = data_loader.code_health()
bt       = data_loader.bizdev_trend()

# ── 集計・判定 ─────────────────────────────────────────────────────────────────
counts   = pl.get("counts", {}) if pl else {}
fail_n   = counts.get("failed", 0)
tv       = ks.get("to_verify", 0) if ks else 0

risk_high = "HIGH" in (risk.get("content", "") or "").upper() if risk else False
cx_issue  = ("要改善" in (cx.get("content", "") or "")) if cx else False

used_api = budget.get("used_usd", (budget.get("anthropic", {}) or {}).get("used_usd", 0)) if budget else 0
lim_api  = budget.get("budget_usd", (budget.get("anthropic", {}) or {}).get("budget_usd", 0)) if budget else 0
api_ratio = (used_api / lim_api) if lim_api else 0

issues     = ch.get("issues", []) if ch else []
high_iss   = [x for x in issues if isinstance(x, dict) and x.get("severity") in ("high", "critical")]
health_ok  = health and "error" not in (health.get("content", "") or "").lower()[:200]

ssid     = str(sys_info.get("ssid", "")) if sys_info else ""
is_co    = "SWing" in ssid

# 致命度の高い順に「要対応アラート」を組み立てる
alerts = []   # (重要度: "critical"/"warn", 文言, 誘導先ページ)
if is_co:
    alerts.append(("critical", "🏢 会社ネットワーク接続中 — エージェント・パイプラインは自動停止します", "📊 稼働状況"))
if fail_n:
    alerts.append(("critical", f"⚙️ パイプライン失敗 {fail_n} 本 — ログを確認してください", "📊 稼働状況"))
if risk_high:
    alerts.append(("critical", "⚠️ Highリスクあり — リスクレポートを確認してください", "😊 CX・品質"))
if api_ratio > 0.8:
    alerts.append(("critical", f"💰 API予算 {api_ratio*100:.0f}% 消費 — 呼び出し削減が急務", "😊 CX・品質"))
if tv >= 5:
    alerts.append(("warn", f"👀 確認待ちタスク {tv} 件 — 承認・差し戻しを判断してください", "🗂️ タスクボード"))
if high_iss:
    alerts.append(("warn", f"🔴 コード高度問題 {len(high_iss)} 件", "😊 CX・品質"))
if cx_issue:
    alerts.append(("warn", "🎯 CXに要改善あり", "😊 CX・品質"))
if api_ratio > 0.5 and api_ratio <= 0.8:
    alerts.append(("warn", f"💰 API予算 {api_ratio*100:.0f}% 消費", "😊 CX・品質"))

n_critical = sum(1 for a in alerts if a[0] == "critical")
hdr_status = "err" if n_critical else ("warn" if alerts else "ok")

style.page_header("🚨 要対応サマリー",
                  subtitle="今すぐ判断・対応が必要な項目だけを集約",
                  updated=data_loader.last_updated(),
                  status=hdr_status)

# ── 要対応カウント（数字を先頭に）──────────────────────────────────────────────
style.section_card_start("🚦 対応必要件数",
                         "要対応あり" if alerts else "クリア",
                         "err" if n_critical else ("warn" if alerts else "ok"))
c1, c2, c3, c4 = st.columns(4)
with c1:
    style.kpi_wrap_start("critical" if n_critical else "ok")
    st.metric("🔴 緊急", n_critical)
    style.kpi_wrap_end()
with c2:
    warn_n = len(alerts) - n_critical
    style.kpi_wrap_start("warn" if warn_n else "ok")
    st.metric("🟡 要確認", warn_n)
    style.kpi_wrap_end()
with c3:
    style.kpi_wrap_start("warn" if tv >= 5 else "ok")
    st.metric("👀 確認待ちタスク", tv)
    style.kpi_wrap_end()
with c4:
    style.kpi_wrap_start("critical" if fail_n else "ok")
    st.metric("❌ 失敗パイプライン", fail_n)
    style.kpi_wrap_end()
style.section_card_end()

# ── アラート一覧（最大表示・重要度順）──────────────────────────────────────────
style.section_card_start("📣 アラート",
                         f"{len(alerts)}件" if alerts else "なし",
                         "err" if n_critical else ("warn" if alerts else "ok"))
if not alerts:
    st.success("✅ 現在、緊急の対応が必要な項目はありません。")
else:
    crit = [a for a in alerts if a[0] == "critical"][:3]
    warns = [a for a in alerts if a[0] == "warn"][:3]
    for _, msg, dest in crit:
        st.error(f"{msg}　→ **{dest}** ページへ")
    for _, msg, dest in warns:
        st.warning(f"{msg}　→ **{dest}** ページへ")
    extra = len(alerts) - len(crit) - len(warns)
    if extra > 0:
        st.caption(f"…他 {extra} 件（各ページで詳細を確認）")
style.section_card_end()

# ── 確認待ちタスク（即対応リスト）──────────────────────────────────────────────
verify_top5 = (ks.get("verify_top5") or []) if ks else []
active_top5 = (ks.get("active_top5") or []) if ks else []
lcol, rcol = st.columns(2)
with lcol:
    style.section_card_start("👀 確認待ちタスク",
                             "要対応" if tv >= 5 else "",
                             "warn" if tv >= 5 else "info")
    if verify_top5:
        for t in verify_top5[:5]:
            st.write(f"• `{t.get('id','')}` {str(t.get('name',''))[:38]} — {t.get('assignee','')}")
        st.caption("→ 「🗂️ タスクボード」で承認・差し戻し")
    else:
        st.info("確認待ちのタスクはありません")
    style.section_card_end()
with rcol:
    style.section_card_start("🔵 進行中タスク")
    if active_top5:
        for t in active_top5[:5]:
            st.write(f"• `{t.get('id','')}` {str(t.get('name',''))[:38]} — {t.get('assignee','')}")
    else:
        st.info("進行中のタスクはありません")
    style.section_card_end()

# ── 収益・予算スナップショット（数字先頭）──────────────────────────────────────
monthly_actual = int(biz.get("monthly_actual", 0)) if biz else 0
monthly_target = int(biz.get("monthly_target", 20000)) if biz else 20000
prog = (monthly_actual / monthly_target) if monthly_target else 0
style.section_card_start("📊 収益・予算スナップショット")
m1, m2, m3 = st.columns(3)
with m1:
    style.kpi_wrap_start("ok" if prog >= 0.8 else "warn" if prog >= 0.3 else "critical")
    st.metric("💰 今月収益", f"¥{monthly_actual:,}",
              f"目標比 {round(prog*100)}%")
    style.kpi_wrap_end()
with m2:
    style.kpi_wrap_start("critical" if api_ratio > 0.8 else "warn" if api_ratio > 0.5 else "ok")
    st.metric("🪙 API消費", f"${used_api:.3f}", help=f"予算 ${lim_api}")
    style.kpi_wrap_end()
with m3:
    st.metric("🩺 ヘルス", "OK" if health_ok else "要確認")
st.caption("詳細は「💼 事業状況」「😊 CX・品質」ページで確認できます")
style.section_card_end()

# ── Bizdevスコア推移（意思決定の参考）──────────────────────────────────────────
entries = bt.get("entries", []) if bt else []
style.section_card_start("📈 Bizdevスコア推移")
if entries:
    import pandas as pd
    avg = round(sum(e.get("score", 0) for e in entries) / len(entries), 1)
    st.metric("平均スコア", f"{avg}/10", help=f"累計 {len(entries)} アイデア")
    df = pd.DataFrame(entries)
    if "date" in df.columns and "score" in df.columns:
        df_chart = df.groupby("date")["score"].mean().reset_index()
        df_chart.columns = ["日付", "平均スコア"]
        st.line_chart(df_chart.set_index("日付"))
    st.caption("→ 高スコア候補は「💡 BizDev」ページで確認")
else:
    st.info("Bizdevスコアデータがありません")
style.section_card_end()
