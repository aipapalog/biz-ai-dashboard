import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader

st.set_page_config(page_title="⏱️ スケジュール", page_icon="⏱️", layout="wide")
st_autorefresh(interval=120_000, key="schedule_refresh")
st.title("⏱️ パイプライン実行スケジュール")

scheduler  = data_loader.scheduler_tasks()
exec_times = data_loader.execution_times()
pl_logs    = data_loader.pipeline_logs()

# ── タスクスケジューラ実データ ────────────────────────────────────────────────
st.subheader("🖥️ タスクスケジューラ（実データ）")
if scheduler:
    import pandas as pd
    df = pd.DataFrame(scheduler)
    display_cols = [c for c in ["name", "schedule", "state", "last_run", "next_run", "status"] if c in df.columns]
    st.dataframe(df[display_cols] if display_cols else df, use_container_width=True)
else:
    st.info("スケジューラ情報がありません")
st.divider()

# ── 定義ベース スケジュール ───────────────────────────────────────────────────
st.subheader("📋 スケジュール定義（パイプライン別）")
SCHEDULE_DEF = [
    ("ProductResearcher",  "毎日 21:00",     "市場調査",   "StrategyChain先頭・市場機会ToT分析"),
    ("DailyLoopImprover",  "毎日 21:01",     "自己改善",   "Loopログ自動改善"),
    ("DefectPredictor",    "毎日 21:04",     "品質管理",   "欠陥予測ToT"),
    ("QaObserver",         "毎日 21:06",     "品質管理",   "QA観察ToT"),
    ("MabBizdev",          "毎日 21:10",     "収益生成",   "MABビジネスアイデア評価"),
    ("DailyBizDev",        "毎日 21:12",     "収益生成",   "bizdev→marketing→reviewer"),
    ("ProcessMonitor",     "毎日 21:15",     "監視",       "プロセス監視"),
    ("BlockerReviewer",    "毎日 21:18",     "管理",       "ブロッカーレビュー"),
    ("ErrorRecovery",      "毎日 21:16",     "インフラ",   "エラー自動回復"),
    ("DailyPriorityEngine","毎日 21:20",     "管理",       "優先度エンジン"),
    ("GDriveBackup",       "毎日 21:21",     "インフラ",   "Google Drive差分バックアップ"),
    ("DailyQiitaPipeline", "毎日 21:22",     "コンテンツ", "Qiita記事パイプライン"),
    ("KdpWriter",          "週次（木）21:05", "コンテンツ", "KDP電子書籍生成"),
    ("FreelanceResearcher","週次（火）21:07", "市場調査",   "フリーランス案件調査"),
    ("AutonomousLoop",     "週次（日）21:23", "自己改善",   "自律タスク探索・実行ループ"),
    ("AgentSupervisor",    "週次（日）21:23", "管理",       "エージェント監督"),
    ("MdOptimizer",        "週次（日）21:27", "管理",       "MDファイル最適化"),
    ("PipelineImprover",   "週次（日）21:29", "自己改善",   "パイプライン改善"),
    ("RevenueTracker",     "週次（月）21:23", "収益生成",   "収益追跡"),
    ("BizPDCA",            "週次（月・木）21:25","収益生成", "PDCA実行"),
]
import pandas as pd
df_def = pd.DataFrame(SCHEDULE_DEF, columns=["タスク名", "実行時刻", "カテゴリ", "説明"])
st.dataframe(df_def, use_container_width=True)
st.divider()

# ── 実行統計 ──────────────────────────────────────────────────────────────────
st.subheader("⏱️ パイプライン実行統計")
if exec_times:
    pipelines = exec_times.get("pipelines", [])
    total_runs = exec_times.get("total_runs", 0)
    st.caption(f"累計実行: {total_runs:,} 回")
    if pipelines:
        df_exec = pd.DataFrame(pipelines)
        display = [c for c in ["name","avg_seconds","run_count","last_run","last_status"] if c in df_exec.columns]
        st.dataframe(df_exec[display] if display else df_exec, use_container_width=True)
else:
    st.info("実行統計データがありません")
