import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, style

st.set_page_config(page_title="🏗️ 会社経営体制", page_icon="🏗️", layout="wide")
style.inject()
st.title("🏗️ 会社経営体制・アーキテクチャ")

pl_logs     = data_loader.pipeline_logs() or {}
exec_t      = data_loader.execution_times() or {}
agents_ctx  = data_loader.agents_context() or {}
token_usage = data_loader.pipeline_token_usage() or {}
exec_map    = {p["name"]: p for p in exec_t.get("pipelines", [])}

# ── エージェント定義（使用パイプライン含む）────────────────────────────────────
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

PIPELINES_DEF = [
    # 収益生成
    {"name": "strategy_chain",      "cat": "収益生成",  "schedule": "月・木 21:07",                "agents": "biz_pdca_planner, marketing",    "desc": "KG抽出→product_researcher→daily_bizdev→bizdev_optimizer→leading_indicators→risk_manager→biz_pdcaをLangGraphで実行"},
    {"name": "biz_pdca",            "cat": "収益生成",  "schedule": "StrategyChain（月・木）",      "agents": "biz_pdca_planner",              "desc": "Check→Act→Planの3フェーズ週2回自動実行。施策TOP3をAI生成してtask_queueに追加"},
    {"name": "daily_bizdev",        "cat": "収益生成",  "schedule": "StrategyChain（月・木）",      "agents": "bizdev marketing reviewer",     "desc": "bizdev→marketing→reviewerの3エージェント連鎖。7点以上を『推奨』として翌日の行動候補に昇格"},
    {"name": "daily_opensource",    "cat": "収益生成",  "schedule": "週次（月）21:05",              "agents": "opensource_analyst",            "desc": "GitHubトレンド・Hacker News・Product Huntから週次収集。OSSの収益化パターンを分析"},
    {"name": "freelance_researcher","cat": "収益生成",  "schedule": "ContentChain（火・金）",       "agents": "biz_pdca_planner",              "desc": "【ToT：3経路】クラウドワークス・ランサーズ・Coconalaのフリーランス案件を3視点で並列調査"},
    {"name": "gumroad_publisher",   "cat": "収益生成",  "schedule": "ContentChain（火・金）",       "agents": "cx_expert content_pipeline",    "desc": "CXスコアが低い製品を優先評価→改善英語コピー生成→Gumroad製品ページに適用"},
    # コンテンツ
    {"name": "content_chain",       "cat": "コンテンツ","schedule": "火・金 21:03",                 "agents": "content_pipeline social_growth","desc": "metrics→content_strategist→content_writer→cx_improver→qiita/note/zenn/kdp/gumroad publisherを逐次実行"},
    {"name": "content_strategist",  "cat": "コンテンツ","schedule": "ContentChain（火・金）",       "agents": "content_pipeline",              "desc": "unified_metrics+brand_memory+now.mdを統合分析し3プラットフォームのコンテンツ戦略プランを立案"},
    {"name": "content_writer",      "cat": "コンテンツ","schedule": "ContentChain（火・金）",       "agents": "content_pipeline",              "desc": "content_plan.jsonに基づきqiita/note/kdp/gumroad向けコンテンツを一括生成"},
    {"name": "cx_improver",         "cat": "コンテンツ","schedule": "ContentChain（火・金）",       "agents": "cx_expert",                     "desc": "CXトレンド調査→全製品評価→即効改善案最大5件自動生成"},
    {"name": "cx_publisher_base",   "cat": "コンテンツ","schedule": "各publisherから呼び出し",      "agents": "cx_expert",                     "desc": "全販売ページ改善の標準ループ。CX評価→改善英語コピー生成→キャッシュ管理"},
    {"name": "kdp_writer",          "cat": "コンテンツ","schedule": "週次（木）22:36",              "agents": "content_pipeline",              "desc": "【廃止→content_writerに統合済み】KDP電子書籍コンテンツ生成"},
    {"name": "metrics_collector",   "cat": "コンテンツ","schedule": "ContentChain（火・金）",       "agents": "content_pipeline",              "desc": "note/Qiita/KDP売上を一元収集しunified_metrics.jsonに保存。旧note_analyticsを統合"},
    {"name": "note_analytics",      "cat": "コンテンツ","schedule": "ContentChain（火・金）",       "agents": "content_pipeline",              "desc": "【廃止→metrics_collectorに統合済み】"},
    {"name": "note_publisher",      "cat": "コンテンツ","schedule": "ContentChain（火・金）",       "agents": "cx_expert content_pipeline",    "desc": "content_drafts.jsonの最新noteドラフトを投稿するthin adapter"},
    {"name": "product_monitor",     "cat": "コンテンツ","schedule": "週次（水）23:03",              "agents": "marketing copywriter",          "desc": "競合価格・レビュー監視／タイトル・説明文コピー改善をweekly統合実行"},
    {"name": "qiita_pipeline",      "cat": "コンテンツ","schedule": "ContentChain（火・金）",       "agents": "content_pipeline",              "desc": "【廃止→content_writer/qiita_publisherに分割済み】"},
    {"name": "qiita_publisher",     "cat": "コンテンツ","schedule": "ContentChain（火・金）",       "agents": "content_pipeline",              "desc": "content_drafts.jsonの最新QiitaドラフトをPlaywright経由でQiitaに投稿"},
    {"name": "x_post_qa_doctor",    "cat": "コンテンツ","schedule": "平日 21:03 ⏸停止中",          "agents": "social_growth",                 "desc": "【停止中・スクリプト未作成】X自動投稿。X APIキー取得後に実装予定"},
    {"name": "zenn_publisher",      "cat": "コンテンツ","schedule": "ContentChain（火・金）",       "agents": "content_pipeline",              "desc": "experience_log.mdの実体験を素材にZenn技術記事を生成・保存"},
    # 自己改善
    {"name": "autonomous_loop",     "cat": "自己改善",  "schedule": "週次（日）22:48",              "agents": "infra_ops",                     "desc": "目標達成まで自動タスク探索→実装→完了→次タスクを繰り返す"},
    {"name": "bizdev_optimizer",    "cat": "自己改善",  "schedule": "StrategyChain / ContentChain", "agents": "quality_gater marketing",       "desc": "bizdev_report→パターン抽出→MABスコア更新→mab_recommendation.json生成"},
    {"name": "mempalace_maintenance","cat":"自己改善",   "schedule": "毎日 21:20",                  "agents": "quality_gater",                 "desc": "5フェーズ構成。Kanban/会話記録/CLI履歴収集→claude -pで判断→mempalace記録→agent_levelup実行"},
    {"name": "monthly_optimizer",   "cat": "自己改善",  "schedule": "月次 15日 21:29",              "agents": "quality_gater",                 "desc": "skills_optimizer+token_optimizer統合版。スキル使用状況・トークン消費量を収集後に統合改善提案を生成"},
    {"name": "name_consistency_check","cat":"自己改善",  "schedule": "週次（日）21:24",              "agents": "quality_gater",                 "desc": "変数名・ファイル名・エージェント名・タスク名の命名一貫性を週次チェック"},
    {"name": "pipeline_improver",   "cat": "自己改善",  "schedule": "SystemLoop（水・土）",         "agents": "quality_gater",                 "desc": "ログ解析・コード健全性・類似パイプライン検出・自動修正・Claude改善提案を週次実行"},
    {"name": "realtime_kg_feed",    "cat": "自己改善",  "schedule": "タスク完了時",                 "agents": "infra_ops",                     "desc": "autonomous_loopのタスク実行完了/失敗直後に呼ばれるKGフィード。失敗パターンをmempalace KGにリアルタイム記録"},
    {"name": "self_audit_engine",   "cat": "自己改善",  "schedule": "毎日 21:11",                  "agents": "quality_gater",                 "desc": "経営コンサルタント視点で自問自答を5問生成。課題があればKanbanタスクに自動投入"},
    {"name": "system_evaluator",    "cat": "自己改善",  "schedule": "SystemLoop（水・土）",         "agents": "quality_gater monitoring_agent","desc": "AIシステム評価。環境監査・ポートフォリオ評価・パフォーマンス分析・改善提案を統合実行"},
    {"name": "system_loop",         "cat": "自己改善",  "schedule": "水・土 21:06",                 "agents": "monitoring_agent quality_gater","desc": "KG抽出→system_health→pipeline_improver→system_evaluatorを逐次実行"},
    # 監視
    {"name": "dashboard_issue_resolver","cat":"監視",   "schedule": "generate_dashboard.py実行時",  "agents": "infra_ops",                     "desc": "ダッシュボードの全異常を自律検知・自動修正またはKanban投入"},
    {"name": "leading_indicators",  "cat": "監視",      "schedule": "StrategyChain（月・木）",      "agents": "biz_pdca_planner",              "desc": "収益以外の先行指標（タスク完了数・施策実施率等）を日次集計"},
    {"name": "risk_manager",        "cat": "監視",      "schedule": "StrategyChain（月・木）",      "agents": "risk_assessor",                 "desc": "法的・プラットフォームToS・セキュリティの3カテゴリを週次評価"},
    {"name": "system_health",       "cat": "監視",      "schedule": "SystemLoop（水・土）",         "agents": "monitoring_agent infra_ops",    "desc": "統合インフラ監視。ログERROR監視・パイプライン鮮度・リソース監視・スケジューラ整合性チェック"},
    {"name": "user_acquisition_funnel","cat":"監視",    "schedule": "毎日 21:08",                  "agents": "monitoring_agent",              "desc": "note→製品ページ→購入のファネルメトリクスを日次更新。ドロップオフ分析・プラットフォーム別導線追跡"},
    # インフラ
    {"name": "doc_sync",            "cat": "インフラ",  "schedule": "週次（日）21:27",              "agents": "backup_agent reviewer",         "desc": "MD監査（陳腐化検出）/ memory→mempalace KG差分同期 / Obsidian→mempalace KG同期"},
    {"name": "gdrive_backup",       "cat": "インフラ",  "schedule": "毎日 21:21",                  "agents": "backup_agent",                  "desc": "Claude Code環境全体をGoogle Drive差分バックアップ。PC故障・環境移行時の完全復元を想定"},
    # 意思決定
    {"name": "consultation_manager","cat": "意思決定",  "schedule": "📞 セッションから呼び出し",   "agents": "cx_expert content_pipeline",    "desc": "複数の専門エージェントに質問を投げ、推奨・リスク・次のアクションを集約して意思決定を支援"},
    # 市場調査
    {"name": "product_researcher",  "cat": "市場調査",  "schedule": "StrategyChain（月・木）",      "agents": "marketing",                     "desc": "市場機会をToT3経路で並列分析し、QAドクター製品の競合ベンチマークを実行"},
]

