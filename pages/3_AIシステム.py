import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, date, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, style
from utils.data_loader import get_push_log
from utils.style import freshness_banner

# ─── 静的定数（旧 0_システム概要.py） ────────────────────────────────────────

DAILY_PIPELINES = [
    ("18:30", "DailyCheckinMailer",   "チェックインメール送信"),
    ("21:00", "DailyCheckinFetch",    "接続チェック・日次初期化"),
    ("21:20", "MempalaceMaintenance", "メモリ保守・agent_levelup・知識補完"),
    ("21:21", "GDriveBackup",         "Googleドライブバックアップ"),
    ("21:23", "⭐ PrefectDailyFlow",  "DailyDriver含む日次パイプライン群（Prefect統合）"),
    ("21:30", "FetchClaudeUsageAuto", "Claude使用量取得・Kanban起票"),
]

CHAIN_PIPELINES = [
    ("月・木 21:05", "PrefectStrategyFlow",    "戦略分析 → BizDev → PDCAレポート（LangGraph+Prefect）"),
    ("火・金 21:05", "PrefectContentFlow",     "コンテンツ生成 → note記事投稿（LangGraph+Prefect）"),
    ("水・土 21:06", "PrefectMaintenanceFlow", "システム改善・監査ループ（LangGraph+Prefect）"),
]

WEEKLY_PIPELINES = [
    ("日 22:57", "NameConsistencyCheck", "ファイル名一貫性チェック"),
    ("日 21:27", "DocSync",             "ドキュメント同期"),
]

DAILY_DRIVER_STEPS = [
    ("1",   "市場調査",       "product_researcher.py / freelance_researcher.py → crawl4ai取得"),
    ("2",   "アイデア生成",   "daily_bizdev.py → wiki参照型ビジネス施策生成"),
    ("3",   "施策抽出",       "Haiku → 優先3施策を選定"),
    ("4",   "施策実行",       "コンテンツ案/製品改善/調査の各アクション自動実行"),
    ("5",   "wiki参照",       "_load_wiki_context() → audience-pains/retention-tricks注入"),
    ("6",   "実績記録",       "agent_runs.jsonl → 全エージェント実行をJSONL記録"),
    ("6.5", "統計サマリー",   "get_run_stats(24h) → エラー率・レイテンシ自動集計"),
    ("7",   "Kanban更新",     "kanban_tasks.json → 完了タスク反映"),
    ("8",   "放置成果物改善", "stale_outputs(>7日) → ContentChainへ自動投入"),
]

AGENTS = [
    ("freelance_researcher", "フリーランス案件リサーチ（AI自動化率95%+）", "DailyDriver step1"),
    ("product_researcher",   "競合製品調査（crawl4ai実サイト取得）",        "DailyDriver step1"),
    ("content_strategist",   "コンテンツマーケ戦略（note/Qiita/X）",       "ContentChain"),
    ("cx_expert",            "CX評価・改善提案（NPS・ジョブ理論）",         "CXチェーン"),
    ("supervisor_agent",     "出力品質チェック・リスク評価",                "AutonomousLoop"),
    ("qa_observer",          "テスト観点抽出・リスク分析",                  "StrategyChain"),
    ("handover_agent",       "引継ぎドキュメント生成",                      "汎用"),
    ("defect_predictor",     "不具合予測・変更影響分析",                     "汎用"),
    ("experiment",           "A/Bテスト・スコア改善（実験ログ→levelup）",   "MempalaceMaintenance"),
]

FOLDERS = [
    ("🟢", "agents/",                   "メインスクリプト群（100+ファイル）",       "chains/agent_framework/tools等"),
    ("🟢", "agents/data/",              "キャッシュ・データファイル（JSON/JSONL）", "単一ライター原則遵守"),
    ("🟢", "agents/logs/",              "実行ログ（JSONL・テキスト・biz_pdca）",   "日次ローテーション"),
    ("🟢", "agents/platforms/",         "外部PF連携（Gumroad/KDP/Etsy/Payhip）", "pending多数"),
    ("🟢", "streamlit_dashboard/",      "Streamlitダッシュボード（3ページ）",       "push→自動デプロイ"),
    ("🟢", "skills/",                   "Claude Codeスキル定義",                  "セッション内で起動"),
    ("🔴", "agents/_archive_20260602/", "2026-06-02以前のアーカイブ",             "削除候補"),
]

DATA_FILES = [
    ("kanban_tasks.json",    "KanbanタスクDB（KT-XXX管理・単一情報源）",    "Firestoreプライマリ"),
    ("business_status.json", "収益・事業状況（BizDevタブの基盤）",          "daily_driver.py"),
    ("agents_prompts.json",  "エージェントプロンプト定義（9エージェント）",  "mempalace_maintenance.py"),
    ("agent_runs.jsonl",     "エージェント実行ログ（24h/7d統計ベース）",    "agent_framework.py"),
    ("datasource.json",      "リアルタイム実行状態・IDEステータスバー",      "daily_driver.py"),
    ("experiments.jsonl",    "A/B実験ログ（500件→levelup優先度計算）",      "agent_framework.py"),
]

# ─── ページ設定 ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="AI・システム", page_icon="🤖", layout="wide")
style.inject()

_push_log = get_push_log()
st.markdown(
    f'<div style="text-align:right;margin-bottom:4px;">{freshness_banner(_push_log)}</div>',
    unsafe_allow_html=True
)

st.title("🤖 AI・システム")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 システム概要",
    "⚙️ 稼働状況",
    "🏢 経営体制",
    "🧠 AI管理",
    "💰 コスト管理",
    "🔄 フロー実行",
])

