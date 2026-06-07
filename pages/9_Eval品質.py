import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, style

st.set_page_config(page_title="🧪 Eval品質", page_icon="🧪", layout="wide")
style.inject()

# ─── データ取得 ──────────────────────────────────────────────────────────────
def _safe(fn, default=None):
    try: return fn()
    except Exception: return default

eval_data        = _safe(lambda: data_loader.eval_status(), {})
failure_data     = _safe(lambda: data_loader.failure_patterns(), {})
updated          = _safe(lambda: data_loader.last_updated(), "")

by_agent    = eval_data.get("by_agent", [])    if eval_data else []
total_exp   = eval_data.get("total_experiments", 0) if eval_data else 0
avg_score   = eval_data.get("overall_avg_score")    if eval_data else None
error_rate  = eval_data.get("overall_error_rate_pct", 0) if eval_data else 0
impl_status = eval_data.get("impl_status", {})      if eval_data else {}
impl_done   = sum(1 for v in impl_status.values() if v)
impl_total  = max(len(impl_status), 7)

hdr_status = "err" if error_rate > 30 else ("warn" if error_rate > 10 else "ok")
style.page_header(
    "🧪 Eval品質",
    subtitle="評価システム全体マップ・スコア分析・実装ロードマップ",
    updated=updated,
    status=hdr_status,
)

# ─── KPI ─────────────────────────────────────────────────────────────────────
style.kpi_wrap_start("info")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("実験記録", f"{total_exp}件")
c2.metric("平均スコア", f"{avg_score:.1f} / 10" if avg_score else "—")
c3.metric("エラー率", f"{error_rate:.0f}%",
          delta=f"+{error_rate:.0f}%" if error_rate > 0 else None,
          delta_color="inverse")
c4.metric("実装済み機能", f"{impl_done} / {impl_total}項目")
c5.metric("評価エージェント数", f"{len(by_agent)}個")
style.kpi_wrap_end()

# ─── タブ ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🗺️ 全体フロー",
    "📊 スコア分析",
    "⚠️ エラーパターン",
    "🗓️ 実装ロードマップ",
])

# ══════════════════════════════════════════════════════════════════════════════
# 🗺️ 全体フロー — どのパイプラインでEvalが動いているか
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    style.section_card_start("📍 Eval接触点マップ（全パイプライン）", "", "info")
    st.markdown("""
> **凡例**: 🟢 実装済み &nbsp;|&nbsp; 🔲 計画中 &nbsp;|&nbsp; ⚪ Eval対象外
    """)

    PIPELINE_EVAL_MAP = [
        # (時刻, パイプライン名, Eval接触点, 状態)
        ("毎日 21:26", "⭐ DailyDriver",
         "step6: agent_runs.jsonl記録 / step6.5: run_stats集計", "🟢"),
        ("毎日 21:20", "MempalaceMaintenance",
         "phase3b: 低スコアエージェント検出 → agents_prompts.json自動改善", "🟢"),
        ("月・木 21:05", "StrategyChain (LangGraph+Prefect)",
         "run_agent_with_retry(): reviewer採点 → experiments.jsonl記録", "🟢"),
        ("火・金 21:05", "ContentChain (LangGraph+Prefect)",
         "run_agent_with_retry(): reviewer採点 → experiments.jsonl記録", "🟢"),
        ("毎日 21:27", "SelfAuditEngine",
         "自己監査スコア記録（独立評価）", "🟢"),
        ("毎日 21:26", "DailyDriver → eval_runner.py",
         "step9: 定義済みテストケースを毎日自動実行（回帰Eval）", "🔲"),
        ("日 21:23", "AutonomousLoop",
         "supervisor_agent: 出力品質チェック → Eval統合予定", "🔲"),
        ("水 23:03", "ProductMonitor",
         "Eval対象外（情報収集のみ）", "⚪"),
        ("月 22:33", "DailyOpensource",
         "Eval対象外（情報収集のみ）", "⚪"),
    ]

    cols_h = st.columns([2, 3, 4, 1])
    cols_h[0].markdown("**時刻 / 頻度**")
    cols_h[1].markdown("**パイプライン**")
    cols_h[2].markdown("**Eval接触点**")
    cols_h[3].markdown("**状態**")

    for t, name, eval_point, status in PIPELINE_EVAL_MAP:
        bg = ""
        if status == "🟢":
            bg = "background:#f0fff0;"
        elif status == "🔲":
            bg = "background:#fffbe6;"
        cols = st.columns([2, 3, 4, 1])
        cols[0].markdown(f'<span style="font-family:monospace;color:#666">{t}</span>',
                         unsafe_allow_html=True)
        cols[1].markdown(f"**{name}**")
        cols[2].markdown(f'<span style="color:#555;font-size:0.9em">{eval_point}</span>',
                         unsafe_allow_html=True)
        cols[3].markdown(status)
    style.section_card_end()

    style.section_card_start("🔄 Evalデータフロー（現状 → 目標）", "", "ok")
    st.markdown("""
```
【現状フロー】
パイプライン実行
  ├─ run_agent()          → agent_runs.jsonl   (latency / error / cost)
  └─ run_agent_with_retry() → experiments.jsonl (score / verdict / blind_spots)
                                    ↓
                           mempalace phase3b (毎日21:20)
                                    ↓
                           agents_prompts.json 自動改善
                                    ↓
                           次回実行から改善済みプロンプトで動作

【目標フロー（追加予定）】
eval_testcases/*.yaml  ← テストケース定義（入力・期待スコア・評価観点）
         ↓
eval_runner.py         ← DailyDriver step9 から毎日呼び出し
         ↓
experiments.jsonl      ← 既存フォーマットに追記（eval_mode=True で区別）
         ↓
回帰検出               ← 前回スコアより2点以上低下 → Kanban自動起票
```
    """)
    style.section_card_end()