SKILLS_DEF = [
    {"cmd": "/draft-message",  "dept": "会社業務",  "desc": "困ったメール・Teamsを状況説明だけで下書き（催促・依頼・謝罪・報告対応）",              "status": "未使用"},
    {"cmd": "/make-pptx",      "dept": "会社業務",  "desc": "箇条書きや表をそのままPowerPointスライドに変換する（報告・提案・ハンドオーバー対応）", "status": "未使用"},
    {"cmd": "/office-to-md",   "dept": "会社業務",  "desc": "OfficeファイルをMarkdownに変換してClaudeに読ませる（PPTX/DOCX/XLSX対応）",           "status": "未使用"},
    {"cmd": "/note-draft",     "dept": "コンテンツ","desc": "note記事の構成・見出し・本文下書きをターゲット読者に合わせてCTA付きで作成する",         "status": "未使用"},
    {"cmd": "/eval-idea",      "dept": "ビジネス",  "desc": "ビジネスアイデアをDevil's Advocate思考＋3軸スコアで評価し、致命的な穴と改善策を指摘する","status": "✓ 使用中"},
    {"cmd": "/agent-status",   "dept": "システム",  "desc": "Claudeのバックグラウンドプロセスとエージェントログをリアルタイムで表示する",            "status": "未使用"},
]

