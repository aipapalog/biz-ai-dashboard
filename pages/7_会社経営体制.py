import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, style

st.set_page_config(page_title="🏗️ 会社経営体制", page_icon="🏗️", layout="wide")
st_autorefresh(interval=60_000, key="arch_refresh")
style.inject()
st.title("🏗️ 会社経営体制・アーキテクチャ")

pl_logs    = data_loader.pipeline_logs()
exec_t     = data_loader.execution_times()
agents_ctx = data_loader.agents_context()
exec_map   = {p["name"]: p for p in exec_t.get("pipelines", [])} if exec_t else {}

AGENTS_DEF = [
    {"name": "bizdev",            "department": "事業開発部",   "purpose": "ビジネスアイデア生成"},
    {"name": "marketing",         "department": "事業開発部",   "purpose": "マーケティング戦略"},
    {"name": "opensource_analyst","department": "事業開発部",   "purpose": "OSS収益化分析"},
    {"name": "copywriter",        "department": "コンテンツ部", "purpose": "コピーライティング改善"},
    {"name": "cx_expert",         "department": "コンテンツ部", "purpose": "CXリサーチ・製品評価（統合）"},
    {"name": "reviewer",          "department": "コンテンツ部", "purpose": "ビジネス/コンテンツ品質評価"},
    {"name": "risk_assessor",     "department": "品質管理部",   "purpose": "法的・セキュリティリスク評価"},
    {"name": "quality_gater",     "department": "経営管理部",   "purpose": "システム/パイプライン品質評価"},
    {"name": "biz_pdca_planner",  "department": "財務部",       "purpose": "PDCA施策立案"},
    {"name": "social_growth",     "department": "集客部",       "purpose": "SNS投稿評価・A/Bテスト"},
    {"name": "infra_ops",         "department": "IT部",         "purpose": "コアインフラ・自律ループ"},
    {"name": "dashboard_agent",   "department": "IT部",         "purpose": "ダッシュボード生成・監視"},
    {"name": "monitoring_agent",  "department": "IT部",         "purpose": "システム監視・ヘルスチェック"},
    {"name": "backup_agent",      "department": "IT部",         "purpose": "バックアップ・環境保全"},
    {"name": "content_pipeline",  "department": "コンテンツ部", "purpose": "Qiita/note・KDP生成"},
    {"name": "experiment",        "department": "IT部",         "purpose": "実験フレームワーク管理"},
]

PIPELINES_DEF = [
    {"name": "daily_bizdev",       "category": "収益生成", "schedule": "StrategyChain（月・木）",  "desc": "bizdev→marketing→reviewer 3段連鎖"},
    {"name": "product_monitor",    "category": "コンテンツ","schedule": "週次（水）",              "desc": "競合価格・レビュー監視／コピー改善"},
    {"name": "cx_improver",        "category": "コンテンツ","schedule": "ContentChain（火・金）",   "desc": "CXトレンド調査→全製品評価→即効改善案5件自動生成"},
    {"name": "pipeline_improver",  "category": "自己改善",  "schedule": "SystemLoop（水・土）",    "desc": "ログ解析・コード健全性・自動修正"},
    {"name": "risk_manager",       "category": "監視",      "schedule": "StrategyChain（月・木）", "desc": "法的・ToS・セキュリティの3カテゴリを評価"},
    {"name": "gdrive_backup",      "category": "インフラ",  "schedule": "毎日 21:21",              "desc": "Claude Code環境全体をGoogle Drive差分バックアップ"},
    {"name": "biz_pdca",           "category": "収益生成",  "schedule": "週次（月・木）",          "desc": "Check→Act→Planの3フェーズ週2回自動実行"},
    {"name": "autonomous_loop",    "category": "自己改善",  "schedule": "週次（日）",              "desc": "目標達成まで自動タスク探索→実装→完了→次タスクを繰り返す"},
    {"name": "product_researcher", "category": "市場調査",  "schedule": "StrategyChain（月・木）", "desc": "市場機会をToT3経路で並列分析・競合ベンチマーク実行"},
    {"name": "qiita_pipeline",     "category": "コンテンツ","schedule": "ContentChain（火・金）",  "desc": "Qiita記事生成・公開パイプライン"},
    {"name": "kdp_writer",         "category": "コンテンツ","schedule": "週次（木）",              "desc": "KDP電子書籍コンテンツ生成"},
    {"name": "freelance_researcher","category":"市場調査",   "schedule": "週次（火）",              "desc": "フリーランス案件を3経路で調査"},
    {"name": "social_growth",      "category": "集客",      "schedule": "週次（月）",              "desc": "SNS成長分析・投稿改善"},
    {"name": "x_post_qa_doctor",   "category": "コンテンツ","schedule": "平日 21:03 ⏸停止中",     "desc": "X自動投稿（APIキー取得待ち・停止中）"},
]