# ══════════════════════════════════════════════════════════════════════════════
# 📊 システム概要（旧 0_システム概要.py）
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    def _safe(fn, default=None):
        try:
            return fn()
        except Exception:
            return default

    pl_status   = _safe(lambda: data_loader.pipeline_status(), {})
    agent_stats = _safe(lambda: data_loader.agent_run_stats(), {})
    cost_report = _safe(lambda: data_loader.pipeline_cost_report(), {})
    updated     = _safe(lambda: data_loader.last_updated(), "")

    counts = pl_status.get("counts", {}) if pl_status else {}

    # ── 🎯 AIレベルスコア（最上部・最優先表示）──────────────────────────────────
    _roi = _safe(lambda: data_loader.roi_score(), {})
    _rel = _safe(lambda: data_loader.reliability_kpi(), {})
    _aut = _safe(lambda: data_loader.autonomy_kpi(), {})
    _eff = _safe(lambda: data_loader.efficiency_kpi(), {})
    _lrn = _safe(lambda: data_loader.learning_kpi(), {})
    _gh  = _safe(lambda: data_loader.anthropic_github_kpi(), {})
    _arch = _safe(lambda: data_loader.architecture_kpi() if hasattr(data_loader, 'architecture_kpi') else {}, {})

    if _roi:
        _comps = _roi.get("component_scores", {})
        _grade = _roi.get("grade", "?")
        _level = _roi.get("ai_level_score", 0)
        _grade_color = {"A": "ok", "B": "ok", "C": "warn", "D": "critical", "F": "critical"}.get(_grade, "info")
        _grade_emoji = {"A": "🟢", "B": "🟢", "C": "🟡", "D": "🔴", "F": "🔴"}.get(_grade, "⚪")

        style.kpi_wrap_start(_grade_color)
        _roi_dict = _roi.get("roi") or {}
        _roi_val  = _roi_dict.get("value", "N/A") if isinstance(_roi_dict, dict) else "N/A"
        st.markdown(
            f'<div style="display:flex;align-items:baseline;gap:16px;flex-wrap:wrap;margin-bottom:12px">'
            f'<span style="font-size:2.2rem;font-weight:800;line-height:1">{_grade_emoji} {_level}</span>'
            f'<span style="font-size:1.1rem;opacity:0.55;font-weight:400">/100</span>'
            f'<span style="font-size:1.3rem;font-weight:700;letter-spacing:0.02em">[{_grade}]</span>'
            f'<span style="font-size:0.9rem;color:#9aa4b2">AIレベルスコア</span>'
            f'<span style="font-size:0.85rem;color:#9aa4b2;margin-left:8px">ROI: <code style="font-size:0.85rem">{_roi_val}</code></span>'
            f'</div>',
            unsafe_allow_html=True
        )
        # ── 行1: 重み大のKPI（4列）──────────────────────────────────────────────
        _kc1, _kc2, _kc3, _kc4 = st.columns(4)
        _rel_score = _comps.get("reliability", 0)
        _aut_score = _comps.get("autonomy", 0)
        _mod_score = _comps.get("modernity", 0)
        _gh_score  = _comps.get("anthropic_github", 0)
        _mod_data  = _roi.get("modernity_detail", {})
        _gh_repos  = _gh.get("repos", [])
        _gh_top    = _gh.get("top_opportunity", "")
        _gh_active = sum(1 for r in _gh_repos if r.get("status") == "active")

        _kc1.metric("🔴 信頼性 ×20%", f"{_rel_score:.0f}/100",
                    delta=f"成功率 {_rel.get('overall',{}).get('success_rate_pct',0)}%",
                    delta_color="normal" if _rel_score >= 60 else "inverse",
                    help="エージェントスコア×30% + パイプライン成功率×20% + 出力品質×35% + PC安定性×15%")
        _kc2.metric("🟠 自律性 ×25%", f"{_aut_score:.0f}/100",
                    delta=f"解決{_aut.get('components',{}).get('problem_resolution_pct',0)}% 価値{_aut.get('components',{}).get('value_creation_pct',0)}%",
                    help="問題解決性×40% + 価値創出性×40% + 自律実行率×20%。価値創出=AI収益×40%+業務支援×35%+文脈把握×25%")
        _kc3.metric("🟣 モダン度 ×20%", f"{_mod_score:.0f}/100",
                    delta=f"{_mod_data.get('implemented',0)}✅ {_mod_data.get('partial',0)}⚠️ {_mod_data.get('missing',0)}❌",
                    delta_color="normal" if _mod_score >= 60 else "inverse",
                    help="モダンAIシステム18項目（知性・知識・行動・設計・品質・運用）の充足度。✅=2点/⚠️=1点/❌=0点")
        _kc4.metric("🔵 GitHub活用 ×10%", f"{_gh_score:.0f}/100",
                    delta=f"活用中 {_gh_active}/{len(_gh_repos)} リポジトリ",
                    delta_color="normal" if _gh_score >= 50 else "inverse",
                    help=f"Anthropic公式7リポジトリの活用充足度。次の一手: {_gh_top}")

        # ── 行2: 残りKPI（3列）─────────────────────────────────────────────────
        st.write("")
        _kc5, _kc6, _kc7 = st.columns(3)
        _mu_score  = _comps.get("model_usage", 0)
        _lrn_score = _comps.get("learning", 0)
        _obs_score = _comps.get("observability", 0)
        _enrich = _lrn.get('enrichment_score', 0)
        _ut_d   = _lrn.get('utilization', {})
        _ut_s   = _lrn.get('utilization_score', 0)
        _ut_n   = _ut_d.get('total_sessions', 0)
        _und_s  = _lrn.get('understanding_score', 0)
        _und_d  = _lrn.get('user_understanding', {})
        _mem_d  = _und_d.get('memory', {})
        if _ut_n >= 5:
            _ut_label = f"充実{_enrich:.0f} 活用{_ut_s:.0f} 理解{_und_s:.0f}"
        else:
            _ut_label = f"充実{_enrich:.0f} 理解{_und_s:.0f}"
        _kc5.metric("🟡 学習率 ×10%", f"{_lrn_score:.0f}/100",
                    delta=_ut_label,
                    help=f"充実×34%+活用×33%+理解度×33%。理解度=MEMORY.md({_mem_d.get('feedback_files',0)}FB/{_mem_d.get('project_files',0)}PJ)+Obsidian/Preferences")
        _kc6.metric("🟢 観測性 ×10%", f"{_obs_score:.0f}/100",
                    delta="UI品質・精度", delta_color="normal" if _obs_score >= 70 else "inverse",
                    help="ダッシュボードの情報集約度・UI深さ・データ鮮度を評価。問題が少ないほど高スコア")
        _kc7.metric("⚪ モデル活用 ×5%", f"{_mu_score:.0f}/100",
                    delta="CC/Haiku/Sonnet",
                    help="CCセッション適切性×50% + パイプラインHaiku適正×30% + Sonnet昇格パターン×20%")

        # ── 行3: アーキテクチャ再評価（マクロ視点） ────────────────────────────
        st.write("")
        _arch_score = _arch.get("score", 0)
        _arch_staleness = _arch.get("review_staleness", {})
        _arch_issues = _arch.get("structural_issues", {})
        _arch_open = _arch_issues.get("open_count", 0)
        _arch_penalty = _arch_issues.get("penalty_pt", 0)
        _arch_days = _arch_staleness.get("days_since", 0)
        _arch_color = "normal" if _arch_score >= 60 else "inverse"
        _arch_col1, _arch_col2, _arch_col3 = st.columns([2, 1, 1])
        _arch_col1.metric(
            "🏗️ アーキテクチャ再評価 ×10%",
            f"{_arch_score:.0f}/100",
            delta=f"構造問題 {_arch_open}件 open / ペナルティ -{_arch_penalty}pt",
            delta_color=_arch_color,
            help="マクロ視点でシステム構成をゼロベースで問い直す習慣の定着度。鮮度（週次-5pt）＋構造問題ペナルティ（HIGH:-15pt / MED:-7pt）"
        )
        _arch_col2.metric(
            "最終レビュー",
            f"{_arch_staleness.get('last_review_date', '未実施')}",
            delta=f"{_arch_days}日前",
            delta_color="normal" if _arch_days < 14 else "inverse"
        )
        _arch_col3.metric(
            "鮮度ペナルティ",
            f"-{_arch_staleness.get('penalty_pt', 0)}pt",
            delta="14日以内なら0pt",
            delta_color="normal" if _arch_staleness.get('penalty_pt', 0) == 0 else "inverse"
        )
        if _arch_issues.get("issues"):
            with st.expander(f"🔍 未解決構造問題 ({_arch_open}件)"):
                for _issue in _arch_issues["issues"]:
                    _sev = _issue.get("severity", "")
                    _sev_icon = "🔴" if _sev == "high" else "🟡"
                    _desc = _issue.get("description") or _issue.get("id", "")
                    st.markdown(f"{_sev_icon} **{_issue.get('id','')}** — {_desc}")
                st.caption(f"マクロ視点での構造問題が残る限り、信頼性・自律性・モデル活用にも -{min(_arch_issues.get('open_count',0)*2,6)}ptのペナルティが適用されます")

        with st.expander("📖 各スコアの定義"):
            st.markdown("""
| スコア | 重み | 計算式 | 高い = |
|--------|------|--------|--------|
| 🔴 **信頼性** | ×20% | エージェントスコア×30% + パイプライン成功率×20% + 出力品質×35% + PC安定性×15% | 安定動作・出力品質・PC負荷が良好 |
| 🟠 **自律性** | ×25% | 問題解決性×40% + 価値創出性×40% + 自律実行率×20% | 問題を放置せず・収益/業務目標に貢献し・会長の業務を深く把握している |
| 🟣 **モダン度** | ×20% | モダンAIシステム18項目（✅=2/⚠️=1/❌=0）÷36×100 | AI設計・品質・運用が最新ベストプラクティスを充足 |
| 🔵 **GitHub活用** | ×10% | Anthropic公式7リポジトリ（skills/SDK/Cookbooks等）の活用充足度 | フル活用でAIシステムが高度化 |
| 🟡 **学習率** | ×10% | 知識充実×34% + 知識活用×33% + ユーザー理解度×33% | 知識が蓄積・活用され、ユーザーへの理解が深まっている |
| 🟢 **観測性** | ×10% | ダッシュボードの情報集約度・UI深さ・データ鮮度 | 必要な情報が一目でわかる状態 |
| ⚪ **モデル活用** | ×5% | CCセッション適切性×50% + Haiku適正×30% + Sonnet昇格×20% | Sonnet/OpusをCCで活用・Haikuをパイプラインで適切に使う |
| 🏗️ **アーキテクチャ再評価** | ×10% | 100pt − 鮮度ペナルティ(週次-5pt) − 構造問題(HIGH-15/MED-7) | ゼロベースのマクロ設計レビューが定期実施・構造問題が閉じている |

**グレード基準**: A≥80 / B≥65 / C≥50 / D≥35 / F<35
""")

        with st.expander("🔍 計算根拠（全内訳）"):
            _c_rel, _c_aut = st.columns(2)

            with _c_rel:
                st.markdown("#### 🔴 信頼性スコア")
                _ag = _rel.get("agent_reliability", {})
                _ag_score = _ag.get("agent_score", 0)
                _pl = _rel.get("pipeline_reliability", {})
                _pl_rate = _pl.get("pipeline_success_rate_pct") or 0
                _oq = _rel.get("output_quality", {})
                _oq_score = _oq.get("score_100", 0)
                _pc = _rel.get("pc_stability", {})
                _pc_score = _pc.get("pc_stability_score", 50)
                st.markdown(f"""
| 軸 | 重み | 値 | 寄与 |
|----|------|-----|------|
| エージェントスコア | ×30% | {_ag_score:.1f} | {_ag_score*0.30:.1f}pt |
| パイプライン成功率 | ×20% | {_pl_rate:.1f} | {_pl_rate*0.20:.1f}pt |
| 出力品質 | ×35% | {_oq_score:.1f} | {_oq_score*0.35:.1f}pt |
| PC安定性 | ×15% | {_pc_score:.1f} | {_pc_score*0.15:.1f}pt |
| **合計** | | | **{_rel_score:.1f}/100** |
""")
                if _pl.get("pipelines"):
                    _failed = [p for p in _pl["pipelines"] if p.get("status") == "failed"]
                    if _failed:
                        st.markdown(f"⚠️ 失敗パイプライン: {', '.join(p['name'] for p in _failed)}")

            with _c_aut:
                st.markdown("#### 🟢 自律性スコア")
                _ac = _aut.get("components", {})
                _pr = _aut.get("problem_resolution", {})
                _vc = _aut.get("value_creation", {})
                _cl = _aut.get("closed_tasks", {})
                _closure_pct = _ac.get("task_closure_rate_pct", 0)
                _res_pct     = _ac.get("problem_resolution_pct", 0)
                _val_pct     = _ac.get("value_creation_pct", 0)
                st.markdown(f"""
| 軸 | 重み | 値 | 寄与 |
|----|------|-----|------|
| 問題解決性 | ×50% | {_res_pct:.1f}% | {_res_pct*0.50:.1f}pt |
| 価値創出性 | ×50% | {_val_pct:.1f}% | {_val_pct*0.50:.1f}pt |
| **合計** | | | **{_aut_score:.1f}/100** |
| [参考] タスク自律率 | - | {_closure_pct:.1f}% | スコア算出外 |
""")
                _pen = _pr.get("total_penalty", 0)
                if _pen > 0:
                    _bt  = _pr.get("blocked_tasks", {})
                    _st  = _pr.get("stale_tasks", {})
                    _da  = _pr.get("dashboard_alerts", {})
                    _la  = _pr.get("low_ai_score", {})
                    st.markdown(f"**問題解決性ペナルティ合計: {_pen}pt**")
                    st.markdown(f"""
- ブロックタスク {_bt.get('count',0)}件: -{_bt.get('penalty',0)}pt
- 放置タスク(7日+) {_st.get('count',0)}件: -{_st.get('penalty',0)}pt
- ダッシュボードアラート {_da.get('count',0)}件: -{_da.get('penalty',0)}pt
- 低AIスコア放置: -{_la.get('penalty',0)}pt
""")
                _rev = _vc.get("revenue_contribution", {})
                _ws  = _vc.get("work_support", {})
                _cd  = _vc.get("context_depth", {})
                _cd_mem = _cd.get("memory_files", {})
                _cd_now = _cd.get("now_freshness", {})
                _cd_ord = _cd.get("standing_orders", {})
                st.markdown(f"""**価値創出性内訳（会長目標への貢献度）:**

| 軸 | 重み | 値 | スコア |
|----|------|-----|--------|
| 💴 AI収益貢献 | ×40% | ¥{_rev.get('monthly_actual',0):,} / ¥{_rev.get('monthly_target',0):,} | {_rev.get('rate_pct',0):.0f}% |
| 💼 業務支援達成 | ×35% | {_ws.get('closed_count',0)}/{_ws.get('target',15)}件 | {_ws.get('rate_pct',0):.0f}% |
| 🧠 業務文脈把握 | ×25% | memory{_cd_mem.get('count',0)}件/now.md{_cd_now.get('age_days',99)}日前/orders{_cd_ord.get('active_count',0)}件 | {_cd.get('context_depth_pct',0):.0f}% |

*AI収益ゼロ時は bizdev 系タスク進捗で最大30%*
""")

            st.divider()
            _c_eff, _c_obs = st.columns(2)
            with _c_eff:
                st.markdown("#### 🤖 モデル活用・学習率・ROI")
                _mu_data = _safe(lambda: data_loader.model_usage_kpi() if hasattr(data_loader, 'model_usage_kpi') else {}, {})
                _mu_comps = _mu_data.get("components", {})
                _mu_detail = _mu_data.get("details", {})
                st.markdown(f"**モデル活用: {_mu_score:.1f}/100**")
                st.markdown(f"""
| 軸 | 重み | スコア |
|----|------|--------|
| CCセッション適切性 | ×50% | {_mu_comps.get('cc_appropriateness', 0):.0f}/100 |
| パイプラインHaiku適正 | ×30% | {_mu_comps.get('haiku_fitness', 0):.0f}/100 |
| Sonnet昇格パターン | ×20% | {_mu_comps.get('sonnet_escalation', 0):.0f}/100 |
""")
                _cc_d = _mu_detail.get("cc", {})
                st.caption(f"CC: Sonnet {_cc_d.get('sonnet_ratio_pct','-')}% / Opus {_cc_d.get('opus_ratio_pct','-')}% / Haiku {_cc_d.get('haiku_ratio_pct','-')}%")
                st.divider()
                _mp2      = _lrn.get('mempalace', {})
                _ob2      = _lrn.get('obsidian', {})
                _imp2     = _lrn.get('ai_improvement', {})
                _enrich2  = _lrn.get('enrichment_score', 0)
                _utilize2 = _lrn.get('utilization_score', 0)
                _ut_d2    = _lrn.get('utilization', {})
                _delta2   = _imp2.get('delta', 0)
                _dir2     = "▲" if _delta2 > 0 else ("▼" if _delta2 < 0 else "→")
                st.markdown(f"**学習率: {_lrn_score:.1f}/100**")
                st.markdown(f"""
| 軸 | 重み | スコア | 内訳 |
|----|------|--------|------|
| 知識充実 | ×50% | {_enrich2:.0f}/100 | Mempalace(量+構造) + Obsidian(量+構造) の平均 |
| 知識活用 | ×50% | {_utilize2:.0f}/100 | 直近7日 {_ut_d2.get('utilized_sessions',0)}/{_ut_d2.get('total_sessions',0)}セッションでMempalace参照 |
| **合計** | | **{_lrn_score:.1f}/100** | ※5セッション未満は充実スコアのみ |
""")
                st.markdown(f"""**📚 知識充実スコア内訳: {_enrich2:.0f}/100**

| 知識系統 | 説明 | 量スコア | 構造スコア |
|---------|------|---------|-----------|
| **Mempalace** | AIの知識パレス（長期記憶DB）。ドロワー＝記憶1件、KGエッジ＝知識同士のつながり | {_mp2.get('volume_score',0):.0f}/100（{_mp2.get('drawers',0):,}件 / 目標10,000） | {_mp2.get('structure_score',0):.0f}/100（{_mp2.get('edges',0)}KGエッジ / 目標200） |
| **Obsidian** | ノートVault。知識の蓄積と`[[リンク]]`で構造化 | {_ob2.get('volume_score',0):.0f}/100（{_ob2.get('files',0)}件 / 目標200） | {_ob2.get('structure_score',0):.0f}/100（平均{_ob2.get('avg_links_per_file',0):.1f}リンク/件 / 目標5.0） |

> 📊 **知識活用スコア**: PostToolUseフックでMempalace MCPコール数を自動集計。5セッション蓄積後に学習スコアへ組み込み開始。
""")
                st.divider()
                _roi_bk = _roi.get("roi")
                _sc = _roi.get("score_change", {})
                _cp = _roi.get("cost_period", {})
                if _sc:
                    _delta = _sc.get("delta", 0)
                    _dir   = "▲" if _delta > 0 else ("▼" if _delta < 0 else "→")
                    _color = "green" if _delta > 0 else ("red" if _delta < 0 else "gray")
                    st.markdown(f"**週次スコア変化: :{_color}[{_dir}{abs(_delta):.1f}pt]** &nbsp; ({_sc.get('oldest_score','?')} → {_sc.get('latest_score','?')} &nbsp; {_sc.get('oldest_date','?')}〜{_sc.get('latest_date','?')})")
                st.divider()
                if _roi_bk and isinstance(_roi_bk, dict):
                    _span = _roi_bk.get('window_span_str', '?')
                    st.markdown(f"**ROI: {_roi_bk.get('value','N/A')}** &nbsp; `直近1億トークン({_span})`")
                    st.markdown(f"計算式: {_roi_bk.get('formula','')}")
                    _w_date  = _roi_bk.get('window_cutoff_date', '?')
                    _w_days  = _roi_bk.get('window_days', 0)
                    _w_tok   = _roi_bk.get('window_tokens', 0)
                    _reached = _roi_bk.get('reached_1b_tokens', False)
                    _s_start = _roi_bk.get('score_at_window_start', 0)
                    _s_now   = _roi_bk.get('score_now', 0)
                    _delta   = _roi_bk.get('numerator_delta_score', 0)
                    _rp      = _roi_bk.get('retry_penalty_multiplier', 1)
                    st.markdown(f"- 期間: {_w_date} 〜 今日 (**{_w_days}日間** / {_w_tok:,}tokens {'✓1億達成' if _reached else '※1億未達'})")
                    st.markdown(f"- 分子: {_s_start}pt → {_s_now}pt = **{_delta:+.1f}pt**")
                    st.markdown(f"- 分母: 1 × {_rp} = **{_rp:.3f}**")
                    _cc_track = _roi_bk.get("cc_tracking", "pending")
                    st.caption(f"{'✅' if _cc_track == 'active' else '⚠️'} CCトークン追跡: {_cc_track}")
            with _c_obs:
                st.markdown("#### 👁️ 観測性スコア（9軸）")
                st.markdown(f"スコア: **{_obs_score:.1f}/100**")
                _obs_det = _roi.get("observability_detail", {})
                _obs_dims = _obs_det.get("dimensions", {})
                _obs_w    = _obs_det.get("weights", {})
                _dim_label = {
                    "freshness":     ("🕐", "鮮度",     "Few"),
                    "sufficiency":   ("📦", "完全性",   "Few"),
                    "context":       ("📊", "文脈性",   "Few"),
                    "actionability": ("🎯", "アクション性", "Few"),
                    "clarity":       ("🔍", "明瞭性",   "Few"),
                    "accuracy":      ("✔️",  "正確性",   "Few"),
                    "metrics":       ("📈", "メトリクス", "SRE"),
                    "logs":          ("📋", "ログ",     "SRE"),
                    "traces":        ("🔗", "トレース", "SRE"),
                }
                if _obs_dims:
                    _rows_obs = []
                    for _dk, (_icon, _dname, _grp) in _dim_label.items():
                        _dv = _obs_dims.get(_dk, {})
                        _ds = _dv.get("score", 0)
                        _dn = _dv.get("note", "")
                        _dw = int(_obs_w.get(_dk, 0) * 100)
                        _rows_obs.append(
                            f"| {_icon} **{_dname}** | {_grp} | ×{_dw}% | {_ds}/100 | {_dn} |"
                        )
                    st.markdown(
                        "| 軸 | 系統 | 重み | スコア | 備考 |\n"
                        "|---|---|---|---|---|\n" +
                        "\n".join(_rows_obs)
                    )
                _obs_issues = _roi.get("observability_issues", [])
                if _obs_issues:
                    st.markdown("**ペナルティ:**")
                    for _iss in _obs_issues:
                        st.markdown(f"- {_iss}")

            st.divider()
            st.markdown("#### 🔵 モダン度スコア")
            _mod_bk = _mod_data.get("breakdown", {})
            _mod_cols = st.columns(3)
            _cat_list = list(_mod_bk.items())
            for _ci, (_cat, _cdata) in enumerate(_cat_list):
                _sub = _cdata.get("subtotal", 0)
                _max = _cdata.get("max", 0)
                with _mod_cols[_ci % 3]:
                    st.markdown(f"**{_cat}** ({_sub}/{_max}点)")
                    for _item in _cdata.get("items", []):
                        st.markdown(f"- {_item}")
            if _mod_data.get("next_action"):
                st.info(f"💡 次のアクション: {_mod_data['next_action']}")

            st.divider()
            st.markdown("#### 🔵 GitHub活用スコア")
            if _gh_repos:
                _status_icon = {"active": "✅", "partial": "⚠️", "not_started": "❌"}
                _rows = []
                for _r in _gh_repos:
                    _icon = _status_icon.get(_r.get("status", ""), "❓")
                    _rows.append(
                        f"| {_r.get('rank','?')} | [{_r.get('name','')}]({_r.get('url','')}) "
                        f"| {_r.get('weight',0)*100:.0f}% "
                        f"| {_r.get('utilization',0)}/100 "
                        f"| {_r.get('contribution',0):.1f}pt "
                        f"| {_icon} {_r.get('status','')} "
                        f"| {_r.get('note','')} |"
                    )
                st.markdown(
                    "| # | リポジトリ | 重み | 活用度 | 寄与 | 状態 | メモ |\n"
                    "|---|-----------|------|--------|------|------|------|\n" +
                    "\n".join(_rows)
                )
                _gh_opp = _gh.get("top_opportunity", "")
                if _gh_opp:
                    st.info(f"💡 最優先アクション: {_gh_opp}")
                st.caption(f"評価日: {_gh.get('assessed_at','')} / 次回見直し: {_gh.get('next_review','')}")
            else:
                st.caption("データなし — anthropic_github_kpi.json を確認してください")

        style.kpi_wrap_end()
    else:
        st.warning("AIレベルスコアデータなし — run_kpi_collectors.pyを実行してください")

    # ── システム構成サマリー（稼働状況の詳細はtab2参照）────────────────────────────
    total_pl = counts.get("total", 0) or len(DAILY_PIPELINES) + len(CHAIN_PIPELINES) + len(WEEKLY_PIPELINES)

    style.kpi_wrap_start("info")
    c1, c2, c3 = st.columns(3)
    c1.metric("スケジューラ", f"{total_pl}本")
    c2.metric("エージェント", f"{len(AGENTS)}個")
    c3.metric("ページ数", "3")
    style.kpi_wrap_end()

    subtab1, subtab2, subtab3 = st.tabs(["⏱️ 実行タイムライン", "🤖 エージェント構成", "📁 ファイル・フォルダ構成"])

    # ── 実行タイムライン ────────────────────────────────────────────────────────
    with subtab1:
        col_daily, col_chain = st.columns([1, 1])

        with col_daily:
            style.section_card_start("📅 日次タスク（毎日）", f"{len(DAILY_PIPELINES)}タスク", "info")
            for t, name, role in DAILY_PIPELINES:
                is_master = "PrefectDailyFlow" in name or "DailyDriver" in name
                icon = "⭐" if is_master else "▸"
                bg = "background:#fffbe6;border-left:3px solid #f5a623;padding:4px 8px;border-radius:4px;" if is_master else ""
                st.markdown(
                    f'<div style="{bg}margin-bottom:6px">'
                    f'<span style="font-family:monospace;color:#666">{t}</span> '
                    f'{icon} <b>{name}</b><br>'
                    f'<span style="color:#888;font-size:0.85em;margin-left:1.5em">{role}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            style.section_card_end()

        with col_chain:
            style.section_card_start("⚡ チェーンパイプライン（週次・Prefect）", f"{len(CHAIN_PIPELINES)}チェーン", "ok")
            for t, name, role in CHAIN_PIPELINES:
                st.markdown(
                    f'<div style="margin-bottom:8px">'
                    f'<span style="font-family:monospace;color:#666">{t}</span> '
                    f'⚡ <b>{name}</b><br>'
                    f'<span style="color:#888;font-size:0.85em;margin-left:1.5em">{role}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            style.section_card_end()

            style.section_card_start("📆 週次タスク", f"{len(WEEKLY_PIPELINES)}タスク", "info")
            for t, name, role in WEEKLY_PIPELINES:
                st.markdown(
                    f'<div style="margin-bottom:5px">'
                    f'<span style="font-family:monospace;color:#666">{t}</span> '
                    f'▸ <b>{name}</b><br>'
                    f'<span style="color:#888;font-size:0.85em;margin-left:1.5em">{role}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            style.section_card_end()

        style.section_card_start("⭐ DailyDriver — ステップ詳細（毎日 21:26）", "master", "ok")
        for no, name, desc in DAILY_DRIVER_STEPS:
            st.markdown(
                f'**Step {no}:** {name} — '
                f'<span style="color:#555;font-size:0.9em">{desc}</span>',
                unsafe_allow_html=True,
            )
        style.section_card_end()

    # ── エージェント構成 ────────────────────────────────────────────────────────
    with subtab2:
        style.section_card_start("🤖 エージェント一覧（agents_prompts.json）", f"{len(AGENTS)}エージェント", "info")

        agent_24h = {}
        if agent_stats and "by_agent" in agent_stats:
            for a in agent_stats["by_agent"]:
                agent_24h[a.get("agent_name", "")] = a

        header_cols = st.columns([2, 3, 2, 1, 1])
        header_cols[0].markdown("**エージェント名**")
        header_cols[1].markdown("**役割**")
        header_cols[2].markdown("**使用パイプライン**")
        header_cols[3].markdown("**24h実行**")
        header_cols[4].markdown("**エラー率**")

        for agent_name, role, pipeline in AGENTS:
            cols = st.columns([2, 3, 2, 1, 1])
            cols[0].code(agent_name)
            cols[1].write(role)
            cols[2].write(pipeline)
            stat = agent_24h.get(agent_name, {})
            runs_24h = stat.get("total_runs", "-")
            error_rate = stat.get("error_rate_pct", None)
            cols[3].write(str(runs_24h))
            if error_rate is not None:
                color = "🔴" if error_rate > 20 else "🟢"
                cols[4].write(f"{color} {error_rate:.0f}%")
            else:
                cols[4].write("—")
        style.section_card_end()

        style.section_card_start("⚖️ モデル割り当てルール", "", "info")
        st.markdown("""
| モデル | 用途 | 条件 |
|--------|------|------|
| **Haiku** | 分類・短文生成・施策抽出・コメント | 常時優先（低コスト） |
| **Sonnet** | 複雑な分析・戦略レポート・CX評価 | 必要時のみ |
| **Opus** | 判断要時・手動のみ | 自動化禁止 |

> **Token使用率80%超** → 全Haikuモード切替（CrowdStrikeリスク軽減）
> **調査・検索・2ファイル以上読み込み** → 無条件でHaikuに委譲
        """)
        style.section_card_end()

        style.section_card_start("🔄 自動改善ループ（毎日 21:20 MempalaceMaintenance）", "", "ok")
        st.markdown("""
```
agent_runs.jsonl (7日分)
    ↓ get_run_stats()
問題エージェント検出（エラー率 > 20% / レイテンシ > 30s）
    ↓ phase3b_run_agent_levelup()
改善プロンプト生成 → agents_prompts.json 自動更新
    ↓
次回実行から改善済みプロンプトで動作
```
        """)
        style.section_card_end()

    # ── ファイル・フォルダ構成 ───────────────────────────────────────────────────
    with subtab3:
        style.section_card_start("📁 スクリプトフォルダ構成（.claude/scripts/）", "", "info")
        header_cols = st.columns([1, 3, 3, 2])
        header_cols[0].markdown("**状態**")
        header_cols[1].markdown("**フォルダ**")
        header_cols[2].markdown("**内容**")
        header_cols[3].markdown("**備考**")
        for status, folder, desc, note in FOLDERS:
            cols = st.columns([1, 3, 3, 2])
            cols[0].write(status)
            cols[1].code(folder)
            cols[2].write(desc)
            cols[3].write(note)
        style.section_card_end()

        style.section_card_start("💾 主要データファイル（単一ライター原則）", "", "info")
        header_cols = st.columns([3, 4, 2])
        header_cols[0].markdown("**ファイル名**")
        header_cols[1].markdown("**内容**")
        header_cols[2].markdown("**書込プロセス**")
        for fname, desc, writer in DATA_FILES:
            cols = st.columns([3, 4, 2])
            cols[0].code(fname)
            cols[1].write(desc)
            cols[2].write(writer)
        style.section_card_end()

        DEPRECATED_SCRIPTS = [
            ("generate_dashboard.py",        "廃止済み",  "firebase_dashboard_pusher.py に移行済み"),
            ("task_queue_protector.py",       "廃止済み",  "task_queue.json 廃止・Kanban移行完了"),
            ("mempalace_session_update.py",   "廃止済み",  "conversation_logger.py に統合済み"),
        ]
        style.section_card_start("🗑️ 削除候補スクリプト（AGENTS_MAP.md 参照）",
                                  f"{len(DEPRECATED_SCRIPTS)}件", "warn")
        st.caption("機能は移行済み。削除しても影響なし。会長確認後に削除可。")
        for fname, status, reason in DEPRECATED_SCRIPTS:
            cols = st.columns([3, 1, 4])
            cols[0].code(fname)
            cols[1].write(f"🔴 {status}")
            cols[2].write(reason)
        style.section_card_end()

        if cost_report and cost_report.get("pipelines"):
            reduction_candidates = [
                p for p in cost_report["pipelines"]
                if p.get("reduction_candidate")
            ]
            high_cost = [
                p for p in cost_report["pipelines"]
                if p.get("high_cost_flag")
            ]
            if reduction_candidates or high_cost:
                style.section_card_start("⚠️ 削減候補（パイプラインコスト分析）",
                                          f"{len(reduction_candidates)}件", "warn")
                if reduction_candidates:
                    st.markdown("**削減候補（30日アクティビティなし・非収益系）:**")
                    for p in reduction_candidates:
                        st.markdown(f"- `{p.get('name', '?')}`")
                if high_cost:
                    st.markdown("**高コスト（Claude呼び出し50回以上）:**")
                    for p in high_cost:
                        st.markdown(f"- `{p.get('name', '?')}` — {p.get('claude_calls', 0)}回")
                style.section_card_end()

# ══════════════════════════════════════════════════════════════════════════════
# ⚙️ 稼働状況（旧 3_稼働状況.py）
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    def _safe2(fn, default=None):
        try:
            return fn()
        except Exception:
            return default

    sys_info       = _safe2(lambda: data_loader.system_info(), {})
    pl_status2     = _safe2(lambda: data_loader.pipeline_status(), {})
    cost_report2   = _safe2(lambda: data_loader.pipeline_cost_report(), {})
    loop_data      = _safe2(lambda: data_loader.autonomous_loop(), {})
    ds             = _safe2(lambda: data_loader.datasource(), {})
    token_usage    = _safe2(lambda: data_loader.pipeline_token_usage(), {})
    all_tasks      = _safe2(lambda: data_loader.kanban_tasks(), [])
    all_outputs    = _safe2(lambda: data_loader.sync_outputs(), {})
    agent_run_data = _safe2(lambda: data_loader.agent_run_stats(), {})

    tab_pl, tab_loop, tab_res, tab_sched, tab_health = st.tabs([
        "⚙️ パイプライン", "🔄 ループログ", "💾 リソース", "⏱️ スケジュール", "🩺 実績・診断"
    ])
    tab_agent = tab_health  # エージェント実績を診断タブに統合（6→5サブタブ）

    # ── パイプライン ────────────────────────────────────────────────────────────
    with tab_pl:
        pipelines = pl_status2.get("pipelines", []) if pl_status2 else []
        counts2   = pl_status2.get("counts", {}) if pl_status2 else {}
        upd       = pl_status2.get("updated_at", "") if pl_status2 else ""

        style.section_card_start("⚙️ パイプライン稼働状況",
                                 "失敗あり" if counts2.get("failed", 0) else "正常",
                                 "err" if counts2.get("failed", 0) else "ok")
        if upd:
            st.caption(f"自動突合: {upd[:16]}  ｜  PIPELINES_DEF定義数: {pl_status2.get('total', 0)}")

        if counts2:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                style.kpi_wrap_start("ok")
                st.metric("✅ 正常", counts2.get("ok", 0))
                style.kpi_wrap_end()
            with c2:
                style.kpi_wrap_start("critical" if counts2.get("failed", 0) else "ok")
                st.metric("❌ 失敗", counts2.get("failed", 0))
                style.kpi_wrap_end()
            with c3:
                st.metric("🆕 未実行", counts2.get("never_ran", 0) + counts2.get("not_registered", 0))
            with c4:
                st.metric("⏸ 停止中", counts2.get("stopped", 0))

        ICON = {"ok": "✅", "failed": "❌", "never_ran": "🆕", "not_registered": "⚠️",
                "stopped": "⏸", "integrated": "🔗", "unknown": "❓"}
        BADGE = {
            "ok":             ("badge-ok",   "正常"),
            "failed":         ("badge-err",  "失敗"),
            "never_ran":      ("badge-info", "未実行"),
            "not_registered": ("badge-warn", "未登録"),
            "stopped":        ("badge-warn", "停止"),
            "integrated":     ("badge-info", "統合"),
            "unknown":        ("badge-info", "不明"),
        }

        categories = sorted({p.get("category", "") for p in pipelines if p.get("category")})
        sel_cat = st.selectbox("カテゴリ絞込", ["すべて"] + categories, key="pl_cat2")
        filtered = [p for p in pipelines if sel_cat == "すべて" or p.get("category") == sel_cat]
        filtered_sorted = sorted(filtered,
            key=lambda p: p.get("log_last_run") or p.get("sched_last_run") or "", reverse=True)

        output_files = (all_outputs or {}).get("files", [])

        if filtered_sorted:
            style.trow_head()
            for p in filtered_sorted:
                overall = p.get("overall", "unknown")
                icon    = ICON.get(overall, "❓")
                last    = p.get("log_last_run") or p.get("sched_last_run") or "-"
                pname   = p.get("name", "")
                badge_cls, badge_label = BADGE.get(overall, ("badge-info", overall))
                tok = token_usage.get(pname, {}) if token_usage else {}
                tok_str = ""
                if tok and tok.get("total", 0) > 0:
                    tok_str = f"🪙{tok['total']:,} (${tok.get('cost_usd', 0):.3f})"
                style.trow(icon, pname, str(last)[:16], badge_label, badge_cls, tok_str)
        else:
            st.info("該当するパイプラインがありません")

        if filtered_sorted:
            names = [p.get("name", "") for p in filtered_sorted]
            sel_name = st.selectbox("詳細を表示するパイプライン", ["（選択）"] + names, key="pl_detail2")
            if sel_name and sel_name != "（選択）":
                p = next((x for x in filtered_sorted if x.get("name") == sel_name), None)
                if p:
                    overall   = p.get("overall", "unknown")
                    icon      = ICON.get(overall, "❓")
                    last      = p.get("log_last_run") or p.get("sched_last_run") or "-"
                    pname     = p.get("name", "")
                    task_name = p.get("task_name", "")
                    tok       = token_usage.get(pname, {}) if token_usage else {}

                    related_tasks = [
                        t for t in (all_tasks or [])
                        if pname and (
                            pname in (t.get("description") or "").lower()
                            or pname in (t.get("name") or "").lower()
                        )
                    ]
                    related_tasks = sorted(related_tasks, key=lambda t: t.get("updated_at", ""), reverse=True)[:3]
                    related_outputs = [f for f in output_files
                                       if pname and pname.replace("_", "-") in f["name"].lower()
                                       or pname in f["name"].lower()][:3]

                    with st.expander(f"{icon} **{pname}**  🕐{last}", expanded=True):
                        st.caption(f"カテゴリ: {p.get('category', '')}  ｜  スケジュール: {p.get('schedule', '')}")

                        script_ok = "✅" if p.get("script_exists") else "❌"
                        sched_ok  = {"ok": "✅", "never": "🆕", "not_registered": "⚠️", "integrated": "🔗"}.get(p.get("sched_status", ""), "❓")
                        log_ok    = {"success": "✅", "failed": "❌", "no_log": "—", "unknown": "❓"}.get(p.get("log_status", ""), "❓")
                        st.write(f"スクリプト{script_ok}  スケジューラ{sched_ok}({p.get('sched_state', '')})  ログ{log_ok}")

                        if p.get("next_run"):
                            st.caption(f"⏰ 次回: **{p['next_run']}**")

                        if tok and tok.get("total", 0) > 0:
                            cost  = tok.get("cost_usd", 0)
                            model = tok.get("model", "")
                            ts    = (tok.get("ts", "") or "")[:10]
                            st.caption(
                                f"🪙 直近トークン: {tok.get('total', 0):,}  "
                                f"（in:{tok.get('input', 0):,} / out:{tok.get('output', 0):,}）"
                                f"  💰 推定課金: ${cost:.4f}  ｜  {ts} {model}"
                            )
                        else:
                            ts_raw = tok.get("ts", "") if tok else ""
                            ts_str = (ts_raw or "")[:10]
                            st.caption(f"🪙 直近トークン: —（計測なし）" + (f"  ｜  {ts_str}" if ts_str else ""))

                        st.markdown("**📋 直近起票タスク**")
                        if related_tasks:
                            for t in related_tasks:
                                tid    = t.get("id", "")
                                tname  = t.get("name", "")[:40]
                                status = t.get("status", "")
                                s_icon = {"open": "🔵", "in_progress": "🟡", "to_verify": "🟠", "closed": "✅"}.get(status, "⬜")
                                st.write(f"{s_icon} [{tid}] {tname}")
                        else:
                            st.caption("— なし")

                        st.markdown("**📦 直近の成果物**")
                        if related_outputs:
                            for f in related_outputs:
                                st.write(f"📝 {f['name']} ({f['size_kb']}KB  {f['modified']})")
                        else:
                            st.caption("— なし")

                        if p.get("stop_reason"):
                            st.warning(p["stop_reason"])
                        if p.get("last_lines"):
                            st.code(p["last_lines"][-300:], language=None)

                        if task_name and overall not in ("stopped",):
                            if st.button(f"▶ 今すぐ実施", key=f"run2_{pname}"):
                                ok = data_loader.send_pipeline_command(pname, task_name)
                                if ok:
                                    st.success(f"✅ コマンド送信完了。次回pusher実行時に {task_name} を起動します。")
                                else:
                                    st.error("❌ コマンド送信失敗")
        style.section_card_end()

        if cost_report2:
            reduction = cost_report2.get("reduction_candidates", [])
            high_cost = cost_report2.get("high_cost_pipelines", [])
            upd_cr    = cost_report2.get("updated", "")
            if reduction or high_cost:
                style.section_card_start("🔻 削減候補・高コストパイプライン", "要確認", "warn")
                st.caption(f"分析日: {upd_cr}  ｜  対象パイプライン: {cost_report2.get('total', 0)}本")
                if reduction:
                    import pandas as pd
                    st.markdown(f"**⚠️ 削減候補（直近30日アクティビティなし・非収益系）: {len(reduction)}件**")
                    df_red = pd.DataFrame([{
                        "パイプライン名": r["name"],
                        "カテゴリ":       r["category"],
                        "スケジュール":   r["schedule"],
                    } for r in reduction])
                    st.dataframe(df_red, use_container_width=True, hide_index=True)
                if high_cost:
                    import pandas as pd
                    st.markdown(f"**🔥 高コスト（直近30日50回以上のclaude呼び出し）: {len(high_cost)}件**")
                    df_hc = pd.DataFrame([{
                        "パイプライン名":       h["name"],
                        "claude呼び出し(30d)": h["claude_calls_30d"],
                        "カテゴリ":             h["category"],
                        "収益貢献":             "✅" if h["revenue_contrib"] else "❌",
                    } for h in high_cost])
                    st.dataframe(df_hc, use_container_width=True, hide_index=True)
                style.section_card_end()

    # ── ループログ ──────────────────────────────────────────────────────────────
    with tab_loop:
        realtime = ds.get("realtime", {}) if ds else {}
        claude   = ds.get("claude_code_status", {}) if ds else {}
        _running = bool(realtime and realtime.get("execution_status")) or \
                   bool(claude and claude.get("cpu_percent", 0) > 0)
        style.section_card_start("🔄 実施中タスク・処理",
                                 "稼働中" if _running else "待機中",
                                 "info" if _running else "ok")
        if realtime and realtime.get("execution_status"):
            st.info(f"**実行状態:** {realtime.get('execution_status', '-')}  ｜  **詳細:** {realtime.get('running_detail', '-')}")
        elif claude and claude.get("cpu_percent", 0) > 0:
            st.info(f"**Claude Code:** CPU {claude.get('cpu_percent', 0):.1f}%  ｜  メモリ {claude.get('memory_mb', 0):.0f}MB")
        else:
            st.success("✓ 実施中タスクなし（待機中）")
        style.section_card_end()

        style.section_card_start("🔄 自律ループ実行ログ")
        if loop_data:
            total  = loop_data.get("total_lines", 0)
            upd2   = loop_data.get("updated_at", "")
            last_e = loop_data.get("last_entry", "")
            st.caption(f"累計ログ行数: **{total:,}** 行  ｜  取得時刻: {upd2[:16]}")
            if last_e:
                st.info(f"**最終エントリ:** {last_e}")
            lines_text = loop_data.get("lines", "")
            if lines_text:
                style.section_title("最新150行")
                st.code(lines_text, language=None)
        else:
            st.info("自律ループログがありません")
        style.section_card_end()

    # ── リソース ────────────────────────────────────────────────────────────────
    with tab_res:
        style.section_card_start("🖥️ システムリソース")
        if sys_info:
            c1, c2, c3, c4, c5 = st.columns(5)
            bat = sys_info.get("battery_percent", 0)
            chg = sys_info.get("charging", False)
            with c1:
                st.metric("🔋 バッテリー", f"{bat}%" + (" ⚡" if chg else ""))
            with c2:
                st.metric("💻 CPU", f"{sys_info.get('cpu_percent', 0):.1f}%")
            with c3:
                st.metric("🧠 メモリ", f"{sys_info.get('memory_percent', 0):.1f}%")
            with c4:
                d_p = sys_info.get("disk_percent", 0)
                d_u = sys_info.get("disk_used_gb", 0)
                d_t = sys_info.get("disk_total_gb", 0)
                st.metric("💾 ディスク(C:)", f"{d_p:.0f}%", help=f"{d_u}GB / {d_t}GB")
            with c5:
                st.metric("🌐 NW", sys_info.get("ssid", "不明"))
        else:
            st.info("システム情報がありません")
        style.section_card_end()

        style.section_card_start("💾 ディスク使用率")
        if ds:
            disk_info = ds.get("disk_usage", {})
            if disk_info:
                for drive, info in (disk_info.items() if isinstance(disk_info, dict) else []):
                    if isinstance(info, dict):
                        pct = info.get("percent", 0)
                        col = "🔴" if pct > 85 else "🟡" if pct > 70 else "🟢"
                        st.write(f"{col} **{drive}**: {pct:.0f}%  ({info.get('used_gb', 0):.1f}GB / {info.get('total_gb', 0):.1f}GB)")
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
        style.section_card_end()

        _is_company = bool(sys_info) and ("SWing" in sys_info.get("ssid", "") or "SWingS" in sys_info.get("ssid", ""))
        style.section_card_start("🌐 ネットワーク状況",
                                 "会社NW" if _is_company else "私用NW",
                                 "err" if _is_company else "ok")
        if sys_info:
            ssid    = sys_info.get("ssid", "不明")
            icon    = "🏢" if _is_company else "🏠"
            nw_type = "会社" if _is_company else "私用"
            st.metric(f"{icon} 現在のNW", ssid, help=f"種別: {nw_type}")
            if _is_company:
                st.error("⛔ 会社ネットワーク（SWing/SWingS）接続中 — Claudeの動作を停止します")
            st.caption("会社NW（swing / 43.x.x.x）接続中はエージェント・パイプラインを自動停止。ネットワーク未接続時も同様。")
        else:
            st.info("ネットワーク情報がありません")
        style.section_card_end()

    # ── スケジュール ────────────────────────────────────────────────────────────
    with tab_sched:
        scheduler  = _safe2(lambda: data_loader.scheduler_tasks(), [])
        exec_times = _safe2(lambda: data_loader.execution_times(), {})

        def _parse_next(val):
            if not val:
                return None
            s = str(val).strip()
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"):
                try:
                    return datetime.strptime(s[:len(fmt) + 2] if "%H" in fmt else s[:10], fmt).date()
                except Exception:
                    continue
            return None

        style.section_card_start("📅 直近の実行予定")
        today    = date.today()
        tomorrow = today + timedelta(days=1)
        week_end = today + timedelta(days=7)
        buckets  = {"🔹 今日": [], "🔹 明日": [], "🔹 今週": []}
        for t in (scheduler or []):
            if not isinstance(t, dict):
                continue
            d = _parse_next(t.get("next_run"))
            if d is None:
                continue
            label = f"{t.get('name', '?')}  🕐 {str(t.get('next_run', ''))[:16]}"
            if d == today:
                buckets["🔹 今日"].append(label)
            elif d == tomorrow:
                buckets["🔹 明日"].append(label)
            elif today < d <= week_end:
                buckets["🔹 今週"].append(label)
        if any(buckets.values()):
            cols = st.columns(3)
            for col, (head, items) in zip(cols, buckets.items()):
                with col:
                    st.markdown(f"**{head}（{len(items)}件）**")
                    for it in sorted(items)[:15]:
                        st.write(f"• {it}")
                    if not items:
                        st.caption("（予定なし）")
        else:
            st.info("ℹ️ 次回実行予定の時刻は取得対象外です。各タスクの実行時刻は下の「スケジュール定義」表を参照してください。")
        style.section_card_end()

        style.section_card_start("🖥️ タスクスケジューラ（実データ）")
        if scheduler:
            import pandas as pd
            STATE_LABELS = {"0": "不明", "1": "無効", "2": "キュー", "3": "✅ 待機中", "4": "🔵 実行中"}
            df = pd.DataFrame(scheduler)
            if "state" in df.columns:
                df["state"] = df["state"].astype(str).map(lambda s: STATE_LABELS.get(s, s))
                df = df.rename(columns={"name": "タスク名", "state": "状態"})
            display_cols = [c for c in ["タスク名", "状態", "schedule", "last_run", "next_run", "status"] if c in df.columns]
            st.caption(f"登録タスク数: {len(scheduler)} 件")
            st.dataframe(df[display_cols] if display_cols else df, use_container_width=True, hide_index=True)
        else:
            st.info("スケジューラ情報がありません")
        style.section_card_end()

        style.section_card_start("📋 スケジュール定義（パイプライン別）")
        SCHEDULE_DEF = [
            ("ProductResearcher",   "毎日 21:00",        "市場調査",   "StrategyChain先頭・市場機会ToT分析"),
            ("DailyLoopImprover",   "毎日 21:01",        "自己改善",   "Loopログ自動改善"),
            ("DefectPredictor",     "毎日 21:04",        "品質管理",   "欠陥予測ToT"),
            ("QaObserver",          "毎日 21:06",        "品質管理",   "QA観察ToT"),
            ("MabBizdev",           "毎日 21:10",        "収益生成",   "MABビジネスアイデア評価"),
            ("DailyBizDev",         "毎日 21:12",        "収益生成",   "bizdev→marketing→reviewer"),
            ("ProcessMonitor",      "毎日 21:15",        "監視",       "プロセス監視"),
            ("BlockerReviewer",     "毎日 21:18",        "管理",       "ブロッカーレビュー"),
            ("ErrorRecovery",       "毎日 21:16",        "インフラ",   "エラー自動回復"),
            ("DailyPriorityEngine", "毎日 21:20",        "管理",       "優先度エンジン"),
            ("GDriveBackup",        "毎日 21:21",        "インフラ",   "Google Drive差分バックアップ"),
            ("DailyQiitaPipeline",  "毎日 21:22",        "コンテンツ", "Qiita記事パイプライン"),
            ("KdpWriter",           "週次（木）21:05",    "コンテンツ", "KDP電子書籍生成"),
            ("FreelanceResearcher", "週次（火）21:07",    "市場調査",   "フリーランス案件調査"),
            ("AutonomousLoop",      "週次（日）21:23",    "自己改善",   "自律タスク探索・実行ループ"),
            ("AgentSupervisor",     "週次（日）21:23",    "管理",       "エージェント監督"),
            ("MdOptimizer",         "週次（日）21:27",    "管理",       "MDファイル最適化"),
            ("PipelineImprover",    "週次（日）21:29",    "自己改善",   "パイプライン改善"),
            ("RevenueTracker",      "週次（月）21:23",    "収益生成",   "収益追跡"),
            ("BizPDCA",             "週次（月・木）21:25", "収益生成",  "PDCA実行"),
        ]
        import pandas as pd
        df_def = pd.DataFrame(SCHEDULE_DEF, columns=["タスク名", "実行時刻", "カテゴリ", "説明"])
        st.dataframe(df_def, use_container_width=True)
        style.section_card_end()

        style.section_card_start("⏱️ パイプライン実行統計")
        if exec_times:
            pipelines_et = exec_times.get("pipelines", [])
            total_runs   = exec_times.get("total_runs", 0)
            st.caption(f"累計実行: {total_runs:,} 回")
            if pipelines_et:
                import pandas as pd
                df_exec = pd.DataFrame(pipelines_et)
                display = [c for c in ["name", "avg_seconds", "run_count", "last_run", "last_status"] if c in df_exec.columns]
                st.dataframe(df_exec[display] if display else df_exec, use_container_width=True)
        else:
            st.info("実行統計データがありません")
        style.section_card_end()

    # ── エージェント実績 ────────────────────────────────────────────────────────
    with tab_agent:
        import pandas as pd

        s24  = agent_run_data.get("last_24h", {}) if agent_run_data else {}
        s7d  = agent_run_data.get("last_7d", {}) if agent_run_data else {}
        upd3 = agent_run_data.get("updated_at", "") if agent_run_data else ""

        if not s24 or s24.get("error"):
            st.info("エージェント実行ログがまだありません。次回パイプライン実行後に反映されます。")
        else:
            style.section_card_start("🤖 エージェント実績（直近24h）", "", "ok")
            if upd3:
                st.caption(f"最終更新: {upd3[:16]}")

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("総呼び出し",       s24.get("total", 0))
            c2.metric("スキップ",         s24.get("skipped", 0))
            c3.metric("エラー",           s24.get("errors", 0),
                      delta=None if not s24.get("errors") else "要確認",
                      delta_color="inverse")
            c4.metric("平均レイテンシ",   f"{s24.get('avg_latency_ms', 0):,} ms")
            c5.metric("合計コスト",       f"${s24.get('total_cost_usd', 0):.4f}")

            by_agent_24 = s24.get("by_agent", {})
            if by_agent_24:
                rows = []
                for ag, v in by_agent_24.items():
                    err_rate = v["errors"] / v["count"] if v["count"] else 0
                    rows.append({
                        "エージェント":       ag,
                        "呼び出し回数":       v["count"],
                        "平均レイテンシ(ms)": v["avg_latency_ms"],
                        "エラー率":           f"{err_rate:.0%}",
                        "コスト($)":          f"{v['cost_usd']:.5f}",
                        "⚠️":                "🔴" if err_rate > 0.2 or v["avg_latency_ms"] > 30000 else "",
                    })
                df24 = pd.DataFrame(rows)
                st.dataframe(df24, use_container_width=True)

                problems = [r for r in rows if r["⚠️"]]
                if problems:
                    st.warning(
                        f"**自動改善対象**: {', '.join(r['エージェント'] for r in problems)}  "
                        f"（エラー率>20% または 平均レイテンシ>30s → 次回 mempalace_maintenance で自動改善）"
                    )
            style.section_card_end()

            if s7d and not s7d.get("error"):
                style.section_card_start("📅 直近7日間サマリー", "", "ok")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("総呼び出し(7d)",     s7d.get("total", 0))
                c2.metric("エラー(7d)",         s7d.get("errors", 0))
                c3.metric("平均レイテンシ(7d)", f"{s7d.get('avg_latency_ms', 0):,} ms")
                c4.metric("合計コスト(7d)",     f"${s7d.get('total_cost_usd', 0):.4f}")

                by_agent_7d = s7d.get("by_agent", {})
                if by_agent_7d:
                    rows7 = []
                    for ag, v in by_agent_7d.items():
                        err_rate = v["errors"] / v["count"] if v["count"] else 0
                        rows7.append({
                            "エージェント":       ag,
                            "呼び出し回数":       v["count"],
                            "平均レイテンシ(ms)": v["avg_latency_ms"],
                            "エラー率":           f"{err_rate:.0%}",
                            "コスト($)":          f"{v['cost_usd']:.5f}",
                        })
                    st.dataframe(pd.DataFrame(rows7), use_container_width=True)
                style.section_card_end()

        # ── Eval品質スコア（tab4から統合）────────────────────────────────────────
        def _safe_eval_t2(fn, default=None):
            try: return fn()
            except Exception: return default

        eval_t2 = _safe_eval_t2(lambda: data_loader.eval_status(), {})
        by_agent_eval_t2 = (eval_t2 or {}).get("by_agent", [])
        if by_agent_eval_t2:
            style.section_card_start("📊 エージェント別 Evalスコア（直近）", "", "info")
            cols_ea = st.columns([2, 1, 1, 1, 3])
            cols_ea[0].markdown("**エージェント**")
            cols_ea[1].markdown("**平均スコア**")
            cols_ea[2].markdown("**実験件数**")
            cols_ea[3].markdown("**エラー率**")
            cols_ea[4].markdown("**Verdict分布**")
            for a_ea in sorted(by_agent_eval_t2, key=lambda x: -(x.get("avg_score") or 0)):
                avg_ea   = a_ea.get("avg_score")
                err_ea   = a_ea.get("error_rate_pct", 0)
                v_ea     = a_ea.get("verdicts", {})
                sico     = "🔴" if (avg_ea and avg_ea < 4) else ("🟡" if (avg_ea and avg_ea < 6) else "🟢")
                eico     = "🔴" if err_ea > 20 else ("🟡" if err_ea > 5 else "🟢")
                vstr     = " / ".join(f"{k[:6]}:{c}" for k, c in sorted(v_ea.items(), key=lambda x: -x[1])[:3]) or "—"
                cols_eb  = st.columns([2, 1, 1, 1, 3])
                cols_eb[0].code(a_ea.get("agent", "?"))
                cols_eb[1].write(f"{sico} {avg_ea:.1f}" if avg_ea else "—")
                cols_eb[2].write(str(a_ea.get("experiment_count", 0)))
                cols_eb[3].write(f"{eico} {err_ea:.0f}%")
                cols_eb[4].write(vstr)
            style.section_card_end()

    # ── 診断・健全性 ────────────────────────────────────────────────────────────
    with tab_health:
        def _safe_h(fn, default=None):
            try:
                return fn()
            except Exception:
                return default

        sh_h       = _safe_h(lambda: data_loader.get_system_health(), {})
        sys_info_h = _safe_h(lambda: data_loader.system_info(), {})
        ds_h       = _safe_h(lambda: data_loader.datasource(), {})

        pl_status_h = _safe_h(lambda: data_loader.pipeline_status(), {})
        pl_counts_h = pl_status_h.get("counts", {}) if pl_status_h else {}
        failed_pipes_h = [p for p in pl_status_h.get("pipelines", [])
                         if p.get("overall") == "failed"] if pl_status_h else []

        alerts_static_h = (sh_h or {}).get("alerts", []) if sh_h else []
        alerts_dynamic_h = [
            {"level": "error", "message": f"パイプライン失敗: {p.get('name')} ({p.get('schedule','')})"}
            for p in failed_pipes_h
        ]
        alerts_h = alerts_dynamic_h + alerts_static_h

        orphan_h    = (sh_h or {}).get("orphan_process_count", 0) or 0
        stale_h     = (sh_h or {}).get("stale_output_count", 0) or 0
        sh_last_h   = ((sh_h or {}).get("last_run", "") or "")[:16] if sh_h else ""

        _health_color_h = "critical" if failed_pipes_h else "ok"
        style.section_card_start("🩺 診断サマリー", "", _health_color_h)
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("🔴 パイプライン失敗", f"{len(failed_pipes_h)}本",
                   delta="要確認" if failed_pipes_h else None, delta_color="inverse")
        mc2.metric("✅ 正常稼働", f"{pl_counts_h.get('ok', 0)}本")
        mc3.metric("🔄 孤立プロセス", orphan_h,
                   delta="要確認" if orphan_h > 0 else None, delta_color="inverse")
        mc4.metric("📦 放置成果物", stale_h,
                   delta="要確認" if stale_h > 5 else None, delta_color="inverse")
        if sh_last_h:
            st.caption(f"最終更新: {sh_last_h}")
        style.section_card_end()

        style.section_card_start("💾 ディスク使用率")
        disk_info_h = (ds_h or {}).get("disk_usage", {}) if ds_h else {}
        if disk_info_h and isinstance(disk_info_h, dict):
            for drv_h, dinfo_h in disk_info_h.items():
                if not isinstance(dinfo_h, dict):
                    continue
                pct_h  = dinfo_h.get("percent", 0)
                used_h = dinfo_h.get("used_gb", 0)
                tot_h  = dinfo_h.get("total_gb", 0)
                st.write(f"**{drv_h}** — {pct_h:.0f}%  ({used_h:.1f}GB / {tot_h:.1f}GB)")
                st.progress(min(pct_h / 100, 1.0))
                if pct_h > 85:
                    st.warning(f"⚠️ {drv_h} ディスク使用率 {pct_h:.0f}% — 85%超。不要ファイル削除を推奨")
        elif sys_info_h:
            d_p_h = sys_info_h.get("disk_percent", 0)
            d_u_h = sys_info_h.get("disk_used_gb", 0)
            d_t_h = sys_info_h.get("disk_total_gb", 0)
            st.write(f"**C:** {d_p_h:.0f}%  ({d_u_h:.1f}GB / {d_t_h:.1f}GB)")
            st.progress(min(d_p_h / 100, 1.0))
            if d_p_h > 85:
                st.warning(f"⚠️ ディスク使用率 {d_p_h:.0f}% — 85%超。不要ファイル削除を推奨")
        else:
            st.info("ディスク情報がありません")
        style.section_card_end()

        if alerts_h:
            style.section_card_start("⚠️ 既知の問題一覧", f"{len(alerts_h)}件", "warn")
            for al_h in alerts_h:
                if isinstance(al_h, dict):
                    level_h = al_h.get("level", "warn")
                    msg_h   = al_h.get("message", str(al_h))
                    icon_h  = "🔴" if level_h == "error" else "🟡"
                    st.markdown(f"{icon_h} {msg_h}")
                else:
                    st.markdown(f"🟡 {al_h}")
            style.section_card_end()
        else:
            style.section_card_start("✅ 問題なし", "", "ok")
            st.success("現在アラートはありません")
            style.section_card_end()

        extra_h = {k: v for k, v in (sh_h or {}).items()
                   if k not in ("alerts", "pipeline_count", "scheduler", "last_run",
                                "flows", "orphan_process_count", "stale_output_count")}
        if extra_h:
            style.section_card_start("📋 その他の健全性情報")
            for k_h, v_h in extra_h.items():
                if isinstance(v_h, dict):
                    with st.expander(f"**{k_h}**"):
                        for kk_h, vv_h in v_h.items():
                            st.write(f"**{kk_h}:** {vv_h}")
                else:
                    st.write(f"**{k_h}:** {v_h}")
            style.section_card_end()

# ══════════════════════════════════════════════════════════════════════════════
# 🏢 経営体制（旧 7_経営体制.py）
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    AGENTS_DEF = [
        {"name": "bizdev",            "dept": "事業開発部",   "purpose": "ビジネスアイデア生成",          "pipelines": "daily_bizdev"},
        {"name": "marketing",         "dept": "事業開発部",   "purpose": "マーケティング戦略",            "pipelines": "daily_bizdev, bizdev_optimizer, product_monitor, product_researcher"},
        {"name": "opensource_analyst","dept": "事業開発部",   "purpose": "OSS収益化分析",                 "pipelines": "daily_opensource"},
        {"name": "copywriter",        "dept": "コンテンツ部", "purpose": "コピーライティング改善",        "pipelines": "product_monitor"},
        {"name": "cx_expert",         "dept": "コンテンツ部", "purpose": "CXリサーチ→製品評価（統合）",   "pipelines": "cx_improver, gumroad_publisher, cx_publisher_base"},
        {"name": "reviewer",          "dept": "コンテンツ部", "purpose": "ビジネス/コンテンツ品質評価",  "pipelines": "daily_bizdev, doc_sync"},
        {"name": "content_pipeline",  "dept": "コンテンツ部", "purpose": "Qiita/note・KDP・コンテンツ生成", "pipelines": "kdp_writer, metrics_collector, content_strategist, content_writer, qiita_publisher, note_publisher, zenn_publisher"},
        {"name": "risk_assessor",     "dept": "品質管理部",   "purpose": "法的・セキュリティリスク評価",  "pipelines": "risk_manager"},
        {"name": "quality_gater",     "dept": "経営管理部",   "purpose": "システム/パイプライン品質評価", "pipelines": "system_evaluator, bizdev_optimizer, monthly_optimizer, name_consistency_check, pipeline_improver, self_audit_engine, mempalace_maintenance"},
        {"name": "biz_pdca_planner",  "dept": "財務部",       "purpose": "PDCA施策立案（先行指標→施策生成）", "pipelines": "biz_pdca, freelance_researcher, leading_indicators"},
        {"name": "social_growth",     "dept": "集客部",       "purpose": "SNS投稿評価・A/Bテスト",        "pipelines": "note_analytics, x_post_qa_doctor"},
        {"name": "infra_ops",         "dept": "IT部",         "purpose": "コアインフラ・自律ループ・タスク調整", "pipelines": "autonomous_loop, system_health, realtime_kg_feed, dashboard_issue_resolver"},
        {"name": "monitoring_agent",  "dept": "IT部",         "purpose": "システム監視・ヘルスチェック",  "pipelines": "system_health, system_evaluator"},
        {"name": "backup_agent",      "dept": "IT部",         "purpose": "バックアップ・環境保全・同期",  "pipelines": "gdrive_backup, doc_sync"},
    ]

    PIPELINES_DEF3 = [
        {"name": "strategy_chain",        "cat": "収益生成",  "schedule": "月・木 21:07",                    "agents": "biz_pdca_planner, marketing",    "desc": "KG抽出→product_researcher→daily_bizdev→bizdev_optimizer→leading_indicators→risk_manager→biz_pdcaをLangGraphで実行"},
        {"name": "biz_pdca",              "cat": "収益生成",  "schedule": "StrategyChain（月・木）経由",     "agents": "biz_pdca_planner",              "desc": "Check→Act→Planの3フェーズ週2回自動実行。施策TOP3をAI生成してtask_queueに追加"},
        {"name": "daily_bizdev",          "cat": "収益生成",  "schedule": "StrategyChain（月・木）",         "agents": "bizdev marketing reviewer",     "desc": "bizdev→marketing→reviewerの3エージェント連鎖。7点以上を『推奨』として翌日の行動候補に昇格"},
        {"name": "daily_driver",          "cat": "収益生成",  "schedule": "毎日 21:26",                      "agents": "infra_ops",                     "desc": "【統合オーケストレーター】毎日21:26実行。市場調査+戦略チェーン→各種パイプラインを逐次実行"},
        {"name": "daily_opensource",      "cat": "収益生成",  "schedule": "週次（月）21:05",                 "agents": "opensource_analyst",            "desc": "GitHubトレンド・Hacker News・Product Huntから週次収集。OSSの収益化パターンを分析"},
        {"name": "freelance_researcher",  "cat": "収益生成",  "schedule": "ContentChain（火・金）",          "agents": "biz_pdca_planner",              "desc": "【ToT：3経路】クラウドワークス・ランサーズ・Coconalaのフリーランス案件を3視点で並列調査"},
        {"name": "gumroad_publisher",     "cat": "収益生成",  "schedule": "ContentChain（火・金）",          "agents": "cx_expert content_pipeline",    "desc": "CXスコアが低い製品を優先評価→改善英語コピー生成→Gumroad製品ページに適用"},
        {"name": "content_chain",         "cat": "コンテンツ","schedule": "火・金 21:03",                    "agents": "content_pipeline social_growth","desc": "metrics→content_strategist→content_writer→cx_improver→qiita/note/zenn/kdp/gumroad publisherを逐次実行"},
        {"name": "content_strategist",    "cat": "コンテンツ","schedule": "ContentChain（火・金）",          "agents": "content_pipeline",              "desc": "unified_metrics+brand_memory+now.mdを統合分析し3プラットフォームのコンテンツ戦略プランを立案"},
        {"name": "content_writer",        "cat": "コンテンツ","schedule": "ContentChain（火・金）",          "agents": "content_pipeline",              "desc": "content_plan.jsonに基づきqiita/note/kdp/gumroad向けコンテンツを一括生成"},
        {"name": "cx_improver",           "cat": "コンテンツ","schedule": "ContentChain（火・金）",          "agents": "cx_expert",                     "desc": "CXトレンド調査→全製品評価→即効改善案最大5件自動生成"},
        {"name": "metrics_collector",     "cat": "コンテンツ","schedule": "ContentChain（火・金）",          "agents": "content_pipeline",              "desc": "note/Qiita/KDP売上を一元収集しunified_metrics.jsonに保存。旧note_analyticsを統合"},
        {"name": "note_publisher",        "cat": "コンテンツ","schedule": "ContentChain（火・金）",          "agents": "cx_expert content_pipeline",    "desc": "content_drafts.jsonの最新noteドラフトを投稿するthin adapter"},
        {"name": "product_monitor",       "cat": "コンテンツ","schedule": "週次（水）23:03",                 "agents": "marketing copywriter",          "desc": "競合価格・レビュー監視／タイトル・説明文コピー改善をweekly統合実行"},
        {"name": "qiita_publisher",       "cat": "コンテンツ","schedule": "ContentChain（火・金）",          "agents": "content_pipeline",              "desc": "content_drafts.jsonの最新QiitaドラフトをPlaywright経由でQiitaに投稿"},
        {"name": "zenn_publisher",        "cat": "コンテンツ","schedule": "ContentChain（火・金）",          "agents": "content_pipeline",              "desc": "experience_log.mdの実体験を素材にZenn技術記事を生成・保存"},
        {"name": "autonomous_loop",       "cat": "自己改善",  "schedule": "週次（日）22:48",                 "agents": "infra_ops",                     "desc": "目標達成まで自動タスク探索→実装→完了→次タスクを繰り返す"},
        {"name": "bizdev_optimizer",      "cat": "自己改善",  "schedule": "StrategyChain / ContentChain",    "agents": "quality_gater marketing",       "desc": "bizdev_report→パターン抽出→MABスコア更新→mab_recommendation.json生成"},
        {"name": "mempalace_maintenance", "cat": "自己改善",  "schedule": "毎日 21:20",                      "agents": "quality_gater",                 "desc": "5フェーズ構成。Kanban/会話記録/CLI履歴収集→claude -pで判断→mempalace記録→agent_levelup実行"},
        {"name": "monthly_optimizer",     "cat": "自己改善",  "schedule": "月次 15日 21:29",                 "agents": "quality_gater",                 "desc": "skills_optimizer+token_optimizer統合版。スキル使用状況・トークン消費量を収集後に統合改善提案を生成"},
        {"name": "name_consistency_check","cat": "自己改善",  "schedule": "週次（日）21:24",                 "agents": "quality_gater",                 "desc": "変数名・ファイル名・エージェント名・タスク名の命名一貫性を週次チェック"},
        {"name": "pipeline_improver",     "cat": "自己改善",  "schedule": "SystemLoop（水・土）",            "agents": "quality_gater",                 "desc": "ログ解析・コード健全性・類似パイプライン検出・自動修正・Claude改善提案を週次実行"},
        {"name": "realtime_kg_feed",      "cat": "自己改善",  "schedule": "タスク完了時",                    "agents": "infra_ops",                     "desc": "autonomous_loopのタスク実行完了/失敗直後に呼ばれるKGフィード。失敗パターンをmempalace KGにリアルタイム記録"},
        {"name": "self_audit_engine",     "cat": "自己改善",  "schedule": "SystemLoop（水・土）経由",        "agents": "quality_gater",                 "desc": "経営コンサルタント視点で自問自答を5問生成。課題があればKanbanタスクに自動投入"},
        {"name": "system_loop",           "cat": "自己改善",  "schedule": "水・土 21:06",                    "agents": "monitoring_agent quality_gater","desc": "KG抽出→self_audit_engine→system_health→pipeline_improver→system_evaluatorを逐次実行"},
        {"name": "leading_indicators",    "cat": "監視",      "schedule": "StrategyChain（月・木）",         "agents": "biz_pdca_planner",              "desc": "収益以外の先行指標（タスク完了数・施策実施率等）を日次集計"},
        {"name": "risk_manager",          "cat": "監視",      "schedule": "StrategyChain（月・木）",         "agents": "risk_assessor",                 "desc": "法的・プラットフォームToS・セキュリティの3カテゴリを週次評価"},
        {"name": "user_acquisition_funnel","cat": "監視",     "schedule": "無効化中",                        "agents": "monitoring_agent",              "desc": "note→製品ページ→購入のファネルメトリクスを日次更新。collect_real_metrics()実装まで停止中"},
        {"name": "doc_sync",              "cat": "インフラ",  "schedule": "週次（日）21:27",                 "agents": "backup_agent reviewer",         "desc": "MD監査（陳腐化検出）/ memory→mempalace KG差分同期 / Obsidian→mempalace KG同期"},
        {"name": "fetch_claude_usage_auto","cat": "インフラ", "schedule": "毎日 21:30",                      "agents": "infra_ops",                     "desc": "claude.aiのCap使用率をusage_cache.jsonに記録。daily_driver終了後に自動実行"},
        {"name": "gdrive_backup",         "cat": "インフラ",  "schedule": "毎日 21:21",                      "agents": "backup_agent",                  "desc": "Claude Code環境全体をGoogle Drive差分バックアップ。PC故障・環境移行時の完全復元を想定"},
        {"name": "orphan_process_killer", "cat": "インフラ",  "schedule": "Stopフック + スケジューラ",       "agents": "infra_ops",                     "desc": "セッション終了時に自動実行。残留した重いPowerShell/Python/bashプロセスを検出・終了"},
        {"name": "consultation_manager",  "cat": "意思決定",  "schedule": "セッションから呼び出し",          "agents": "cx_expert content_pipeline",    "desc": "複数の専門エージェントに質問を投げ、推奨・リスク・次のアクションを集約して意思決定を支援"},
        {"name": "product_researcher",    "cat": "市場調査",  "schedule": "StrategyChain（月・木）",         "agents": "marketing",                     "desc": "市場機会をToT3経路で並列分析し、QAドクター製品の競合ベンチマークを実行"},
    ]

    SKILLS_DEF = [
        {"cmd": "/draft-message",  "dept": "会社業務",  "desc": "困ったメール・Teamsを状況説明だけで下書き（催促・依頼・謝罪・報告対応）",              "status": "未使用"},
        {"cmd": "/make-pptx",      "dept": "会社業務",  "desc": "箇条書きや表をそのままPowerPointスライドに変換する（報告・提案・ハンドオーバー対応）", "status": "未使用"},
        {"cmd": "/office-to-md",   "dept": "会社業務",  "desc": "OfficeファイルをMarkdownに変換してClaudeに読ませる（PPTX/DOCX/XLSX対応）",           "status": "未使用"},
        {"cmd": "/note-draft",     "dept": "コンテンツ","desc": "note記事の構成・見出し・本文下書きをターゲット読者に合わせてCTA付きで作成する",         "status": "未使用"},
        {"cmd": "/eval-idea",      "dept": "ビジネス",  "desc": "ビジネスアイデアをDevil's Advocate思考＋3軸スコアで評価し、致命的な穴と改善策を指摘する","status": "✓ 使用中"},
        {"cmd": "/agent-status",   "dept": "システム",  "desc": "Claudeのバックグラウンドプロセスとエージェントログをリアルタイムで表示する",            "status": "未使用"},
    ]

    n_pl3 = len(PIPELINES_DEF3)
    n_ag3 = len(AGENTS_DEF)

    def _safe3(fn, default=None):
        try:
            return fn()
        except Exception:
            return default

    pl_logs3     = _safe3(lambda: data_loader.pipeline_logs(), {})
    exec_t3      = _safe3(lambda: data_loader.execution_times(), {})
    agents_ctx3  = _safe3(lambda: data_loader.agents_context(), {})
    token_usage3 = _safe3(lambda: data_loader.pipeline_token_usage(), {})
    exec_map3    = {p["name"]: p for p in (exec_t3 or {}).get("pipelines", [])}

    # 体制概要
    style.section_card_start("📊 組織体制・AI最高経営責任者")
    col_left, col_right = st.columns([1, 1])
    with col_left:
        style.section_title("📊 体制図")
        st.markdown("""
| 役職 | 担当 |
|---|---|
| 👑 **会長（ユーザー）** | 意思決定・最終判断 |
| 🤖 **社長 Claude**（Main: Sonnet） | CEO・オーケストレーター |
| 🏭 COO（日常業務統括） | 日常業務統括・タスク実行 |

**部門一覧:**
事業開発部 / コンテンツ部 / 品質管理部 / 経営管理部 / 財務部 / 集客部 / IT部
""")
    with col_right:
        style.section_title("🤖 社長 AI Chief Executive Officer")
        st.info("""
実績ある自律型AIエグゼクティブ。アイデア創出から収益化まで短期完結が得意。
指示待ちゼロ、常に先手を打つ経営スタイル。

⚡ 自律実行　💡 アイデア量産　🎯 顧客ニーズ発見　🚀 短期収益化　🤖 AI活用エキスパート
""")
    style.section_card_end()

    # システム構造概要
    style.section_card_start("🏗️ システム構造概要")
    s1, s2, s3 = st.columns(3)
    s1.metric("⚙️ パイプライン", f"{n_pl3} 本")
    s2.metric("🤖 エージェント", f"{n_ag3} 種")
    s3.metric("🔗 チェーン数", "3 本（戦略・コンテンツ・システム）")
    st.caption(f"AIパイプライン {n_pl3} 本 が {n_ag3} 種のエージェントを共有利用。")
    style.section_card_end()

    subtab3_1, subtab3_2, subtab3_3, subtab3_4, subtab3_5 = st.tabs([
        "⚙️ パイプライン一覧",
        "👥 エージェント一覧",
        "🎯 スキル一覧",
        "🔗 チェーン設計",
        "🗺️ アーキテクチャ図",
    ])

    with subtab3_1:
        import pandas as pd
        style.section_card_start(f"⚙️ パイプライン一覧（{n_pl3} 本）")
        categories3 = sorted(set(p["cat"] for p in PIPELINES_DEF3))
        selected_cat3 = st.selectbox("カテゴリで絞り込み", ["すべて"] + categories3, key="cat3_pl")
        filtered3 = PIPELINES_DEF3 if selected_cat3 == "すべて" else [p for p in PIPELINES_DEF3 if p["cat"] == selected_cat3]
        st.caption(f"表示: {len(filtered3)} 本 / 全 {n_pl3} 本")

        for p in filtered3:
            logs_raw3   = (pl_logs3 or {}).get("logs", pl_logs3)
            logs_entry3 = logs_raw3.get(p["name"], {}) if isinstance(logs_raw3, dict) else {}
            if not isinstance(logs_entry3, dict):
                logs_entry3 = {}
            status3     = logs_entry3.get("status", "unknown")
            last_run3   = logs_entry3.get("last_run", "—")
            last_lines3 = logs_entry3.get("last_lines", "")
            tok_entry3  = (token_usage3 or {}).get(p["name"], {})
            tokens3     = tok_entry3.get("total", 0)
            cost3       = tok_entry3.get("cost_usd", 0)
            tok_ts3     = (tok_entry3.get("ts", "") or "")[:10]
            stopped3    = "停止" in p["schedule"] or "⏸" in p["schedule"]
            haishi3     = "廃止" in p["desc"] or "統合済み" in p["desc"]
            icon3 = "⏸" if stopped3 else ("🗑" if haishi3 else ("✅" if status3 == "success" else "❌" if status3 == "failed" else "⬜"))

            with st.expander(f"{icon3} **{p['name']}** — {p['cat']} ／ {p['schedule']}"):
                c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                with c1:
                    st.caption(p["desc"])
                    st.write(f"**エージェント:** {p['agents']}")
                with c2:
                    st.write(f"**最終実行:** {last_run3}")
                    st.write(f"**状態:** {status3}")
                with c3:
                    if tokens3:
                        st.write(f"**トークン:** {tokens3:,}")
                        st.caption(f"${cost3:.4f}  {tok_ts3}")
                    else:
                        st.caption("トークン: —")
                with c4:
                    ei3 = exec_map3.get(p["name"], {})
                    if ei3:
                        st.write(f"**平均:** {ei3.get('avg_seconds','-')} 秒")
                        st.write(f"**累計:** {ei3.get('run_count',0)} 回")
                if last_lines3:
                    st.markdown("---")
                    st.code(str(last_lines3)[-300:], language=None)
        style.section_card_end()

    with subtab3_2:
        import pandas as pd
        style.section_card_start(f"👥 エージェント一覧（{n_ag3} 種）")
        departments3 = sorted(set(a["dept"] for a in AGENTS_DEF))
        for dept3 in departments3:
            agents3 = [a for a in AGENTS_DEF if a["dept"] == dept3]
            style.section_title(f"🏢 {dept3}")
            rows3 = [{"エージェント名": a["name"], "役割": a["purpose"], "使用パイプライン": a["pipelines"]} for a in agents3]
            st.dataframe(pd.DataFrame(rows3), use_container_width=True, hide_index=True)

        if (agents_ctx3 or {}).get("content"):
            with st.expander("📋 エージェント コンテキスト詳細", expanded=False):
                st.markdown(agents_ctx3["content"])
        style.section_card_end()

    with subtab3_3:
        import pandas as pd
        style.section_card_start(f"🎯 スキル一覧（{len(SKILLS_DEF)} 種）")
        df_sk = pd.DataFrame([
            {"コマンド": s["cmd"], "部門": s["dept"], "機能説明": s["desc"], "パイプライン活用": s["status"]}
            for s in SKILLS_DEF
        ])
        st.dataframe(df_sk, use_container_width=True, hide_index=True)
        style.section_card_end()

    with subtab3_4:
        style.section_card_start("🔗 チェーン設計")
        style.section_title("🔵 戦略チェーン（月・木 21:07）")
        st.markdown("""
市場調査 → BizDev → MAB最適化 → 先行指標 → リスク確認 → PDCA

| ステップ | スクリプト | 役割 | 出力ファイル |
|---|---|---|---|
| 🧠 KG抽出 | extract_chain_context.py | now.md/brand/learningから抽出 | chain_context.md |
| 🔍 市場調査 | product_researcher | ToT3経路で市場分析・競合ベンチマーク | market_analysis.md |
| 💡 BizDev | daily_bizdev | bizdev→marketing→reviewerの3連鎖 | bizdev_report.md（State経由） |
| 📊 MAB最適化 | bizdev_optimizer | パターン抽出→MABスコア更新 | mab_recommendation.json |
| 📈 先行指標 | leading_indicators | プロセス指標の日次集計 | leading_indicators.json |
| 🛡 リスク確認 | risk_manager | 法的・ToS・セキュリティ評価 | risk_assessment.md |
| 🔄 PDCA | biz_pdca | Check→Act→Planの3フェーズ | — |
""")

        style.section_title("🟢 コンテンツチェーン（火・金 21:03）")
        st.markdown("""
メトリクス収集 → 戦略立案 → コンテンツ生成 → CX品質レビュー → 各PF公開

| ステップ | スクリプト | 役割 | 出力ファイル |
|---|---|---|---|
| 📊 メトリクス収集 | metrics_collector | note/Qiita/KDP売上を一元収集 | unified_metrics.json |
| 🗺 戦略立案 | content_strategist | 3プラットフォームの戦略プラン立案 | content_plan.json |
| ✍ コンテンツ生成 | content_writer | qiita/note/kdp/gumroad向け一括生成 | content_drafts.json |
| ✅ 品質レビュー | cx_improver | CXトレンド調査→全製品評価 | cx評価+quick_wins |
| 🔄 CX改善ループ | cx_publisher_base | 改善コピー生成→各PF適用 | 改善コピー（英語） |
| 📢 各PF公開 | qiita/note/kdp/gumroad publisher | 各プラットフォームへ投稿 | 各PF適用完了 |
""")

        style.section_title("🟣 システム改善ループ（水・土 21:06）")
        st.markdown("""
インフラ監視 → 改善案生成 → 評価 → eval_reportが次週のインフラ監視インプットに戻る

| ステップ | スクリプト | 役割 | 出力ファイル |
|---|---|---|---|
| 🧠 KG抽出 | extract_chain_context.py | failures/learning/eval_reportから抽出 | chain_context.md |
| 🔍 インフラ監視 | system_health | ログERROR/リソース/スケジューラ整合性 | health_report.md |
| 🛠 改善案生成 | pipeline_improver | ログ解析・コード健全性・自動修正 | improvement.md |
| 📊 評価 | system_evaluator | 環境監査・パフォーマンス分析・改善提案 | eval_report.md |
| ↻ フィードバック | — | eval_report.md → system_health へ（次週） | — |
""")

        style.section_title("🔗 チェーン間連携ルール")
        st.markdown("""
**送信（戦略 → コンテンツ）**
- ✅ `extract_chain_context.py` が `market_analysis_*.md` を要約 → `chain_context_content.md` に書き出し → コンテンツチェーンの各ノードへ注入
- ✅ `market_score < 4.0` の日: `route_after_research()` が BizDev 2本をスキップ、`route_before_publish()` が `note_publisher` をスキップ（低品質日のLLM節約）

**受信（コンテンツ ← 戦略）**
- ✅ `node_context` が `chain_context_content.md` を読み込み → ContentState に `market_score` / `market_summary` を格納 → 各エージェントへ渡す
""")

        style.section_title("🛠 OSS移行進捗 — LangGraph + Prefect + OpenRouter")
        st.markdown("""
| フェーズ | 状態 | 解決した問題 |
|---|---|---|
| **フェーズ1: Prefect** | ✅ 完了 | チェーン途中で止まった場所の可視化 |
| **フェーズ2: LangGraph** | ✅ 完了 | 低スコア日のLLMスキップ（トークン30〜40%削減） |
| **フェーズ3: OpenRouter** | 🔍 検討中 | claude -p の従量課金（6/15〜）対策。6/15以降の実課金額を確認してから判断 |
""")
        st.info("Prefect可視化: `prefect server start` → ブラウザで `localhost:4200` → Flows → StrategyChain/ContentChain を選択")
        style.section_card_end()

    with subtab3_5:
        style.section_card_start("🗺️ アーキテクチャ図")
        dot3 = """
digraph {
    rankdir=LR
    node  [fontname="Helvetica" style="filled" shape="box" fontsize="11"]
    edge  [fontsize="9"]
    subgraph cluster_strategy {
        label="StrategyChain（月・木）" style="dashed" color="#3b82f6"
        node [fillcolor="#dbeafe"]
        PR [label="ProductResearcher"]
        BD [label="DailyBizDev"]
        BO [label="BizdevOptimizer"]
        RM [label="RiskManager"]
        BP [label="BizPDCA"]
        PR -> BD -> BO -> RM -> BP
    }
    subgraph cluster_content {
        label="ContentChain（火・金）" style="dashed" color="#22c55e"
        node [fillcolor="#dcfce7"]
        MC [label="MetricsCollector"]
        CS [label="ContentStrategist"]
        CW [label="ContentWriter"]
        CX [label="CXImprover"]
        PB [label="Publishers"]
        MC -> CS -> CW -> CX -> PB
    }
    subgraph cluster_system {
        label="SystemLoop（水・土）" style="dashed" color="#a855f7"
        node [fillcolor="#fae8ff"]
        SH [label="SystemHealth"]
        PI [label="PipelineImprover"]
        SE [label="SystemEvaluator"]
        SH -> PI -> SE
        SE -> SH [label="eval_report" style="dashed"]
    }
    subgraph cluster_infra {
        label="インフラ（毎日）" style="dashed" color="#f97316"
        node [fillcolor="#ffedd5"]
        GB [label="GDriveBackup"]
        FP [label="FirebasePusher"]
        MM [label="MempalaceMaintenance"]
    }
    FB  [label="Firebase\\nFirestore" shape="cylinder" fillcolor="#fde68a"]
    ST  [label="Streamlit\\nDashboard" shape="diamond" fillcolor="#bae6fd"]
    LF  [label="Local Logs/JSON" shape="parallelogram" fillcolor="#f1f5f9"]
    MP  [label="MemPalace\\n(SQLite KG)" shape="cylinder" fillcolor="#e9d5ff"]
    LF -> FP [label="read"]
    FP -> FB [label="push" color="#f97316"]
    FB -> ST [label="read" color="#0ea5e9"]
    MM -> MP [label="write"]
    GB -> LF [label="backup"]
}
"""
        st.graphviz_chart(dot3)

        style.section_title("📁 フォルダ配置方針")
        st.markdown("""
| フォルダ | 用途 |
|---|---|
| `agents/` | パイプライン・エージェント本体・メインスクリプト |
| `agents/data/` | JSON設定・キャッシュ・状態ファイル |
| `agents/logs/` | 実行ログ・エラーログ |
| `agents/platforms/` | プラットフォーム別スクリプト（Etsy/KDP等） |
| `agents/backups/` | バックアップファイル・復旧用スナップショット |
| `agents/_archive/` | 廃止スクリプト・歴史的記録 |
| `Sync/ai/brain/` | 毎セッション読むコア（now.md・map.md・me.md） |
| `Sync/ai/knowledge/` | 蓄積ナレッジ・claude -pキャッシュ |
| `Sync/ai/tasks/` | 常時参照データ（standing_orders・kanban_tasks） |
| `Sync/ai/outputs/` | パイプライン生成物（qiita・note・kdp） |
| `Sync/ai/secrets/` | APIキー・認証情報 |
""")
        style.section_card_end()

# ══════════════════════════════════════════════════════════════════════════════
# 🧠 AI管理（旧 8_AI管理.py）
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    def _safe4(fn, default=None):
        try:
            return fn()
        except Exception:
            return default

    # ── 4サブタブ + AI出力品質を統合 ──────────────────────────────────────────
    tab_knowledge, tab_growth, tab_ops, tab_outputs = st.tabs([
        "🧠 メモリ・知識",     # mempalace + Sync/aiコンテキスト
        "🚀 成長・改善",       # レベルアップ + 4層学習システム
        "📖 体制・ルール",     # ルールエンジン + エージェント体制
        "📦 生成物・評価",     # 生成物一覧 + AI出力品質
    ])
    tab_eval = tab_outputs  # AI出力品質を生成物タブに統合（5→4サブタブ）

    with tab_knowledge:
        # ── mempalace ─────────────────────────────────────────────────────────
        style.section_card_start("🧠 mempalace ナレッジ成長（直近14日）")
        mem = _safe4(lambda: data_loader.mempalace(), {})
        if mem:
            rows_m = mem.get("rows", [])
            if rows_m:
                import pandas as pd
                df_m = pd.DataFrame(rows_m)
                last_m = rows_m[-1] if rows_m else {}
                c1, c2, c3 = st.columns(3)
                with c1: st.metric("ルーム数",      last_m.get("rooms", "-"))
                with c2: st.metric("エンティティ数", last_m.get("entities", "-"))
                with c3: st.metric("トリプル数",     last_m.get("triples", "-"))
                style.section_title("📊 mempalace成長推移")
                if "date" in df_m.columns:
                    num_cols_m = [c for c in df_m.columns if c != "date"]
                    try:
                        for c in num_cols_m: df_m[c] = pd.to_numeric(df_m[c], errors="coerce")
                        st.line_chart(df_m.set_index("date")[num_cols_m])
                    except Exception: pass
                st.dataframe(df_m, use_container_width=True)
        else:
            st.info("mempalaceデータがありません")
        style.section_card_end()

        style.section_card_start("📦 mempalace ルーム別ナレッジ分布")
        rooms_data = _safe4(lambda: data_loader.mempalace_rooms(), {})
        if rooms_data:
            rooms_m    = rooms_data.get("rooms", {})
            latest_date_m = rooms_data.get("latest_date", "")
            history_m  = rooms_data.get("history", [])
            st.caption(f"最終更新: {latest_date_m}")
            if rooms_m:
                ROOM_LABELS = {
                    "general":       "汎用メモ（未分類）",
                    "products":      "製品情報",
                    "strategy":      "戦略・計画",
                    "lessons":       "失敗と学び",
                    "branding":      "ブランド・表現",
                    "diary":         "日記・振り返り",
                    "documentation": "ドキュメント",
                }
                ROOM_COLORS = {
                    "general": "🔵", "products": "🟢", "strategy": "🟣",
                    "lessons": "🟠", "branding": "🩷", "diary": "🔴", "documentation": "⚫",
                }
                total_m = sum(rooms_m.values()) if rooms_m else 0
                cols_m = st.columns(min(len(rooms_m), 4))
                for i, (room, cnt) in enumerate(sorted(rooms_m.items(), key=lambda x: -x[1])):
                    pct_m = (cnt / total_m * 100) if total_m else 0
                    label_m = ROOM_LABELS.get(room, room)
                    icon_m  = ROOM_COLORS.get(room, "⬜")
                    with cols_m[i % 4]:
                        st.metric(f"{icon_m} {label_m}", cnt, help=f"{pct_m:.1f}%")
                st.progress(1.0, text=f"合計 {total_m} ドロワー")

                issues_m = []
                if rooms_m.get("general", 0) / max(total_m, 1) > 0.8:
                    issues_m.append("⚠️ general集中度が高い — 製品/戦略/学習カテゴリへの再分類を推奨")
                for room_m in ("products", "strategy", "lessons"):
                    if rooms_m.get(room_m, 0) < 5:
                        issues_m.append(f"⚠️ {ROOM_LABELS.get(room_m, room_m)}が{rooms_m.get(room_m,0)}件のみ — 構造化ナレッジを優先追加")
                for iss in issues_m[:3]:
                    st.warning(iss)

                if history_m:
                    import pandas as pd
                    style.section_title("📅 ルーム別ドロワー数推移（直近14日）")
                    df_hist = pd.DataFrame(history_m)
                    if "date" in df_hist.columns:
                        room_cols = [c for c in df_hist.columns if c != "date"]
                        try:
                            for c in room_cols: df_hist[c] = pd.to_numeric(df_hist[c], errors="coerce")
                            st.line_chart(df_hist.set_index("date")[room_cols])
                        except Exception: pass
        else:
            st.info("ルーム別データがありません。firebase_dashboard_pusher.py を実行してください。")
        style.section_card_end()

        style.section_card_start("📖 Obsidian ナレッジ体系")
        OBSIDIAN_FOLDERS = [
            ("MOC",          "🗺️", "ナビゲーション起点。_HOME・Rules-MOC・Projects-MOC"),
            ("Rules",        "📏", "Claudeへの全行動ルール（ai/system/business/communication）"),
            ("Rules/ai",     "🤖", "AI振る舞い・Haiku委譲・設計ルール・モデル選択"),
            ("Rules/system", "⚙️", "ダッシュボード・MS Store・プロセス管理"),
            ("Rules/business","💼","コンテンツ施策・note・Etsy・LSルール"),
            ("Reference",    "📚", "ツール・APIキー・場所・チャネル状態の参照情報"),
            ("Preferences",  "👤", "プロフィール・PC制約・会長/社長呼称・NW環境"),
            ("Projects",     "🚀", "QA Doctor・claude-p課金対応・TOEIC UP"),
            ("Knowledge",    "💡", "成長戦略・mempalace設計・プラットフォーム分析"),
            ("raw",          "📥", "Web記事・メモの投入口（Karpathyパターン）"),
            ("wiki",         "📖", "コンパイル済み知識（sources/entities/concepts/synthesis）"),
            ("output",       "📤", "生成されたレポート・成果物"),
            ("Decisions",    "⚖️", "意思決定の記録"),
        ]
        st.markdown("**AI自律層（mempalace）** + **人間管理層（Obsidian）** の2層構造")
        st.markdown("- 🧠 **mempalace**: Claude セッション間記憶継続・KGグラフ検索・自動集約")
        st.markdown("- 📓 **Obsidian**: ビジュアルグラフ・手動編集・Web記事クリップ・ルール閲覧")
        st.markdown("- 📥 **raw/ → wiki/**: Web記事を投入→AIがコンパイル→知識ページ生成（Karpathyパターン）")
        st.markdown("- 🔄 **週次同期**: Obsidian → mempalace KGバックアップ（毎週日曜 21:27）")

        obs = _safe4(lambda: data_loader.obsidian_stats(), {})
        if obs:
            o1, o2 = st.columns(2)
            o1.metric("📝 総ノート数", obs.get("total_notes", 0))
            o2.metric("🆕 直近14日追加", obs.get("recent_14d", 0))
            folders_obs = obs.get("folders", {})
            if folders_obs:
                style.section_title("📁 Vault フォルダ構成")
                rows_obs = [{"フォルダ": k, "件数": v} for k, v in sorted(folders_obs.items(), key=lambda x: -x[1])]
                import pandas as pd
                st.dataframe(pd.DataFrame(rows_obs), use_container_width=True, hide_index=True)

        style.section_title("📁 フォルダ構成")
        cols_obs = st.columns(3)
        for i, (folder, icon, desc) in enumerate(OBSIDIAN_FOLDERS):
            with cols_obs[i % 3]:
                st.markdown(f"{icon} **{folder}**  \n{desc}")
        style.section_card_end()

        # ── Sync/ai コンテキスト（旧7ミニタブ → エキスパンダーに変換）──────────
        brain4 = _safe4(lambda: data_loader.sync_brain(), {})
        tasks4 = _safe4(lambda: data_loader.sync_tasks(), {})
        ll4    = _safe4(lambda: data_loader.lessons_learned(), {})

        style.section_card_start("📋 Sync/ai コンテキスト")
        st.caption(f"最終更新: {(brain4 or {}).get('updated_at', '')[:16]}")

        for label4, content4 in [
            ("🟢 now.md",            (brain4 or {}).get("now", "")),
            ("📌 Standing Orders",   (tasks4 or {}).get("standing_orders", "")),
            ("🧩 コンテキスト",       (tasks4 or {}).get("claude_context", "")),
            ("👤 me.md",             (brain4 or {}).get("me", "")),
            ("🎨 brand_memory",      (brain4 or {}).get("brand_memory", "")),
            ("🏗️ OSS移行計画",       (brain4 or {}).get("oss_migration_plan", "")),
            ("📚 lessons_learned",   (ll4 or {}).get("content", "")),
        ]:
            with st.expander(label4, expanded=(label4 == "🟢 now.md")):
                if content4:
                    st.markdown(content4[:3000])
                else:
                    st.caption("データなし")
        style.section_card_end()

    with tab_growth:
        # ── レベルアップ ──────────────────────────────────────────────────────
        style.section_card_start("🚀 エージェント レベルアップ状況")
        status_lv = _safe4(lambda: data_loader.levelup_status(), {})
        if status_lv:
            if isinstance(status_lv, dict):
                for key, val in status_lv.items():
                    if isinstance(val, dict):
                        with st.expander(f"**{key}**", expanded=False):
                            for k2, v2 in val.items():
                                st.write(f"**{k2}:** {v2}")
                    elif isinstance(val, list):
                        st.markdown(f"**{key}**")
                        for item in val[:10]: st.write(f"- {item}")
                    else:
                        st.write(f"**{key}:** {val}")
        else:
            st.info("レベルアップ状況データがありません")
        style.section_card_end()

        style.section_card_start("📜 レベルアップ履歴")
        history_lv = _safe4(lambda: data_loader.levelup_history(), [])
        if history_lv:
            for h in sorted(history_lv, key=lambda x: x.get("date",""), reverse=True):
                date_lv    = h.get("date", "?")
                content_lv = h.get("content", "")
                with st.expander(f"📅 {date_lv}", expanded=False):
                    if content_lv: st.markdown(content_lv[:2000])
        else:
            st.info("レベルアップ履歴がありません")
        style.section_card_end()

        # ── 4層学習システム ───────────────────────────────────────────────────
        ls4 = _safe4(lambda: data_loader.learning_system(), {})
        style.section_card_start("🛡️ エラー再発防止：4層の多層防御")
        if ls4:
            active_count4 = ls4.get("active_count", 0)
            total4        = ls4.get("total", 4)
            overall4      = ls4.get("overall", "")
            flow4         = ls4.get("flow", "")
            c1, c2 = st.columns(2)
            c1.metric("有効レイヤー", f"{active_count4}/{total4}層",
                      delta="正常" if active_count4 == total4 else f"⚠ {total4 - active_count4}層未設定")
            c2.markdown(f"**全体状態:** {overall4}")
            for la in ls4.get("layers", []):
                icon4       = "🟢" if la.get("active") else "⚪"
                status_tag4 = f"✓ {la['status']}" if la.get("active") else la["status"]
                with st.expander(f"{icon4} Layer {la['layer']}: {la['name']} — {status_tag4}", expanded=la.get("active", False)):
                    st.markdown(f"**コンポーネント:** {la.get('components','')}")
                    st.markdown(f"**動作内容:** {la.get('desc','')}")
            st.markdown(f"**学習フロー:** {flow4}")
        else:
            st.info("学習システムデータがありません")
        style.section_card_end()

    with tab_ops:
        # ── ルールエンジン ────────────────────────────────────────────────────
        rule_data = _safe4(lambda: data_loader.rule_engine(), {})
        style.section_card_start("⚙️ ルールエンジン状態")
        if rule_data:
            r1, r2, r3 = st.columns(3)
            with r1: st.metric("🪝 フック数",      rule_data.get("hook_count", 0))
            with r2: st.metric("✅ 許可ルール数",   rule_data.get("allow_count", 0))
            with r3: st.metric("🔒 デフォルトモード", rule_data.get("default_mode", "-"))
            st.caption(f"最終更新: {(rule_data.get('updated_at','') or '')[:16]}")
            hook_types = rule_data.get("hook_types", [])
            if hook_types:
                style.section_title("🪝 登録フック")
                for ht in hook_types: st.write(f"• **{ht}**")
        else:
            st.info("ルールエンジンデータがありません")
        style.section_card_end()

        style.section_card_start("📋 主要ルール（CLAUDE.md）")
        for rule_name, desc in [
            ("🔴 会社NW接続時は完全停止",           "SWing/SWingS 検出→全ツール停止"),
            ("🔴 自動化スクリプトでOpus禁止",         "claude-haiku-4-5 推奨。Opusは自動化禁止"),
            ("🔴 subprocess.run直接禁止",             "safe_run/safe_popen に差し替え必須"),
            ("🔴 AtLogonトリガー禁止",                "BSOD防止。21:00〜21:30の定時スケジューラのみ"),
            ("🔴 Microsoft Store禁止",                "管理者権限なし。pip/scoopを使う"),
            ("🟡 Haiku委譲（閾値9）",                 "スコア≤9のタスクは全てHaiku"),
            ("🟡 新規スクリプト追加は会長明示指示のみ","システムシンプル化原則"),
        ]:
            st.markdown(f"**{rule_name}**  \n　{desc}")
        style.section_card_end()

        # ── エージェント体制 ──────────────────────────────────────────────────
        agents_ctx4 = _safe4(lambda: data_loader.agents_context(), {})
        insights4   = _safe4(lambda: data_loader.agent_insights(), {})
        style.section_card_start("📖 エージェント体制・成功パターン")
        if (agents_ctx4 or {}).get("content"):
            st.markdown(agents_ctx4["content"])
        patterns4 = (insights4 or {}).get("success_patterns", {})
        if patterns4:
            style.section_title("🌟 成功パターンライブラリ")
            for cat4, items4 in patterns4.items():
                if not isinstance(items4, list): continue
                with st.expander(f"**{cat4}** （{len(items4)}件）"):
                    for item4 in items4[-5:]:
                        if isinstance(item4, dict):
                            score4   = item4.get("score", 0)
                            summary4 = item4.get("summary", "")
                            ts4      = (item4.get("ts") or "")[:10]
                            color4   = "🟢" if score4 >= 8 else "🟡" if score4 >= 6 else "🔴"
                            st.write(f"{color4} {ts4} スコア{score4}: {summary4[:100]}")
        if not (agents_ctx4 or {}).get("content") and not patterns4:
            st.info("エージェント体制データがありません")
        style.section_card_end()

    with tab_outputs:
        outputs4 = _safe4(lambda: data_loader.sync_outputs(), {})
        style.section_card_start("📦 Sync/ai/outputs/ 生成物一覧")

        if outputs4:
            files4 = outputs4.get("files", [])
            total4o = outputs4.get("total", 0)
            st.caption(f"合計 {total4o} ファイル（最新40件表示）| 最終更新: {outputs4.get('updated_at','')[:16]}")

            if files4:
                import pandas as pd
                EXT_ICON = {".md": "📝", ".json": "📊", ".txt": "📄"}
                df4 = pd.DataFrame([{
                    "種類": EXT_ICON.get(f["ext"], "📁"),
                    "ファイル名": f["name"],
                    "サイズ(KB)": f["size_kb"],
                    "更新日": f["modified"],
                } for f in files4])
                st.dataframe(df4, use_container_width=True, hide_index=True)

                note_files4 = [f for f in files4 if f["name"].startswith("note_")]
                kdp_files4  = [f for f in files4 if f["name"].startswith("kdp_") or f["name"].startswith("chapter")]
                x_files4    = [f for f in files4 if f["name"].startswith("x_")]

                cols4 = st.columns(3)
                cols4[0].metric("📝 note下書き", len(note_files4))
                cols4[1].metric("📚 KDP原稿", len(kdp_files4))
                cols4[2].metric("🐦 X投稿", len(x_files4))
        else:
            st.info("生成物データがありません。firebase_dashboard_pusher.pyを実行してください。")
        style.section_card_end()

    # ── AI出力品質（旧 tab5）────────────────────────────────────────────────────
    with tab_eval:
        st.caption("🔍 AI出力品質: エージェントが生成したレポート・記事・分析の採点スコアと評価判定（推奨/条件付き/保留/却下）を追跡します")
    
        def _safe5(fn, default=None):
            try:
                return fn()
            except Exception:
                return default
    
        eval_data5    = _safe5(lambda: data_loader.eval_status(), {})
        failure_data5 = _safe5(lambda: data_loader.failure_patterns(), {})
    
        by_agent5    = (eval_data5 or {}).get("by_agent", [])
        total_exp5   = (eval_data5 or {}).get("total_experiments", 0)
        avg_score5   = (eval_data5 or {}).get("overall_avg_score")
        error_rate5  = (eval_data5 or {}).get("overall_error_rate_pct", 0)
        impl_status5 = (eval_data5 or {}).get("impl_status", {})
        impl_done5   = sum(1 for v in impl_status5.values() if v)
        impl_total5  = max(len(impl_status5), 7)
    
        style.kpi_wrap_start("info")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("実験記録", f"{total_exp5}件")
        c2.metric("平均スコア", f"{avg_score5:.1f} / 10" if avg_score5 else "—")
        c3.metric("エラー率", f"{error_rate5:.0f}%",
                  delta=f"+{error_rate5:.0f}%" if error_rate5 > 0 else None,
                  delta_color="inverse")
        c4.metric("実装済み機能", f"{impl_done5} / {impl_total5}項目")
        c5.metric("評価エージェント数", f"{len(by_agent5)}個")
        style.kpi_wrap_end()
    
        tab5_1, tab5_2, tab5_3, tab5_4 = st.tabs([
            "🗺️ 全体フロー",
            "📊 スコア分析",
            "⚠️ エラーパターン",
            "🗓️ 実装ロードマップ",
        ])
    
        with tab5_1:
            style.section_card_start("📍 Eval接触点マップ（全パイプライン）", "", "info")
            st.markdown("""
    > **凡例**: 🟢 実装済み &nbsp;|&nbsp; 🔲 計画中 &nbsp;|&nbsp; ⚪ Eval対象外
            """)
    
            PIPELINE_EVAL_MAP = [
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
    
            cols_h5 = st.columns([2, 3, 4, 1])
            cols_h5[0].markdown("**時刻 / 頻度**")
            cols_h5[1].markdown("**パイプライン**")
            cols_h5[2].markdown("**Eval接触点**")
            cols_h5[3].markdown("**状態**")
    
            for t5, name5, eval_point5, status5 in PIPELINE_EVAL_MAP:
                cols5 = st.columns([2, 3, 4, 1])
                cols5[0].markdown(f'<span style="font-family:monospace;color:#666">{t5}</span>',
                                  unsafe_allow_html=True)
                cols5[1].markdown(f"**{name5}**")
                cols5[2].markdown(f'<span style="color:#555;font-size:0.9em">{eval_point5}</span>',
                                  unsafe_allow_html=True)
                cols5[3].markdown(status5)
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
    
        with tab5_2:
            st.info("エージェント別スコア・Verdict分布は「⚙️ 稼働状況 > 🤖 エージェント実績」に統合しました。")
            if by_agent5:
                problem_agents5 = [a5 for a5 in by_agent5
                                   if (a5.get("avg_score") or 10) < 5 or a5.get("error_rate_pct", 0) > 20]
                if problem_agents5:
                    style.section_card_start(
                        f"🔴 要改善エージェント（スコア<5 or エラー率>20%）",
                        f"{len(problem_agents5)}件", "warn")
                    for a5 in problem_agents5:
                        avg_s5b    = a5.get("avg_score")
                        err_rate5b = a5.get("error_rate_pct", 0)
                        reasons5   = []
                        if avg_s5b and avg_s5b < 5:
                            reasons5.append(f"スコア低: {avg_s5b:.1f}/10")
                        if err_rate5b > 20:
                            reasons5.append(f"エラー率高: {err_rate5b:.0f}%")
                        st.markdown(f"- `{a5['agent']}` — {' / '.join(reasons5)}")
                    style.section_card_end()
            else:
                st.info("Firebase にデータがまだありません。`firebase_dashboard_pusher.py` を実行してください。")
    
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
    
        with tab5_3:
            fp_patterns5 = (failure_data5 or {}).get("patterns", {})
    
            if fp_patterns5:
                style.section_card_start("🔍 失敗パターン分類（mempalace phase3b が自動解析）", "", "warn")
                cols_h5c = st.columns([2, 2, 1, 3])
                cols_h5c[0].markdown("**エージェント**")
                cols_h5c[1].markdown("**エラー種別**")
                cols_h5c[2].markdown("**件数**")
                cols_h5c[3].markdown("**自動対処内容**")
                AUTO_FIX5 = {
                    "json_parse_failed": "プロンプトに「JSONのみ出力」制約を自動注入",
                    "claude_cli_error":  "プロンプト短縮・トークン削減を改善に反映",
                    "timeout":           "出力簡潔化指示を改善に反映",
                }
                for agent_name5c, err_counts5 in sorted(fp_patterns5.items()):
                    if not isinstance(err_counts5, dict):
                        continue
                    for err_type5, count5 in sorted(err_counts5.items(), key=lambda x: -x[1]):
                        cols5c = st.columns([2, 2, 1, 3])
                        cols5c[0].code(agent_name5c)
                        cols5c[1].write(f"`{err_type5}`")
                        cols5c[2].write(f"{'🔴' if count5 >= 3 else '🟡'} {count5}")
                        cols5c[3].write(AUTO_FIX5.get(err_type5, "次回phase3bで分析・改善"))
                style.section_card_end()
    
            elif by_agent5:
                style.section_card_start("⚠️ エラー率サマリー（agent_runs.jsonl）", "", "warn")
                error_agents5 = [a5 for a5 in by_agent5 if a5.get("error_rate_pct", 0) > 0]
                if error_agents5:
                    cols_h5d = st.columns([2, 1, 3])
                    cols_h5d[0].markdown("**エージェント**")
                    cols_h5d[1].markdown("**エラー率**")
                    cols_h5d[2].markdown("**状態**")
                    for a5d in sorted(error_agents5, key=lambda x: -x.get("error_rate_pct", 0)):
                        cols5d = st.columns([2, 1, 3])
                        cols5d[0].code(a5d["agent"])
                        rate5d = a5d.get("error_rate_pct", 0)
                        cols5d[1].write(f"{'🔴' if rate5d > 20 else '🟡'} {rate5d:.0f}%")
                        cols5d[2].write("phase3b次回実行時に自動分類・改善")
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
    
        with tab5_4:
            style.section_card_start("✅ 実装済み機能（Eval基盤）", "", "ok")
            DONE_ITEMS5 = [
                ("agent_runs.jsonl", "本番ログ記録（latency/error/cost/trace_id）",
                 "agent_framework.py → run_agent()"),
                ("experiments.jsonl", "評価ログ記録（score/verdict/blind_spots）",
                 "agent_framework.py → run_agent_with_retry()"),
                ("agents_prompts.json + Git", "プロンプトバージョン管理（履歴付き）",
                 "mempalace_maintenance.py → GitHub管理"),
                ("mempalace phase3b", "日次自動改善（run_stats→低スコア検知→prompt更新）",
                 "毎日 21:20 自動実行"),
                ("agent_run_stats Firebase", "エラー率・レイテンシのダッシュボード可視化",
                 "AIシステム → 稼働状況タブ"),
            ]
            for name5e, desc5e, where5e in DONE_ITEMS5:
                st.markdown(
                    f'✅ **{name5e}**'
                    f'<br><span style="color:#555;font-size:0.9em;margin-left:1.5em">'
                    f'{desc5e}<br>'
                    f'<span style="color:#888">実装場所: {where5e}</span>'
                    f'</span>',
                    unsafe_allow_html=True,
                )
                st.markdown("")
            style.section_card_end()
    
            style.section_card_start("🔲 未実装（次のステップ）", "優先順", "warn")
            PLANNED_ITEMS5 = [
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
            cols_h5e = st.columns([0.5, 2, 4, 1, 2])
            cols_h5e[0].markdown("**#**")
            cols_h5e[1].markdown("**機能**")
            cols_h5e[2].markdown("**内容**")
            cols_h5e[3].markdown("**工数**")
            cols_h5e[4].markdown("**統合先**")
            for no5, name5f, desc5f, effort5, where5f in PLANNED_ITEMS5:
                cols5e = st.columns([0.5, 2, 4, 1, 2])
                cols5e[0].write(no5)
                cols5e[1].code(name5f)
                cols5e[2].write(desc5f)
                cols5e[3].write(effort5)
                cols5e[4].write(where5f)
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
            """)
        style.section_card_end()

# ══════════════════════════════════════════════════════════════════════════════
# 💰 コスト管理
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    def _safe6(fn, default=None):
        try:
            return fn()
        except Exception:
            return default

    finance6    = _safe6(lambda: data_loader.get_finance(), {})
    usage_cache6 = _safe6(lambda: data_loader._local("usage_cache.json", {}), {})

    sonnet_pct6  = usage_cache6.get("sonnet_weekly_pct", 0) if usage_cache6 else 0
    haiku_pct6   = 100 - sonnet_pct6 if sonnet_pct6 else 0
    session_pct6 = usage_cache6.get("session_pct", 0) if usage_cache6 else 0
    all_pct6     = usage_cache6.get("all_models_weekly_pct", 0) if usage_cache6 else 0
    last_check6  = (usage_cache6.get("last_checked", "") or "")[:16] if usage_cache6 else ""

    cost_doc6   = finance6.get("cost_report", {}) if finance6 else {}
    token_doc6  = finance6.get("token_usage", {}) if finance6 else {}
    budget_doc6 = finance6.get("api_budget", {}) if finance6 else {}

    monthly_tokens6 = token_doc6.get("monthly_total", 0) if token_doc6 else 0
    est_cost6       = cost_doc6.get("estimated_monthly_usd", 0) if cost_doc6 else 0

    style.section_card_start("💰 コスト & モデル使用率")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("🪙 月間トークン", f"{monthly_tokens6:,}" if monthly_tokens6 else "未収集")
    with c2:
        sonnet_color = "🟠" if sonnet_pct6 > 30 else "🟢"
        st.metric("🤖 Sonnet比率（週次）", f"{sonnet_color} {sonnet_pct6}%", help="30%超でオレンジ警告")
    with c3:
        st.metric("💵 課金見込み（月）", f"${est_cost6:.2f}" if est_cost6 else "未収集")

    if sonnet_pct6 > 30:
        st.warning(f"⚠️ Sonnet使用率が {sonnet_pct6}% — 30%を超えています。Haikuへの委譲を強化してください。")

    st.info("ℹ️ 6/15以降の実データで蓄積中。usage_cache.json は毎日21:30に自動更新されます。")
    style.section_card_end()

    style.section_card_start("📊 Claude Cap使用状況（usage_cache.json）")
    if usage_cache6:
        cc1, cc2, cc3 = st.columns(3)
        cc1.metric("セッション使用率", f"{session_pct6}%")
        cc2.metric("全モデル週次使用率", f"{all_pct6}%")
        cc3.metric("Haiku比率（推定）", f"{haiku_pct6}%")
        if last_check6:
            st.caption(f"最終取得: {last_check6}")
        if all_pct6 >= 80:
            st.error("🔴 Token使用率80%超 — 全Haikuモード切替推奨（CrowdStrikeリスク軽減）")
        elif all_pct6 >= 60:
            st.warning(f"🟡 Token使用率 {all_pct6}% — Haiku優先を徹底してください")
    else:
        st.info("usage_cache.jsonが見つかりません。fetch_claude_usage_auto.pyを実行してください。")
    style.section_card_end()

    if budget_doc6:
        style.section_card_start("💳 APIバジェット")
        budget_items6 = budget_doc6.get("items", []) if isinstance(budget_doc6, dict) else []
        if budget_items6:
            import pandas as pd
            st.dataframe(pd.DataFrame(budget_items6), use_container_width=True, hide_index=True)
        else:
            for k6, v6 in (budget_doc6.items() if isinstance(budget_doc6, dict) else []):
                st.write(f"**{k6}:** {v6}")
        style.section_card_end()

# ══════════════════════════════════════════════════════════════════════════════
# 🔄 フロー実行ログ
# ══════════════════════════════════════════════════════════════════════════════
with tab6:
    from utils import flow_status_reader
    from utils import firebase_client as _fc7

    def _safe7(fn, default=None):
        try:
            return fn()
        except Exception:
            return default

    flow7 = _safe7(lambda: flow_status_reader.get_flow_status(_fc7), {})
    sh7   = _safe7(lambda: data_loader.get_system_health(), {})

    FLOWS7 = [
        ("maintenance", "MempalaceMaintenance",  "毎日 21:20"),
        ("strategy",    "StrategyChain",         "月・木 21:07"),
        ("content",     "ContentChain",          "火・金 21:03"),
        ("daily",       "DailyDriver",           "毎日 21:26"),
    ]

    style.section_card_start("🔄 Prefectフロー実行状況（Firestore: flow_status/latest）")
    col7s = st.columns(4)
    for i7, (key7, label7, sched7) in enumerate(FLOWS7):
        fdata7  = (flow7 or {}).get(key7, {})
        status7   = fdata7.get("status", "unknown") if isinstance(fdata7, dict) else "unknown"
        last_run7 = fdata7.get("last_run", None) if isinstance(fdata7, dict) else None
        duration7 = fdata7.get("duration_seconds", None) if isinstance(fdata7, dict) else None
        icon7     = flow_status_reader.status_icon(status7)
        last_str7 = flow_status_reader.format_last_run(last_run7)
        dur_str7  = f"{duration7:.0f}秒" if isinstance(duration7, (int, float)) and duration7 else "—"
        bg7  = "#f0fdf4" if status7 == "ok" else ("#fef2f2" if status7 not in ("ok", "unknown") else "#f8fafc")
        brd7 = "#22c55e" if status7 == "ok" else ("#ef4444" if status7 not in ("ok", "unknown") else "#94a3b8")
        with col7s[i7]:
            st.markdown(
                f'<div style="background:{bg7};border-left:4px solid {brd7};'
                f'padding:10px 12px;border-radius:6px;margin-bottom:8px">'
                f'<div style="font-size:1.4em">{icon7}</div>'
                f'<div style="font-weight:600;font-size:0.95em">{label7}</div>'
                f'<div style="color:#666;font-size:0.8em">{sched7}</div>'
                f'<div style="margin-top:6px;font-size:0.85em">状態: <b>{status7}</b></div>'
                f'<div style="font-size:0.8em;color:#555">最終: {last_str7}</div>'
                f'<div style="font-size:0.8em;color:#555">所要: {dur_str7}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    style.section_card_end()

    for key7e, label7e, _ in FLOWS7:
        fdata7e  = (flow7 or {}).get(key7e, {})
        if not isinstance(fdata7e, dict):
            continue
        status7e = fdata7e.get("status", "unknown")
        error7e  = fdata7e.get("error", "") or fdata7e.get("error_detail", "")
        if status7e not in ("ok", "unknown") and error7e:
            with st.expander(f"❌ {label7e} — エラー詳細"):
                st.code(str(error7e)[:1000], language=None)

    if not flow7 or all(
        (flow7.get(k, {}) or {}).get("status", "unknown") == "unknown"
        for k, _, _ in FLOWS7
    ):
        st.info("ℹ️ Firestoreにflow_statusデータがありません。Prefectフロー実行後に自動反映されます。")

    flows_in_sh7 = (sh7 or {}).get("flows", {})
    if flows_in_sh7 and isinstance(flows_in_sh7, dict):
        style.section_card_start("📋 system_health からのフロー情報")
        for fname7, finfo7 in flows_in_sh7.items():
            if isinstance(finfo7, dict):
                st.write(f"**{fname7}**: {finfo7}")
        style.section_card_end()