# ── 体制図・システム概要（冒頭） ───────────────────────────────────────────────
col_left, col_right = st.columns([1, 1])
with col_left:
    st.subheader("📊 体制図")
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
    st.subheader("🤖 社長 AI Chief Executive Officer")
    st.info("""
実績ある自律型AIエグゼクティブ。アイデア創出から収益化まで短期完結が得意。
指示待ちゼロ、常に先手を打つ経営スタイル。

⚡ 自律実行　💡 アイデア量産　🎯 顧客ニーズ発見　🚀 短期収益化　🤖 AI活用エキスパート
""")

st.divider()

# ── システム構造概要 ───────────────────────────────────────────────────────────
n_pl = len(PIPELINES_DEF)
n_ag = len(AGENTS_DEF)
st.subheader("🏗️ システム構造概要")
s1, s2, s3 = st.columns(3)
s1.metric("⚙️ パイプライン", f"{n_pl} 本")
s2.metric("🤖 エージェント", f"{n_ag} 種")
s3.metric("🔗 チェーン数", "3 本（戦略・コンテンツ・システム）")
st.caption(f"AIパイプライン {n_pl} 本 が {n_ag} 種のエージェントを共有利用。"
           "1つのパイプラインが複数エージェントを連鎖（例: daily_bizdev → bizdev→marketing→reviewer）")