tab1, tab2, tab3 = st.tabs(["⚙️ パイプライン一覧", "👥 エージェント体制", "🗺️ アーキテクチャ図"])

# ── パイプライン一覧 ──────────────────────────────────────────────────────────
with tab1:
    categories = sorted(set(p["category"] for p in PIPELINES_DEF))
    selected_cat = st.selectbox("カテゴリで絞り込み", ["すべて"] + categories)
    filtered = PIPELINES_DEF if selected_cat == "すべて" else [p for p in PIPELINES_DEF if p["category"] == selected_cat]
    for p in filtered:
        logs_entry = pl_logs.get("logs", {}).get(p["name"], pl_logs.get(p["name"], {})) if pl_logs else {}
        run_status = logs_entry.get("status", "unknown") if isinstance(logs_entry, dict) else "unknown"
        last_run   = logs_entry.get("last_run", "未実行") if isinstance(logs_entry, dict) else "未実行"
        last_lines = logs_entry.get("last_lines", "") if isinstance(logs_entry, dict) else ""
        exec_info  = exec_map.get(p["name"], {})
        stopped    = "停止" in p["schedule"] or "⏸" in p["schedule"]
        icon = "⏸" if stopped else ("✅" if run_status == "success" else "❌" if run_status == "failed" else "⬜")
        with st.expander(f"{icon} **{p['name']}** — {p['category']} ／ {p['schedule']}"):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1: st.caption(p["desc"])
            with col2: st.write(f"**最終実行:** {last_run}")
            with col3:
                if exec_info:
                    st.write(f"**平均:** {exec_info.get('avg_seconds','-')} 秒")
                    st.write(f"**累計:** {exec_info.get('run_count',0)} 回")
            if last_lines: st.markdown("---"); st.code(last_lines[-300:], language=None)

# ── エージェント体制 ──────────────────────────────────────────────────────────
with tab2:
    departments = sorted(set(a["department"] for a in AGENTS_DEF))
    for dept in departments:
        agents = [a for a in AGENTS_DEF if a["department"] == dept]
        st.subheader(f"🏢 {dept}（{len(agents)} エージェント）")
        cols = st.columns(min(len(agents), 3))
        for i, agent in enumerate(agents):
            with cols[i % 3]:
                st.markdown(f"🟢 **{agent['name']}**  \n{agent['purpose']}")
        st.divider()
    if agents_ctx.get("content"):
        st.subheader("📋 エージェント コンテキスト")
        st.markdown(agents_ctx["content"])

# ── アーキテクチャ図 ──────────────────────────────────────────────────────────
with tab3:
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
        RM [label="RiskManager"]
        BP [label="BizPDCA"]
        PR -> BD -> RM
        BD -> BP
    }
    subgraph cluster_content {
        label="ContentChain（火・金）" style="dashed" color="#22c55e"
        node [fillcolor="#dcfce7"]
        CX [label="CXImprover"]
        QP [label="QiitaPipeline"]
        PM [label="ProductMonitor"]
        KW [label="KdpWriter"]
        CX -> QP
    }
    subgraph cluster_system {
        label="System（毎日/週次）" style="dashed" color="#a855f7"
        node [fillcolor="#fae8ff"]
        AL [label="AutonomousLoop"]
        PI [label="PipelineImprover"]
        AL -> PI
    }
    subgraph cluster_infra {
        label="Infrastructure（毎日）" style="dashed" color="#f97316"
        node [fillcolor="#ffedd5"]
        GB [label="GDriveBackup"]
        FP [label="FirebasePusher\\n(30min)"]
    }

    FB  [label="Firebase\\nFirestore" shape="cylinder" fillcolor="#fde68a"]
    ST  [label="Streamlit\\nDashboard" shape="diamond" fillcolor="#bae6fd"]
    LF  [label="Local Logs/JSON" shape="parallelogram" fillcolor="#f1f5f9"]

    LF -> FP [label="read"]
    FP -> FB [label="push" color="#f97316"]
    FB -> ST [label="read" color="#0ea5e9"]
}
"""
    st.graphviz_chart(dot)