# ══════════════════════════════════════════════════════════════════════════════
# 📊 スコア分析
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    if by_agent:
        style.section_card_start("📊 エージェント別スコア・Verdict分布", "", "info")
        cols_h = st.columns([2, 1, 1, 1, 3])
        cols_h[0].markdown("**エージェント**")
        cols_h[1].markdown("**平均スコア**")
        cols_h[2].markdown("**実験件数**")
        cols_h[3].markdown("**エラー率**")
        cols_h[4].markdown("**Verdict分布**")

        for a in sorted(by_agent, key=lambda x: -(x.get("avg_score") or 0)):
            agent_name  = a.get("agent", "?")
            avg_s       = a.get("avg_score")
            exp_count   = a.get("experiment_count", 0)
            err_rate    = a.get("error_rate_pct", 0)
            verdicts    = a.get("verdicts", {})

            score_icon = "🔴" if (avg_s and avg_s < 4) else ("🟡" if (avg_s and avg_s < 6) else "🟢")
            err_icon   = "🔴" if err_rate > 20 else ("🟡" if err_rate > 5 else "🟢")

            # Verdict 要約
            v_parts = []
            for k, cnt in sorted(verdicts.items(), key=lambda x: -x[1])[:3]:
                v_parts.append(f"{k[:6]}:{cnt}")
            verdict_str = " / ".join(v_parts) if v_parts else "—"

            cols = st.columns([2, 1, 1, 1, 3])
            cols[0].code(agent_name)
            cols[1].write(f"{score_icon} {avg_s:.1f}" if avg_s else "—")
            cols[2].write(str(exp_count))
            cols[3].write(f"{err_icon} {err_rate:.0f}%")
            cols[4].write(verdict_str)
        style.section_card_end()

        # 要改善エージェントをハイライト
        problem_agents = [a for a in by_agent
                          if (a.get("avg_score") or 10) < 5 or a.get("error_rate_pct", 0) > 20]
        if problem_agents:
            style.section_card_start(
                f"🔴 要改善エージェント（スコア<5 or エラー率>20%）",
                f"{len(problem_agents)}件", "warn")
            for a in problem_agents:
                avg_s    = a.get("avg_score")
                err_rate = a.get("error_rate_pct", 0)
                reasons  = []
                if avg_s and avg_s < 5:
                    reasons.append(f"スコア低: {avg_s:.1f}/10")
                if err_rate > 20:
                    reasons.append(f"エラー率高: {err_rate:.0f}%")
                st.markdown(f"- `{a['agent']}` — {' / '.join(reasons)}")
            style.section_card_end()
    else:
        st.info("Firebase にデータがまだありません。`firebase_dashboard_pusher.py` を実行してください。")

    # Verdict 定義説明
    style.section_card_start("📋 Verdict 判定基準", "", "info")
    st.markdown("""
| Verdict | スコア目安 | 意味 |
|---------|-----------|------|
| **推奨** | 7.0〜10 | そのまま本番投入可 |
| **条件付き** | 5.5〜6.9 | 軽微な修正で投入可 |
| **保留** | 4.0〜5.4 | 改善してから再評価 |
| **却下** | 0〜3.9 | 根本的な見直しが必要 |

> スコアは `reviewer` エージェントが 1〜10 点で評価。`experiments.jsonl` に記録。
    """)
    style.section_card_end()