st.divider()

# ── タブ ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⚙️ パイプライン一覧",
    "👥 エージェント一覧",
    "🎯 スキル一覧",
    "🔗 チェーン設計",
    "🗺️ アーキテクチャ図",
])

# ── パイプライン一覧（39本）──────────────────────────────────────────────────
with tab1:
    categories = sorted(set(p["cat"] for p in PIPELINES_DEF))
    selected_cat = st.selectbox("カテゴリで絞り込み", ["すべて"] + categories)
    filtered = PIPELINES_DEF if selected_cat == "すべて" else [p for p in PIPELINES_DEF if p["cat"] == selected_cat]
    st.caption(f"表示: {len(filtered)} 本 / 全 {len(PIPELINES_DEF)} 本")

    for p in filtered:
        logs_raw = pl_logs.get("logs", pl_logs)
        logs_entry = logs_raw.get(p["name"], {}) if isinstance(logs_raw, dict) else {}
        if not isinstance(logs_entry, dict):
            logs_entry = {}
        status    = logs_entry.get("status", "unknown")
        last_run  = logs_entry.get("last_run", "—")
        last_lines= logs_entry.get("last_lines", "")
        tok_entry = token_usage.get(p["name"], {})
        tokens    = tok_entry.get("total", 0)
        cost      = tok_entry.get("cost_usd", 0)
        tok_ts    = (tok_entry.get("ts", "") or "")[:10]
        stopped   = "停止" in p["schedule"] or "⏸" in p["schedule"]
        廃止     = "廃止" in p["desc"] or "統合済み" in p["desc"]
        icon = "⏸" if stopped else ("🗑" if 廃止 else ("✅" if status == "success" else "❌" if status == "failed" else "⬜"))

        with st.expander(f"{icon} **{p['name']}** — {p['cat']} ／ {p['schedule']}"):
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            with c1:
                st.caption(p["desc"])
                st.write(f"**エージェント:** {p['agents']}")
            with c2:
                st.write(f"**最終実行:** {last_run}")
                st.write(f"**状態:** {status}")
            with c3:
                if tokens:
                    st.write(f"**トークン:** {tokens:,}")
                    st.caption(f"${cost:.4f}  {tok_ts}")
                else:
                    st.caption("トークン: —")
            with c4:
                ei = exec_map.get(p["name"], {})
                if ei:
                    st.write(f"**平均:** {ei.get('avg_seconds','-')} 秒")
                    st.write(f"**累計:** {ei.get('run_count',0)} 回")
            if last_lines:
                st.markdown("---")
                st.code(str(last_lines)[-300:], language=None)

