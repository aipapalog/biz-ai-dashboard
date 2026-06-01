import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, style
from datetime import datetime, date, timedelta

st.set_page_config(page_title="⏱️ スケジュール", page_icon="⏱️", layout="wide")
style.inject()
st.title("⏱️ パイプライン実行スケジュール")

scheduler  = data_loader.scheduler_tasks()
exec_times = data_loader.execution_times()
pl_logs    = data_loader.pipeline_logs()


def _parse_next(val):
    """next_run 文字列を date に変換（失敗時 None）。"""
    if not val:
        return None
    s = str(val).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s[:len(fmt) + 2] if "%H" in fmt else s[:10], fmt).date()
        except Exception:
            continue
    return None


# ── 今日 / 明日 / 今週（next_run ベース）─────────────────────────────────────
st.subheader("📅 直近の実行予定")
today = date.today()
tomorrow = today + timedelta(days=1)
week_end = today + timedelta(days=7)
buckets = {"🔹 今日": [], "🔹 明日": [], "🔹 今週": []}
for t in (scheduler or []):
    if not isinstance(t, dict):
        continue
    d = _parse_next(t.get("next_run"))
    if d is None:
        continue
    label = f"{t.get('name','?')}  🕐 {str(t.get('next_run',''))[:16]}"
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
st.divider()

# ── タスクスケジューラ実データ ────────────────────────────────────────────────
st.subheader("🖥️ タスクスケジューラ（実データ）")
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