# ══════════════════════════════════════════════════════════════════════════════
# ⚠️ エラーパターン
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    fp_patterns = failure_data.get("patterns", {}) if failure_data else {}
    total_runs_db = eval_data.get("total_runs", 0) if eval_data else 0

    # 失敗パターン分類結果（failure_patterns.json から）
    if fp_patterns:
        style.section_card_start("🔍 失敗パターン分類（mempalace phase3b が自動解析）", "", "warn")
        cols_h = st.columns([2, 2, 1, 3])
        cols_h[0].markdown("**エージェント**")
        cols_h[1].markdown("**エラー種別**")
        cols_h[2].markdown("**件数**")
        cols_h[3].markdown("**自動対処内容**")
        AUTO_FIX = {
            "json_parse_failed": "プロンプトに「JSONのみ出力」制約を自動注入",
            "claude_cli_error":  "プロンプト短縮・トークン削減を改善に反映",
            "timeout":           "出力簡潔化指示を改善に反映",
        }
        for agent_name, err_counts in sorted(fp_patterns.items()):
            if not isinstance(err_counts, dict):
                continue
            for err_type, count in sorted(err_counts.items(), key=lambda x: -x[1]):
                cols = st.columns([2, 2, 1, 3])
                cols[0].code(agent_name)
                cols[1].write(f"`{err_type}`")
                cols[2].write(f"{'🔴' if count >= 3 else '🟡'} {count}")
                cols[3].write(AUTO_FIX.get(err_type, "次回phase3bで分析・改善"))
        style.section_card_end()

    elif by_agent:
        style.section_card_start("⚠️ エラー率サマリー（agent_runs.jsonl）", "", "warn")
        error_agents = [a for a in by_agent if a.get("error_rate_pct", 0) > 0]
        if error_agents:
            cols_h = st.columns([2, 1, 3])
            cols_h[0].markdown("**エージェント**")
            cols_h[1].markdown("**エラー率**")
            cols_h[2].markdown("**状態**")
            for a in sorted(error_agents, key=lambda x: -x.get("error_rate_pct", 0)):
                cols = st.columns([2, 1, 3])
                cols[0].code(a["agent"])
                rate = a.get("error_rate_pct", 0)
                cols[1].write(f"{'🔴' if rate > 20 else '🟡'} {rate:.0f}%")
                cols[2].write("phase3b次回実行時に自動分類・改善")
        style.section_card_end()
    else:
        st.info("Firebase にデータがまだありません。`firebase_dashboard_pusher.py` を実行してください。")

    style.section_card_start("🔍 既知エラーパターンと対処法", "", "info")
    st.markdown("""
| エラー種別 | 発生エージェント | 原因 | 対処法 |
|-----------|----------------|------|--------|
| `json_parse_failed` | bizdev / reviewer | Haiku が JSON 以外のテキストを出力 | プロンプトに `出力はJSONのみ` 制約を追加 |
| `claude_cli_error` | cx_expert | claude -p プロセス異常終了 | `safe_run()` の timeout 延長・リトライ追加 |
| タイムアウト | 全般 | 処理時間超過 | Haiku 優先 / 入力トークン削減 |
| コンテキスト超過 | LangGraph系 | プロンプト肥大化 | `--max-tokens` / 入力切り詰め |

> **自動対処**: `mempalace_maintenance.py phase3b` が毎日 21:20 にエラー率>20%を検知し、
> 改善プロンプトを自動生成して `agents_prompts.json` を更新。
    """)
    style.section_card_end()