# ── エージェント一覧（使用パイプライン付き）──────────────────────────────────
with tab2:
    departments = sorted(set(a["dept"] for a in AGENTS_DEF))
    for dept in departments:
        agents = [a for a in AGENTS_DEF if a["dept"] == dept]
        st.subheader(f"🏢 {dept}")
        rows = []
        for a in agents:
            rows.append({"エージェント名": a["name"], "役割": a["purpose"], "使用パイプライン": a["pipelines"]})
        import pandas as pd
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    if agents_ctx.get("content"):
        with st.expander("📋 エージェント コンテキスト詳細", expanded=False):
            st.markdown(agents_ctx["content"])

# ── スキル一覧（6種）────────────────────────────────────────────────────────
with tab3:
    st.subheader(f"🎯 スキル一覧（{len(SKILLS_DEF)} 種）")
    import pandas as pd
    df_sk = pd.DataFrame([
        {"コマンド": s["cmd"], "部門": s["dept"], "機能説明": s["desc"], "パイプライン活用": s["status"]}
        for s in SKILLS_DEF
    ])
    st.dataframe(df_sk, use_container_width=True, hide_index=True)

# ── チェーン設計 ──────────────────────────────────────────────────────────────
with tab4:
    st.subheader("🔵 戦略チェーン（月・木 21:07）")
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

    st.subheader("🟢 コンテンツチェーン（火・金 21:03）")
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

    st.subheader("🟣 システム改善ループ（水・土 21:06）")
    st.markdown("""
インフラ監視 → 改善案生成 → 評価 → eval_reportが次週のインフラ監視インプットに戻る（フィードバックループ）

| ステップ | スクリプト | 役割 | 出力ファイル |
|---|---|---|---|
| 🧠 KG抽出 | extract_chain_context.py | failures/learning/eval_reportから抽出 | chain_context.md |
| 🔍 インフラ監視 | system_health | ログERROR/リソース/スケジューラ整合性 | health_report.md |
| 🛠 改善案生成 | pipeline_improver | ログ解析・コード健全性・自動修正 | improvement.md |
| 📊 評価 | system_evaluator | 環境監査・パフォーマンス分析・改善提案 | eval_report.md |
| ↻ フィードバック | — | eval_report.md → system_health へ（次週） | — |
""")

    st.divider()
    st.subheader("🔗 チェーン間連携ルール")
    st.markdown("""
**送信（戦略 → コンテンツ）**
- ✅ `extract_chain_context.py` が `market_analysis_*.md` を要約 → `chain_context_content.md` に書き出し → コンテンツチェーンの各ノードへ注入
- ✅ `market_score < 4.0` の日: `route_after_research()` が BizDev 2本をスキップ、`route_before_publish()` が `note_publisher` をスキップ（低品質日のLLM節約）
- ✅ `experience_log.md`（体験談・Zenn/note記事素材）→ `chain_context_content.md` に注入 → 各コンテンツノードへ

**受信（コンテンツ ← 戦略）**
- ✅ `node_context` が `chain_context_content.md` を読み込み → ContentState に `market_score` / `market_summary` を格納 → 各エージェントへ渡す
""")

    st.divider()
    st.subheader("🛠 OSS移行進捗 — LangGraph + Prefect + OpenRouter")
    st.markdown("""
| フェーズ | 状態 | 解決した問題 |
|---|---|---|
| **フェーズ1: Prefect** | ✅ 完了 | チェーン途中で止まった場所の可視化（localhost:4200 で5分以内特定） |
| **フェーズ2: LangGraph** | ✅ 完了 | 低スコア日のLLMスキップ（トークン30〜40%削減）・StateGraph経由のデータ受け渡し |
| **フェーズ3: OpenRouter** | 🔍 検討中 | claude -p の従量課金（6/15〜）対策。6/15以降の実課金額を1ヶ月確認してから判断 |
""")
    st.info("Prefect可視化: `prefect server start` → ブラウザで `localhost:4200` → Flows → StrategyChain/ContentChain を選択")

# ── アーキテクチャ図 ──────────────────────────────────────────────────────────
with tab5:
    dot = """
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
        PB [label="Publishers\\n(qiita/note/kdp/gumroad)"]
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
        FP [label="FirebasePusher\\n(30min)"]
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
    st.graphviz_chart(dot)

    st.subheader("📁 フォルダ配置方針")
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
