import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, style

st.set_page_config(page_title="🗺️ システム概要", page_icon="🗺️", layout="wide")
style.inject()

# ─── データ取得 ─────────────────────────────────────────────────────────────
pl_status    = data_loader.pipeline_status()
agent_stats  = data_loader.agent_run_stats()
sched_data   = data_loader.scheduler_tasks()
cost_report  = data_loader.pipeline_cost_report()
updated      = data_loader.last_updated()

counts = pl_status.get("counts", {}) if pl_status else {}
hdr_status = "err" if counts.get("failed", 0) else "ok"

style.page_header(
    "🗺️ システム概要",
    subtitle="パイプライン・エージェント・ファイル構成の全体図",
    updated=updated,
    status=hdr_status,
)

# ─── 定義データ（静的） ──────────────────────────────────────────────────────

DAILY_PIPELINES = [
    ("21:00", "DailyCheckinFetch",       "接続チェック・日次初期化"),
    ("21:15", "UserAcquisitionFunnel",   "ユーザー獲得ファネル分析"),
    ("21:20", "MempalaceMaintenance",    "メモリ保守・agent_levelup・知識補完"),
    ("21:21", "GDriveBackup",            "Googleドライブバックアップ"),
    ("21:26", "⭐ DailyDriver",          "メインオーケストレーター（全施策実行）"),
    ("21:27", "SelfAuditEngine",         "自己監査・品質評価"),
    ("21:30", "FetchClaudeUsageAuto",    "Claude使用量取得・Kanban起票"),
    ("21:55", "FirebaseDashboardPusher", "Firebaseへのデータプッシュ"),
]

CHAIN_PIPELINES = [
    ("月・木 21:05", "StrategyChain", "戦略分析 → BizDev → PDCAレポート（LangGraph+Prefect）"),
    ("火・金 21:05", "ContentChain",  "コンテンツ生成 → note記事投稿（LangGraph+Prefect）"),
]

WEEKLY_PIPELINES = [
    ("日 21:23", "AutonomousLoop",      "自律ループ実行（クラウド化エージェント統合）"),
    ("月 22:33", "DailyOpensource",     "OSS記事パイプライン"),
    ("水 23:03", "ProductMonitor",       "製品監視・市場情報収集"),
    ("日 22:57", "NameConsistencyCheck", "ファイル名一貫性チェック"),
    ("日 21:27", "DocSync",             "ドキュメント同期"),
    ("毎日 18:30", "DailyCheckinMailer", "チェックインメール送信"),
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
    ("🟢", "agents/",                    "メインスクリプト群（100+ファイル）",        "chains/agent_framework/tools等"),
    ("🟢", "agents/data/",               "キャッシュ・データファイル（JSON/JSONL）",  "単一ライター原則遵守"),
    ("🟢", "agents/logs/",               "実行ログ（JSONL・テキスト・biz_pdca）",    "日次ローテーション"),
    ("🟢", "agents/platforms/",          "外部PF連携（Gumroad/KDP/Etsy/Payhip）",  "pending多数"),
    ("🟢", "streamlit_dashboard/",       "Streamlitダッシュボード（8ページ）",        "push→自動デプロイ"),
    ("🟢", "wiki/",                       "ナレッジベース（audience-pains等）",        "DailyDriver参照"),
    ("🟢", "skills/",                     "Claude Codeスキル定義",                   "セッション内で起動"),
    ("🔴", "agents/deprecated_scripts/", "廃止スクリプト（参照用）",                 "削除候補"),
    ("🔴", "agents/_archive_20260602/",  "2026-06-02以前のアーカイブ",              "削除候補"),
]

DATA_FILES = [
    ("kanban_tasks.json",    "KanbanタスクDB（KT-XXX管理・単一情報源）",    "Firestoreプライマリ"),
    ("business_status.json", "収益・事業状況（BizDevタブの基盤）",          "daily_driver.py"),
    ("agents_prompts.json",  "エージェントプロンプト定義（9エージェント）",  "mempalace_maintenance.py"),
    ("agent_runs.jsonl",     "エージェント実行ログ（24h/7d統計ベース）",    "agent_framework.py"),
    ("datasource.json",      "リアルタイム実行状態・IDEステータスバー",      "daily_driver.py"),
    ("experiments.jsonl",    "A/B実験ログ（500件→levelup優先度計算）",      "agent_framework.py"),
]

# ─── KPIサマリー ──────────────────────────────────────────────────────────────
total_pl = counts.get("total", 0) or len(DAILY_PIPELINES) + len(CHAIN_PIPELINES) + len(WEEKLY_PIPELINES)
failed_pl = counts.get("failed", 0)
ok_pl = counts.get("ok", 0)
integrated_pl = counts.get("integrated", 0)

style.kpi_wrap_start("info")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("スケジューラータスク", f"{total_pl}本")
c2.metric("エージェント", f"{len(AGENTS)}個")
c3.metric("ダッシュボードページ", "8ページ")
c4.metric("パイプライン正常", f"{ok_pl}本", delta=None)
c5.metric("パイプライン失敗", f"{failed_pl}本",
          delta=f"-{failed_pl}" if failed_pl else None,
          delta_color="inverse" if failed_pl else "off")
c6.metric("統合スクリプト", f"{integrated_pl}本")
style.kpi_wrap_end()

# ─── タブ ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["⏱️ 実行タイムライン", "🤖 エージェント構成", "📁 ファイル・フォルダ構成"])

# ══════════════════════════════════════════════════════════════════════════════
# ⏱️ 実行タイムライン
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    col_daily, col_chain = st.columns([1, 1])

    with col_daily:
        style.section_card_start("📅 日次タスク（毎日 21:00〜）", "8タスク", "info")
        for i, (t, name, role) in enumerate(DAILY_PIPELINES):
            is_master = "DailyDriver" in name
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
        style.section_card_start("⚡ チェーンパイプライン（週2回）", "2チェーン", "ok")
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

    # DailyDriverの詳細
    style.section_card_start("⭐ DailyDriver — ステップ詳細（毎日 21:26）", "master", "ok")
    for no, name, desc in DAILY_DRIVER_STEPS:
        st.markdown(
            f'**Step {no}:** {name} — '
            f'<span style="color:#555;font-size:0.9em">{desc}</span>',
            unsafe_allow_html=True,
        )
    style.section_card_end()

# ══════════════════════════════════════════════════════════════════════════════
# 🤖 エージェント構成
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    style.section_card_start("🤖 エージェント一覧（agents_prompts.json）", f"{len(AGENTS)}エージェント", "info")

    # エージェント統計をFirebaseから取得
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

# ══════════════════════════════════════════════════════════════════════════════
# 📁 ファイル・フォルダ構成
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
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

    # コスト分析サマリー
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