# ══════════════════════════════════════════════════════════════════════════════
# 🗓️ 実装ロードマップ
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    style.section_card_start("✅ 実装済み機能（Eval基盤）", "", "ok")
    DONE_ITEMS = [
        ("agent_runs.jsonl", "本番ログ記録（latency/error/cost/trace_id）",
         "agent_framework.py → run_agent()"),
        ("experiments.jsonl", "評価ログ記録（score/verdict/blind_spots）",
         "agent_framework.py → run_agent_with_retry()"),
        ("agents_prompts.json + Git", "プロンプトバージョン管理（履歴付き）",
         "mempalace_maintenance.py → GitHub管理"),
        ("mempalace phase3b", "日次自動改善（run_stats→低スコア検知→prompt更新）",
         "毎日 21:20 自動実行"),
        ("agent_run_stats Firebase", "エラー率・レイテンシのダッシュボード可視化",
         "3_稼働状況.py エージェント実績タブ"),
    ]
    for name, desc, where in DONE_ITEMS:
        st.markdown(
            f'✅ **{name}**'
            f'<br><span style="color:#555;font-size:0.9em;margin-left:1.5em">'
            f'{desc}<br>'
            f'<span style="color:#888">実装場所: {where}</span>'
            f'</span>',
            unsafe_allow_html=True,
        )
        st.markdown("")
    style.section_card_end()

    style.section_card_start("🔲 未実装（次のステップ）", "優先順", "warn")
    PLANNED_ITEMS = [
        ("1", "eval_testcases/*.yaml",
         "エージェントごとのテストケース定義（入力・期待スコア・評価観点）",
         "30分", "eval_testcases/ フォルダ新規作成"),
        ("2", "eval_runner.py",
         "YAMLテストケースを実行 → experiments.jsonlに記録（回帰Eval）",
         "30分", "DailyDriver step9 から呼び出し"),
        ("3", "回帰検出（DailyDriver連携）",
         "前回比スコア低下 > 2点 → Kanban自動起票",
         "10分", "eval_runner.py 追記のみ"),
        ("4", "失敗パターン自動分類",
         "agent_runs.jsonl のエラー種別を自動タグ付け → failure_patterns.md 更新",
         "20分", "mempalace phase3b 拡張"),
        ("5", "プロンプトA/Bテスト",
         "2バージョンのプロンプトを同一入力で比較評価",
         "後日", "eval_runner.py 拡張"),
    ]
    cols_h = st.columns([0.5, 2, 4, 1, 2])
    cols_h[0].markdown("**#**")
    cols_h[1].markdown("**機能**")
    cols_h[2].markdown("**内容**")
    cols_h[3].markdown("**工数**")
    cols_h[4].markdown("**統合先**")
    for no, name, desc, effort, where in PLANNED_ITEMS:
        cols = st.columns([0.5, 2, 4, 1, 2])
        cols[0].write(no)
        cols[1].code(name)
        cols[2].write(desc)
        cols[3].write(effort)
        cols[4].write(where)
    style.section_card_end()

    style.section_card_start("💡 OSS vs 自前の設計判断", "", "info")
    st.markdown("""
| 選択肢 | メリット | デメリット | 判断 |
|--------|---------|-----------|------|
| **promptfoo** | 業界標準・CI統合容易 | Node.js依存・外部HTTP・CrowdStrikeリスク | ❌ 不採用 |
| **deepeval** | Python製・豊富なメトリクス | API呼び出し前提・外部依存 | ❌ 不採用 |
| **自前 eval_runner.py** | 既存インフラ完全統合・claude -p のみ・外部HTTP不要 | 機能は最小限 | ✅ 採用 |

> **採用理由**: `claude -p` 縛り・CrowdStrikeリスク・外部HTTP最小化の制約下では、
> `experiments.jsonl + agent_framework.py` の既存仕組みに乗せた自前実装が最適。
> promptfoo の「YAML定義・スコア集計・回帰検出」という**設計思想**のみ輸入する。
    """)
    style.section_card_end()
