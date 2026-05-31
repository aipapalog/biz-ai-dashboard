import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, firebase_client

st.set_page_config(page_title="パイプライン体制", page_icon="⚙️", layout="wide")
st_autorefresh(interval=60_000, key="pipeline_refresh")
st.title("⚙️ パイプライン・エージェント体制")

# ── 定義（dashboard_sections.py から同期）────────────────────────────────────
# Firebase /dashboard/definitions があればそちらを優先
defs = firebase_client.get("/dashboard/definitions", {})

AGENTS_DEF = defs.get("agents") or [
    {"name": "bizdev", "department": "事業開発部", "purpose": "ビジネスアイデア生成", "active": True},
    {"name": "marketing", "department": "事業開発部", "purpose": "マーケティング戦略", "active": True},
    {"name": "opensource_analyst", "department": "事業開発部", "purpose": "OSS収益化分析", "active": True},
    {"name": "copywriter", "department": "コンテンツ部", "purpose": "コピーライティング改善", "active": True},
    {"name": "cx_expert", "department": "コンテンツ部", "purpose": "CXリサーチ→製品評価（統合）", "active": True},
    {"name": "reviewer", "department": "コンテンツ部", "purpose": "ビジネス/コンテンツ品質評価", "active": True},
    {"name": "risk_assessor", "department": "品質管理部", "purpose": "法的・セキュリティリスク評価", "active": True},
    {"name": "quality_gater", "department": "経営管理部", "purpose": "システム/パイプライン品質評価", "active": True},
    {"name": "biz_pdca_planner", "department": "財務部", "purpose": "PDCA施策立案", "active": True},
    {"name": "social_growth", "department": "集客部", "purpose": "SNS投稿評価・A/Bテスト", "active": True},
    {"name": "infra_ops", "department": "IT部", "purpose": "コアインフラ・自律ループ", "active": True},
    {"name": "dashboard_agent", "department": "IT部", "purpose": "ダッシュボード生成・監視", "active": True},
    {"name": "monitoring_agent", "department": "IT部", "purpose": "システム監視・ヘルスチェック", "active": True},
    {"name": "backup_agent", "department": "IT部", "purpose": "バックアップ・環境保全", "active": True},
    {"name": "content_pipeline", "department": "コンテンツ部", "purpose": "Qiita/note・KDP生成", "active": True},
    {"name": "experiment", "department": "IT部", "purpose": "実験フレームワーク管理", "active": True},
]

PIPELINES_DEF = defs.get("pipelines") or [
    {"name": "daily_bizdev", "category": "収益生成", "schedule": "StrategyChain（月・木）", "type": "AI", "desc": "bizdev→marketing→reviewer 3段連鎖。ニッチ×即日可能な施策を自動生成・スコアリング"},
    {"name": "product_monitor", "category": "コンテンツ", "schedule": "週次（水）", "type": "AI", "desc": "競合価格・レビュー監視／コピー改善／noteベンチマーク"},
    {"name": "cx_improver", "category": "コンテンツ", "schedule": "ContentChain（火・金）", "type": "AI", "desc": "CXトレンド調査→全製品ローテーション評価→即効改善案5件自動生成"},
    {"name": "pipeline_improver", "category": "自己改善", "schedule": "SystemLoop（水・土）", "type": "AI", "desc": "ログ解析・コード健全性・類似パイプライン検出・自動修正"},
    {"name": "risk_manager", "category": "監視", "schedule": "StrategyChain（月・木）", "type": "AI", "desc": "法的・ToS・セキュリティの3カテゴリを評価。High/Medium/Low分類"},
    {"name": "gdrive_backup", "category": "インフラ", "schedule": "毎日 21:21", "type": "システム", "desc": "Claude Code環境全体をGoogle Drive差分バックアップ"},
    {"name": "biz_pdca", "category": "収益生成", "schedule": "StrategyChain（月・木）", "type": "AI", "desc": "Check→Act→Planの3フェーズ週2回自動実行"},
    {"name": "autonomous_loop", "category": "自己改善", "schedule": "週次（日）", "type": "AI", "desc": "目標達成まで自動タスク探索→実装→完了→次タスクを繰り返す"},
    {"name": "product_researcher", "category": "市場調査", "schedule": "StrategyChain（月・木）", "type": "AI", "desc": "市場機会をToT3経路で並列分析・競合ベンチマーク実行"},
    {"name": "qiita_pipeline", "category": "コンテンツ", "schedule": "ContentChain（火・金）", "type": "AI", "desc": "Qiita記事生成・公開パイプライン"},
    {"name": "kdp_writer", "category": "コンテンツ", "schedule": "週次（木）", "type": "AI", "desc": "KDP電子書籍コンテンツ生成"},
    {"name": "x_post_qa_doctor", "category": "コンテンツ", "schedule": "平日 21:03 ⏸停止中", "type": "Playwright", "desc": "X自動投稿（APIキー取得待ち・停止中）"},
    {"name": "name_consistency_check", "category": "自己改善", "schedule": "週次（日）", "type": "ルール", "desc": "変数名・ファイル名の命名一貫性を週次チェック"},
    {"name": "freelance_researcher", "category": "市場調査", "schedule": "週次（火）", "type": "AI", "desc": "フリーランス案件を3経路で調査・自動化率Top5を報告"},
    {"name": "biz_pdca", "category": "収益生成", "schedule": "週次（月・木）", "type": "AI", "desc": "PDCA週2回実行"},
    {"name": "social_growth", "category": "集客", "schedule": "週次（月）", "type": "AI", "desc": "SNS成長分析・投稿改善"},
]

pl_logs = data_loader.pipeline_logs()

# ── パイプライン実行状況 ──────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["パイプライン一覧", "エージェント体制"])

with tab1:
    # カテゴリ別にグループ化
    categories = sorted(set(p["category"] for p in PIPELINES_DEF))
    selected_cat = st.selectbox("カテゴリで絞り込み", ["すべて"] + categories)

    filtered = PIPELINES_DEF if selected_cat == "すべて" else [
        p for p in PIPELINES_DEF if p["category"] == selected_cat
    ]

    for p in filtered:
        log = pl_logs.get(p["name"], {})
        run_status = log.get("status", "unknown")
        status_icon = "✅" if run_status == "success" else ("❌" if run_status == "failed" else "⏸" if "停止" in p["schedule"] else "⬜")
        last_run = log.get("last_run", "未実行")

        with st.expander(f"{status_icon} **{p['name']}** — {p['category']} ／ {p['schedule']}"):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.caption(p["desc"])
                st.write(f"**種別:** {p['type']}")
            with col2:
                st.write(f"**最終実行:** {last_run}")
                if run_status != "unknown":
                    st.write(f"**結果:** {run_status}")

with tab2:
    departments = sorted(set(a["department"] for a in AGENTS_DEF))
    for dept in departments:
        agents = [a for a in AGENTS_DEF if a["department"] == dept]
        st.subheader(f"🏢 {dept}")
        cols = st.columns(min(len(agents), 3))
        for i, agent in enumerate(agents):
            with cols[i % 3]:
                active = "🟢" if agent.get("active") else "🔴"
                st.markdown(f"{active} **{agent['name']}**  \n{agent['purpose']}")
        st.divider()
