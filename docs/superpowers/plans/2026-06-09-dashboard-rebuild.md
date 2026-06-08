# ダッシュボード再構築 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** StreamlitダッシュボードをグラスモーフィズムUI・4ページ構成に再構築し、Firestore反映不具合（古い値が残り続ける）を根絶する。

**Architecture:** firebase_pusher_v2.py が45ドキュメントを10統合ドキュメントにpushし、_push_logで鮮度を可視化。data_loader_v2.py が @st.cache_data(ttl=3600) でFirestoreを読み全関数がデフォルト値を返す。UIは既存style.pyにグラスモーフィズムCSSを追加した4ページ構成。レガシーHTML生成系3ファイルは最終フェーズで削除。

**Tech Stack:** Python 3.12, Streamlit, Firestore REST API (requests), pytest

**制約（厳守）:**
- スケジューラ追加禁止・pusherは21:55のみ
- `from subprocess_wrapper import safe_run` 必須（直接subprocess禁止）
- `User-Agent: Claude-Script/1.0` 必須
- `@st.cache_data` でPC負荷を最小化

---

## ファイルマップ

| 操作 | パス |
|------|------|
| CREATE | `scripts/agents/firebase_pusher_v2.py` |
| CREATE | `scripts/agents/tests/test_pusher_v2.py` |
| CREATE | `streamlit_dashboard/utils/data_loader_v2.py` |
| CREATE | `streamlit_dashboard/tests/test_data_loader_v2.py` |
| MODIFY | `streamlit_dashboard/utils/style.py` |
| MODIFY | `streamlit_dashboard/Home.py` |
| CREATE | `streamlit_dashboard/pages/1_タスク.py` |
| CREATE | `streamlit_dashboard/pages/2_ビジネス.py` |
| CREATE | `streamlit_dashboard/pages/3_AIシステム.py` |
| DELETE | `streamlit_dashboard/pages/0_システム概要.py` ～ `9_Eval品質.py` (9ファイル) |
| DELETE | `scripts/agents/generate_dashboard.py` |
| DELETE | `scripts/agents/generate_dashboard_safe.py` |
| DELETE | `scripts/agents/dashboard_sections.py` |

---

## Phase 1: バックエンド（pusher_v2 + data_loader_v2）

---

### Task 1: firebase_pusher_v2.py — 基盤・ユーティリティ

**Files:**
- Create: `scripts/agents/firebase_pusher_v2.py`
- Create: `scripts/agents/tests/test_pusher_v2.py`

- [ ] **Step 1: テストファイルを作成し、失敗することを確認**

```python
# scripts/agents/tests/test_pusher_v2.py
import sys, json
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_to_firestore_string():
    from firebase_pusher_v2 import to_firestore
    assert to_firestore("hello") == {"stringValue": "hello"}

def test_to_firestore_int():
    from firebase_pusher_v2 import to_firestore
    assert to_firestore(42) == {"integerValue": "42"}

def test_to_firestore_bool():
    from firebase_pusher_v2 import to_firestore
    assert to_firestore(True) == {"booleanValue": True}

def test_to_firestore_none():
    from firebase_pusher_v2 import to_firestore
    assert to_firestore(None) == {"nullValue": None}

def test_to_firestore_list_truncates_at_1000():
    from firebase_pusher_v2 import to_firestore
    result = to_firestore(list(range(1500)))
    assert len(result["arrayValue"]["values"]) == 1000

def test_load_json_missing_file_returns_default():
    from firebase_pusher_v2 import load_json
    assert load_json(Path("/nonexistent/file.json"), default={"x": 1}) == {"x": 1}

def test_push_doc_skips_empty_data():
    from firebase_pusher_v2 import push_doc
    with patch("firebase_pusher_v2.requests") as mock_req:
        result = push_doc("test_doc", {})
        mock_req.patch.assert_not_called()
        assert result is False
```

- [ ] **Step 2: testsディレクトリを作成してテストが失敗することを確認**

```bash
cd "C:\Users\0000112191\.claude\scripts\agents"
mkdir -p tests && touch tests/__init__.py
python -m pytest tests/test_pusher_v2.py -v 2>&1 | head -20
```
Expected: `ModuleNotFoundError: No module named 'firebase_pusher_v2'`

- [ ] **Step 3: firebase_pusher_v2.py の基盤を実装**

```python
# scripts/agents/firebase_pusher_v2.py
import os
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from subprocess_wrapper import safe_run

PROJECT_ID = "ai-agent-dashboard-5810b"
API_KEY = "AIzaSyAphCqxbM-fHenxUNFikW_AsVTNuPc_Ems"
FIRESTORE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"
HEADERS = {"User-Agent": "Claude-Script/1.0", "Content-Type": "application/json"}
AGENTS_DIR = Path(r"C:\Users\0000112191\.claude\scripts\agents")
DATA_DIR = Path(r"C:\Users\0000112191\.claude\data")

logging.basicConfig(
    filename=str(AGENTS_DIR.parent / "logs" / "pusher_v2.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8",
)


def load_json(path: Path, default=None):
    """ローカルJSONを安全に読む。失敗時はdefaultを返す。"""
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default if default is not None else {}


def to_firestore(obj) -> dict:
    """Python値 → Firestoreフィールド形式"""
    if isinstance(obj, bool):
        return {"booleanValue": obj}
    if isinstance(obj, int):
        return {"integerValue": str(obj)}
    if isinstance(obj, float):
        return {"doubleValue": obj}
    if isinstance(obj, str):
        return {"stringValue": obj}
    if obj is None:
        return {"nullValue": None}
    if isinstance(obj, list):
        return {"arrayValue": {"values": [to_firestore(v) for v in obj[:1000]]}}
    if isinstance(obj, dict):
        items = list(obj.items())[:100]
        return {"mapValue": {"fields": {k: to_firestore(v) for k, v in items}}}
    return {"stringValue": str(obj)}


def push_doc(doc_id: str, data: dict) -> bool:
    """dashboard/{doc_id} にPATCH。空データはスキップしてFalseを返す。"""
    if not data:
        return False
    fields = {k: to_firestore(v) for k, v in data.items()}
    url = f"{FIRESTORE_URL}/dashboard/{doc_id}?key={API_KEY}"
    r = requests.patch(url, json={"fields": fields}, headers=HEADERS, timeout=30)
    ok = r.status_code == 200
    if not ok:
        logging.error(f"push_doc failed: {doc_id} status={r.status_code}")
    return ok


def push_to_collection(collection: str, doc_id: str, data: dict) -> bool:
    """任意コレクションにPATCH。commands書き戻し等に使用。"""
    if not data:
        return False
    fields = {k: to_firestore(v) for k, v in data.items()}
    url = f"{FIRESTORE_URL}/{collection}/{doc_id}?key={API_KEY}"
    r = requests.patch(url, json={"fields": fields}, headers=HEADERS, timeout=30)
    return r.status_code == 200
```

- [ ] **Step 4: テストを実行して通過を確認**

```bash
cd "C:\Users\0000112191\.claude\scripts\agents"
python -m pytest tests/test_pusher_v2.py -v
```
Expected: 7 passed

- [ ] **Step 5: コミット**

**注意:** pusher は `claude-scripts` リポジトリ（git root: `C:\Users\0000112191\.claude\`）に属する。

```bash
cd "C:\Users\0000112191\.claude"
git add scripts/agents/firebase_pusher_v2.py scripts/agents/tests/test_pusher_v2.py scripts/agents/tests/__init__.py
git commit -m "feat: firebase_pusher_v2 基盤・ユーティリティ追加"
```

---

### Task 2: firebase_pusher_v2.py — collect関数群（10統合ドキュメント）

**Files:**
- Modify: `scripts/agents/firebase_pusher_v2.py`
- Modify: `scripts/agents/tests/test_pusher_v2.py`

**注意:** 既存の `firebase_dashboard_pusher.py` の collect_* 関数群を参照して、同じローカルJSONパスを使う。collect関数の**データ収集ロジックは変えない**、統合先の構造だけ変える。

- [ ] **Step 1: テストを先に追加（collect関数のデフォルト値テスト）**

既存テストファイルの末尾に追加:

```python
def test_collect_system_health_returns_dict_when_files_missing():
    from firebase_pusher_v2 import collect_system_health
    result = collect_system_health()
    assert isinstance(result, dict)
    assert "flows" in result
    assert "alerts" in result

def test_collect_tasks_returns_dict_when_files_missing():
    from firebase_pusher_v2 import collect_tasks
    result = collect_tasks()
    assert isinstance(result, dict)

def test_collect_finance_returns_dict_when_files_missing():
    from firebase_pusher_v2 import collect_finance
    result = collect_finance()
    assert isinstance(result, dict)
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
python -m pytest tests/test_pusher_v2.py::test_collect_system_health_returns_dict_when_files_missing -v
```
Expected: FAIL（関数未定義）

- [ ] **Step 3: 10個のcollect関数を firebase_pusher_v2.py に追加**

```python
# === collect関数群 ===
# 既存 firebase_dashboard_pusher.py の個別collect_*を統合する

def collect_system_health() -> dict:
    """パイプライン稼働・スケジューラ・フロー状態・アラートをまとめる"""
    flow_status = load_json(DATA_DIR / "flow_status.json", default={})
    scheduler_raw = {}
    try:
        r = safe_run(["schtasks", "/query", "/fo", "CSV", "/nh"],
                     capture_output=True, text=True, timeout=15)
        # CSV行をパース: タスク名, 次回実行, ステータス
        lines = [l for l in r.stdout.splitlines() if l.strip()]
        scheduler_raw = {"entries": lines[:50]}
    except Exception:
        pass

    flows = flow_status.get("flows", {})
    alerts = []
    for name, info in flows.items():
        if isinstance(info, dict) and info.get("status") not in ("ok", "running", None):
            alerts.append(f"{name}: {info.get('status', 'unknown')}")

    return {
        "flows": flows,
        "last_run": flow_status.get("last_updated", ""),
        "alerts": alerts,
        "scheduler": scheduler_raw,
        "pipeline_count": len(flows),
    }


def collect_tasks() -> dict:
    """Kanban要約とアクティブタスクをまとめる"""
    kanban = load_json(DATA_DIR / "kanban_summary.json", default={})
    active = load_json(DATA_DIR / "kanban_active.json", default={})
    return {
        "summary": kanban,
        "active": active,
        "total": kanban.get("total", 0),
        "in_progress": kanban.get("in_progress", 0),
        "high_priority": kanban.get("high_priority", []),
    }


def collect_business() -> dict:
    """事業状況・プラットフォーム監視・フリーランスをまとめる"""
    biz = load_json(AGENTS_DIR / "data" / "business_status.json", default={})
    pf = load_json(AGENTS_DIR / "data" / "pf_watch.json", default={})
    fl = load_json(AGENTS_DIR / "data" / "freelance_report.json", default={})
    return {"business_status": biz, "pf_watch": pf, "freelance": fl}


def collect_bizdev() -> dict:
    """BizDevレポートとトレンドをまとめる"""
    report = load_json(AGENTS_DIR / "data" / "bizdev_report.json", default={})
    trend = load_json(AGENTS_DIR / "data" / "bizdev_trend.json", default={})
    return {"report": report, "trend": trend}


def collect_cx_quality() -> dict:
    """CX品質・LevelUpをまとめる"""
    cx = load_json(AGENTS_DIR / "data" / "cx_report.json", default={})
    levelup = load_json(AGENTS_DIR / "data" / "levelup_status.json", default={})
    history = load_json(AGENTS_DIR / "data" / "levelup_history.json", default=[])
    return {"cx_report": cx, "levelup_status": levelup, "levelup_history": history}


def collect_ai_ops() -> dict:
    """自律ループ・エージェント稼働をまとめる"""
    loop = load_json(AGENTS_DIR / "data" / "autonomous_loop.json", default={})
    stats = load_json(AGENTS_DIR / "data" / "agent_run_stats.json", default={})
    insights = load_json(AGENTS_DIR / "data" / "agent_insights.json", default={})
    return {"autonomous_loop": loop, "agent_run_stats": stats, "agent_insights": insights}


def collect_finance() -> dict:
    """API予算・コストをまとめる"""
    budget = load_json(AGENTS_DIR / "data" / "api_budget.json", default={})
    cost = load_json(AGENTS_DIR / "data" / "pipeline_cost_report.json", default={})
    tokens = load_json(AGENTS_DIR / "data" / "pipeline_token_usage.json", default={})
    return {"api_budget": budget, "cost_report": cost, "token_usage": tokens}


def collect_content() -> dict:
    """Mempalace・obsidian・brain同期をまとめる"""
    mp = load_json(AGENTS_DIR / "data" / "mempalace.json", default={})
    mp_rooms = load_json(AGENTS_DIR / "data" / "mempalace_rooms.json", default={})
    obs = load_json(AGENTS_DIR / "data" / "obsidian_stats.json", default={})
    brain = load_json(AGENTS_DIR / "data" / "sync_brain.json", default={})
    tasks = load_json(AGENTS_DIR / "data" / "sync_tasks.json", default={})
    return {
        "mempalace": mp,
        "mempalace_rooms": mp_rooms,
        "obsidian": obs,
        "sync_brain": brain,
        "sync_tasks": tasks,
    }


def collect_meta() -> dict:
    """リスク・障害パターン・eval・pdcaをまとめる"""
    risk = load_json(AGENTS_DIR / "data" / "risk_report.json", default={})
    failure = load_json(AGENTS_DIR / "data" / "failure_patterns.json", default={})
    code = load_json(AGENTS_DIR / "data" / "code_health.json", default={})
    eval_s = load_json(AGENTS_DIR / "data" / "eval_status.json", default={})
    pdca = load_json(AGENTS_DIR / "data" / "pdca.json", default={})
    biz_pdca = load_json(AGENTS_DIR / "data" / "biz_pdca_reports.json", default={})
    return {
        "risk_report": risk,
        "failure_patterns": failure,
        "code_health": code,
        "eval_status": eval_s,
        "pdca": pdca,
        "biz_pdca": biz_pdca,
        "last_updated": datetime.now().isoformat(),
    }
```

- [ ] **Step 4: テストを実行して通過を確認**

```bash
python -m pytest tests/test_pusher_v2.py -v
```
Expected: 10 passed

- [ ] **Step 5: コミット**

```bash
cd "C:\Users\0000112191\.claude"
git add scripts/agents/firebase_pusher_v2.py scripts/agents/tests/test_pusher_v2.py
git commit -m "feat: pusher_v2 collect関数群 (10統合ドキュメント)"
```

---

### Task 3: firebase_pusher_v2.py — main() + _push_log + execute_pending_commands

**Files:**
- Modify: `scripts/agents/firebase_pusher_v2.py`
- Modify: `scripts/agents/tests/test_pusher_v2.py`

- [ ] **Step 1: テストを追加**

```python
def test_push_all_writes_push_log():
    from firebase_pusher_v2 import push_all
    with patch("firebase_pusher_v2.requests") as mock_req:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_req.patch.return_value = mock_resp
        mock_req.get.return_value = MagicMock(status_code=200, json=lambda: {"documents": []})
        log = push_all()
    assert "timestamp" in log
    assert "success_count" in log
    assert "fail_count" in log
    assert isinstance(log["errors"], dict)

def test_push_all_continues_on_failure():
    from firebase_pusher_v2 import push_all
    call_count = 0
    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        mock = MagicMock()
        # 最初の呼び出しは失敗、残りは成功
        mock.status_code = 500 if call_count == 1 else 200
        return mock
    with patch("firebase_pusher_v2.requests") as mock_req:
        mock_req.patch.side_effect = side_effect
        mock_req.get.return_value = MagicMock(status_code=200, json=lambda: {"documents": []})
        log = push_all()
    # fail_countが1以上でも処理が完了している
    assert "timestamp" in log
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
python -m pytest tests/test_pusher_v2.py::test_push_all_writes_push_log -v
```
Expected: FAIL

- [ ] **Step 3: execute_pending_commands() と push_all() と main() を実装**

```python
# execute_pending_commands: 既存 firebase_dashboard_pusher.py からそのまま移植
def execute_pending_commands():
    """Firestoreのcommandsコレクションのpendingコマンドを取得・実行・完了更新"""
    try:
        url = f"{FIRESTORE_URL}/commands?key={API_KEY}"
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code != 200:
            return
        docs = r.json().get("documents", [])
        for doc in docs:
            raw = doc.get("fields", {})
            fields = {k: list(v.values())[0] if v else None for k, v in raw.items()}
            if fields.get("status") != "pending":
                continue
            task_name = str(fields.get("task_name", ""))
            if not task_name:
                continue
            result = safe_run(["schtasks", "/run", "/tn", task_name],
                              capture_output=True, text=True, timeout=20)
            new_status = "done" if result.returncode == 0 else "failed"
            print(f"  ▶ command [{task_name}] → {new_status}")
            doc_name = doc.get("name", "").split("/")[-1]
            push_to_collection("commands", doc_name, {
                **fields,
                "status": new_status,
                "executed_at": datetime.now().isoformat(),
            })
    except Exception as e:
        logging.error(f"execute_pending_commands error: {e}")
        print(f"  execute_pending_commands error: {e}")


# 10ドキュメントとcollect関数のマッピング
COLLECTORS = {
    "system_health": collect_system_health,
    "tasks":         collect_tasks,
    "business":      collect_business,
    "bizdev":        collect_bizdev,
    "cx_quality":    collect_cx_quality,
    "ai_ops":        collect_ai_ops,
    "finance":       collect_finance,
    "content":       collect_content,
    "meta":          collect_meta,
}


def push_all() -> dict:
    """全ドキュメントをpushし、_push_logを書き込んで結果dictを返す"""
    results = {}
    for doc_id, collector in COLLECTORS.items():
        try:
            data = collector()
            ok = push_doc(doc_id, data)
            results[doc_id] = "ok" if ok else "push_failed"
            print(f"  {'✓' if ok else '✗'} {doc_id}")
        except Exception as e:
            results[doc_id] = str(e)
            logging.error(f"collect/push failed: {doc_id}: {e}")
            print(f"  ✗ {doc_id}: {e}")

    push_log = {
        "timestamp": datetime.now().isoformat(),
        "success_count": sum(1 for v in results.values() if v == "ok"),
        "fail_count": sum(1 for v in results.values() if v != "ok"),
        "errors": {k: v for k, v in results.items() if v != "ok"},
    }
    push_doc("_push_log", push_log)
    print(f"  _push_log: {push_log['success_count']}/{len(COLLECTORS)} OK")
    return push_log


if __name__ == "__main__":
    print(f"[{datetime.now().strftime('%H:%M:%S')}] firebase_pusher_v2 開始")
    log = push_all()
    execute_pending_commands()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 完了 "
          f"成功:{log['success_count']} 失敗:{log['fail_count']}")
    if log["errors"]:
        print(f"  エラー詳細: {log['errors']}")
```

- [ ] **Step 4: テストを実行して通過を確認**

```bash
python -m pytest tests/test_pusher_v2.py -v
```
Expected: 12 passed

- [ ] **Step 5: 手動実行テスト（自宅NW接続時のみ）**

```bash
python firebase_pusher_v2.py
```
Expected: 各ドキュメント ✓ / ✗ が表示され、最後に `完了 成功:N 失敗:M`

- [ ] **Step 6: スケジューラのコマンドをpusher_v2に向け替え**

既存の `21:55` スケジューラエントリを確認:
```bash
schtasks /query /fo LIST | findstr /i "pusher"
```

見つかったタスク名で（**pythonwはフルパス必須**）:
```bash
schtasks /change /tn "<タスク名>" /tr "C:\Users\0000112191\AppData\Local\Programs\Python\Python312\pythonw.exe C:\Users\0000112191\.claude\scripts\agents\firebase_pusher_v2.py"
```

pythonwのパスが不明な場合:
```bash
where pythonw
```

- [ ] **Step 7: コミット**

```bash
cd "C:\Users\0000112191\.claude"
git add scripts/agents/firebase_pusher_v2.py scripts/agents/tests/test_pusher_v2.py
git commit -m "feat: pusher_v2 push_all/_push_log/execute_pending_commands 実装完了"
git push origin master
```

---

### Task 4: data_loader_v2.py

**Files:**
- Create: `streamlit_dashboard/utils/data_loader_v2.py`
- Create: `streamlit_dashboard/tests/test_data_loader_v2.py`

- [ ] **Step 1: テストファイルを作成**

```python
# streamlit_dashboard/tests/test_data_loader_v2.py
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))

# st.cache_data デコレータをモック
import streamlit as st
st.cache_data = lambda ttl=None: (lambda f: f)

def _mock_get_doc(collection, doc_id):
    return None  # Firestore応答なし = デフォルト値テスト

def test_get_system_health_returns_default_on_empty():
    with patch("utils.firebase_client.get_doc", side_effect=_mock_get_doc):
        from utils.data_loader_v2 import get_system_health
        result = get_system_health()
    assert isinstance(result, dict)
    assert "flows" in result
    assert "alerts" in result
    assert isinstance(result["alerts"], list)

def test_get_tasks_returns_default_on_empty():
    with patch("utils.firebase_client.get_doc", side_effect=_mock_get_doc):
        from utils.data_loader_v2 import get_tasks
        result = get_tasks()
    assert isinstance(result, dict)
    assert "total" in result

def test_get_push_log_no_cache():
    """get_push_log はキャッシュなしで常にFirestoreを叩く"""
    call_count = [0]
    def counting_get(col, doc):
        call_count[0] += 1
        return None
    with patch("utils.firebase_client.get_doc", side_effect=counting_get):
        from utils.data_loader_v2 import get_push_log
        get_push_log()
        get_push_log()
    assert call_count[0] >= 2  # キャッシュされていない

def test_no_function_raises_key_error():
    """全get_*関数がKeyError/AttributeErrorを起こさない"""
    with patch("utils.firebase_client.get_doc", side_effect=_mock_get_doc):
        import utils.data_loader_v2 as dl
        for name in ["get_system_health","get_tasks","get_business","get_bizdev",
                     "get_cx_quality","get_ai_ops","get_finance","get_content","get_meta"]:
            result = getattr(dl, name)()
            assert isinstance(result, dict), f"{name} should return dict"
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
cd "C:\Users\0000112191\.claude\scripts\streamlit_dashboard"
python -m pytest tests/test_data_loader_v2.py -v 2>&1 | head -10
```
Expected: ModuleNotFoundError

- [ ] **Step 3: data_loader_v2.py を実装**

```python
# streamlit_dashboard/utils/data_loader_v2.py
import streamlit as st
from utils.firebase_client import get_doc


@st.cache_data(ttl=3600)
def get_system_health() -> dict:
    return get_doc("dashboard", "system_health") or {
        "flows": {}, "alerts": [], "pipeline_count": 0,
        "scheduler": {}, "last_run": "",
    }


@st.cache_data(ttl=3600)
def get_tasks() -> dict:
    return get_doc("dashboard", "tasks") or {
        "summary": {}, "active": {}, "total": 0,
        "in_progress": 0, "high_priority": [],
    }


@st.cache_data(ttl=3600)
def get_business() -> dict:
    return get_doc("dashboard", "business") or {
        "business_status": {}, "pf_watch": {}, "freelance": {},
    }


@st.cache_data(ttl=3600)
def get_bizdev() -> dict:
    return get_doc("dashboard", "bizdev") or {"report": {}, "trend": {}}


@st.cache_data(ttl=3600)
def get_cx_quality() -> dict:
    return get_doc("dashboard", "cx_quality") or {
        "cx_report": {}, "levelup_status": {}, "levelup_history": [],
    }


@st.cache_data(ttl=3600)
def get_ai_ops() -> dict:
    return get_doc("dashboard", "ai_ops") or {
        "autonomous_loop": {}, "agent_run_stats": {}, "agent_insights": {},
    }


@st.cache_data(ttl=3600)
def get_finance() -> dict:
    return get_doc("dashboard", "finance") or {
        "api_budget": {}, "cost_report": {}, "token_usage": {},
    }


@st.cache_data(ttl=3600)
def get_content() -> dict:
    return get_doc("dashboard", "content") or {
        "mempalace": {}, "mempalace_rooms": {}, "obsidian": {},
        "sync_brain": {}, "sync_tasks": {},
    }


@st.cache_data(ttl=3600)
def get_meta() -> dict:
    return get_doc("dashboard", "meta") or {
        "risk_report": {}, "failure_patterns": {}, "code_health": {},
        "eval_status": {}, "pdca": {}, "biz_pdca": {}, "last_updated": "",
    }


def get_push_log() -> dict:
    """キャッシュなし — 鮮度バナー表示用"""
    return get_doc("dashboard", "_push_log") or {
        "timestamp": None, "success_count": 0, "fail_count": 0, "errors": {},
    }
```

- [ ] **Step 4: テストを実行して通過を確認**

```bash
python -m pytest tests/test_data_loader_v2.py -v
```
Expected: 4 passed

- [ ] **Step 5: コミット**

```bash
git add utils/data_loader_v2.py tests/test_data_loader_v2.py
git commit -m "feat: data_loader_v2 追加 (10関数・全デフォルト値返却・ttl=3600)"
```

---

## Phase 2: UI（グラスモーフィズム4ページ）

---

### Task 5: style.py にグラスモーフィズムCSS追加

**Files:**
- Modify: `streamlit_dashboard/utils/style.py`

- [ ] **Step 1: 既存 GLOBAL_CSS の末尾にグラスモーフィズムクラスを追加**

`style.py` の `GLOBAL_CSS` 文字列の `</style>` の直前に以下を挿入:

```css
/* ============ グラスモーフィズムテーマ ============ */
.glass-card {
    background: rgba(255, 255, 255, 0.07);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
}
.glass-kpi {
    background: rgba(255, 255, 255, 0.07);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 10px;
    padding: 14px 10px;
    text-align: center;
}
.glass-kpi .kpi-label { color: #6c7086; font-size: 11px; margin-bottom: 4px; }
.glass-kpi .kpi-value { font-size: 24px; font-weight: 700; }
.glass-alert-red {
    background: rgba(243,139,168,0.15);
    border: 1px solid rgba(243,139,168,0.4);
    border-radius: 8px;
    padding: 8px 14px;
    color: #f38ba8;
    font-size: 13px;
    margin-bottom: 10px;
}
.glass-alert-yellow {
    background: rgba(249,226,175,0.15);
    border: 1px solid rgba(249,226,175,0.4);
    border-radius: 8px;
    padding: 8px 14px;
    color: #f9e2af;
    font-size: 13px;
    margin-bottom: 10px;
}
.freshness-ok   { background:rgba(166,227,161,0.12); border:1px solid rgba(166,227,161,0.35);
                  border-radius:20px; padding:3px 12px; color:#a6e3a1; font-size:11px; }
.freshness-warn { background:rgba(249,226,175,0.12); border:1px solid rgba(249,226,175,0.35);
                  border-radius:20px; padding:3px 12px; color:#f9e2af; font-size:11px; }
.freshness-stale{ background:rgba(243,139,168,0.12); border:1px solid rgba(243,139,168,0.35);
                  border-radius:20px; padding:3px 12px; color:#f38ba8; font-size:11px; }
.flow-badge-ok   { background:rgba(166,227,161,0.15); border:1px solid rgba(166,227,161,0.3);
                   border-radius:4px; padding:3px 8px; color:#a6e3a1; font-size:11px; margin:2px; display:inline-block; }
.flow-badge-err  { background:rgba(243,139,168,0.15); border:1px solid rgba(243,139,168,0.3);
                   border-radius:4px; padding:3px 8px; color:#f38ba8; font-size:11px; margin:2px; display:inline-block; }
.flow-badge-warn { background:rgba(249,226,175,0.15); border:1px solid rgba(249,226,175,0.3);
                   border-radius:4px; padding:3px 8px; color:#f9e2af; font-size:11px; margin:2px; display:inline-block; }
/* ============================================== */
```

- [ ] **Step 2: freshness_banner() ヘルパー関数を style.py に追加**

```python
def freshness_banner(push_log: dict) -> str:
    """_push_logのtimestampから鮮度バナーHTMLを返す"""
    from datetime import datetime
    ts = push_log.get("timestamp")
    errors = push_log.get("errors", {})
    fail = push_log.get("fail_count", 0)

    if not ts:
        return '<span class="freshness-stale">⚠️ データ未取得</span>'

    try:
        dt = datetime.fromisoformat(ts)
        minutes = int((datetime.now() - dt).total_seconds() / 60)
    except Exception:
        return '<span class="freshness-warn">更新時刻不明</span>'

    if minutes < 120:
        css = "freshness-ok"
        label = f"● 更新: {minutes}分前"
    elif minutes < 1440:
        css = "freshness-warn"
        label = f"⚠️ 更新: {minutes // 60}時間前"
    else:
        css = "freshness-stale"
        label = f"🔴 更新: {minutes // 1440}日前"

    suffix = f" ({fail}件失敗)" if fail else ""
    return f'<span class="{css}">{label}{suffix}</span>'
```

- [ ] **Step 3: Streamlitを起動して既存ページが壊れていないか確認**

```bash
cd "C:\Users\0000112191\.claude\scripts\streamlit_dashboard"
streamlit run Home.py --server.headless true --server.port 8502 &
# ブラウザで http://localhost:8502 を開いて既存ページが表示されることを確認
```

- [ ] **Step 4: コミット**

```bash
git add utils/style.py
git commit -m "feat: style.py にグラスモーフィズムCSS + freshness_banner追加"
```

---

### Task 6: Home.py 再構築

**Files:**
- Modify: `streamlit_dashboard/Home.py`

- [ ] **Step 1: Home.py を完全に置き換え**

```python
# streamlit_dashboard/Home.py
import streamlit as st
from utils import style
from utils.data_loader_v2 import (
    get_system_health, get_tasks, get_finance, get_meta, get_push_log
)

st.set_page_config(page_title="BizDash", page_icon="📊", layout="wide")
style.inject()

# --- 鮮度バナー ---
push_log = get_push_log()
freshness_html = style.freshness_banner(push_log)
st.markdown(
    f'<div style="text-align:right;margin-bottom:8px;">{freshness_html}</div>',
    unsafe_allow_html=True
)

# --- ヘッダー ---
st.markdown('<h1 style="color:#cba6f7;margin-bottom:4px;">📊 BizDash</h1>', unsafe_allow_html=True)

# --- アラートバナー ---
health = get_system_health()
alerts = health.get("alerts", [])
tasks = get_tasks()
high = tasks.get("high_priority", [])

if alerts or high:
    items = alerts + [f"High: {t}" for t in high[:3]]
    alert_text = " &nbsp;|&nbsp; ".join(items[:5])
    st.markdown(f'<div class="glass-alert-red">🔴 {alert_text}</div>', unsafe_allow_html=True)

# --- KPIカード ---
finance = get_finance()
meta = get_meta()
flows = health.get("flows", {})
ok_flows = sum(1 for v in flows.values() if isinstance(v, dict) and v.get("status") == "ok")
total_flows = len(flows)
budget = finance.get("api_budget", {})
budget_pct = budget.get("remaining_pct", 0) if isinstance(budget, dict) else 0
eval_s = meta.get("eval_status", {})
success_rate = eval_s.get("success_rate", 0) if isinstance(eval_s, dict) else 0
in_progress = tasks.get("in_progress", 0)

kpi_color = {"pipeline": "#a6e3a1", "kanban": "#89b4fa", "budget": "#f9e2af", "eval": "#cba6f7"}

col1, col2, col3, col4 = st.columns(4)
for col, label, value, unit, color in [
    (col1, "パイプライン", f"{ok_flows}/{total_flows}", "稼働中", kpi_color["pipeline"]),
    (col2, "Kanban",      str(in_progress),              "進行中", kpi_color["kanban"]),
    (col3, "API予算",     f"{int(budget_pct)}%",          "残余",   kpi_color["budget"]),
    (col4, "Eval成功率",  f"{int(success_rate)}%",        "",       kpi_color["eval"]),
]:
    with col:
        st.markdown(
            f'<div class="glass-kpi">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value" style="color:{color};">{value}</div>'
            f'<div class="kpi-label">{unit}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

# --- System Health ---
st.markdown("---")
st.markdown("**⚙️ System Health**")
badges_html = ""
for name, info in flows.items():
    status = info.get("status", "unknown") if isinstance(info, dict) else "unknown"
    css = "flow-badge-ok" if status == "ok" else ("flow-badge-err" if status == "error" else "flow-badge-warn")
    icon = "✓" if status == "ok" else "✗"
    badges_html += f'<span class="{css}">{name} {icon}</span>'
if badges_html:
    st.markdown(
        f'<div class="glass-card" style="margin-top:8px;">{badges_html}</div>',
        unsafe_allow_html=True
    )
else:
    st.markdown(
        '<div class="glass-alert-yellow">⬜ フロー情報なし — pusherを実行してください</div>',
        unsafe_allow_html=True
    )
```

- [ ] **Step 2: Streamlitで確認**

```bash
streamlit run Home.py --server.port 8502
```
ブラウザで以下を確認:
- グラスカード・KPI・鮮度バナーが表示される
- Firestoreデータがなくても0/0・0%のデフォルト値で表示される（クラッシュしない）

- [ ] **Step 3: コミット**

```bash
git add Home.py
git commit -m "feat: Home.py グラスモーフィズム再構築 (鮮度バナー+KPI+SystemHealth)"
```

---

### Task 7: 1_タスク.py 作成

**Files:**
- Create: `streamlit_dashboard/pages/1_タスク.py`

- [ ] **Step 1: ファイルを作成**

```python
# streamlit_dashboard/pages/1_タスク.py
import streamlit as st
from utils import style
from utils.data_loader_v2 import get_tasks, get_system_health, get_push_log
from utils.firebase_client import get_collection, patch_doc

st.set_page_config(page_title="タスク | BizDash", layout="wide")
style.inject()

push_log = get_push_log()
st.markdown(
    f'<div style="text-align:right;">{style.freshness_banner(push_log)}</div>',
    unsafe_allow_html=True
)
st.markdown('<h2 style="color:#cba6f7;">✅ タスク</h2>', unsafe_allow_html=True)

tasks_data = get_tasks()
health = get_system_health()

# --- 左右レイアウト ---
col_left, col_right = st.columns([1, 2])

with col_left:
    st.markdown("**🔴 要対応**")
    alerts = health.get("alerts", [])
    high = tasks_data.get("high_priority", [])
    items = [{"text": a, "level": "red"} for a in alerts] + \
            [{"text": t, "level": "yellow"} for t in high[:5]]

    if items:
        for item in items:
            css = "glass-alert-red" if item["level"] == "red" else "glass-alert-yellow"
            st.markdown(f'<div class="{css}">{item["text"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="glass-card" style="color:#a6e3a1;">✅ 要対応なし</div>',
                    unsafe_allow_html=True)

with col_right:
    st.markdown("**📋 Kanban**")
    # kanban_tasksコレクションから直接取得（詳細表示用）
    raw_tasks = get_collection("kanban_tasks", max_docs=200)
    todo     = [t for t in raw_tasks if t.get("status") == "todo"]
    in_prog  = [t for t in raw_tasks if t.get("status") == "in_progress"]
    done     = [t for t in raw_tasks if t.get("status") == "done"]

    c1, c2, c3 = st.columns(3)
    for col, label, items, color in [
        (c1, f"TODO ({len(todo)})",          todo,    "#6c7086"),
        (c2, f"IN PROGRESS ({len(in_prog)})", in_prog, "#f9e2af"),
        (c3, f"DONE ({len(done)})",           done,    "#a6e3a1"),
    ]:
        with col:
            st.markdown(f'<div style="color:{color};font-size:11px;margin-bottom:6px;">{label}</div>',
                        unsafe_allow_html=True)
            for t in items[:10]:
                title = t.get("title", t.get("subject", ""))[:40]
                kid = t.get("id", "")
                st.markdown(
                    f'<div class="glass-card" style="padding:8px;font-size:11px;">'
                    f'<span style="color:#6c7086;">{kid}</span><br>{title}</div>',
                    unsafe_allow_html=True
                )
```

- [ ] **Step 2: Streamlitで確認**

```bash
streamlit run Home.py --server.port 8502
```
「タスク」ページに遷移して要対応リストとKanbanが表示されることを確認。

- [ ] **Step 3: コミット**

```bash
git add pages/1_タスク.py
git commit -m "feat: 1_タスク.py 新規作成 (要対応+Kanban)"
```

---

### Task 8: 2_ビジネス.py と 3_AIシステム.py 作成

**Files:**
- Create: `streamlit_dashboard/pages/2_ビジネス.py`
- Create: `streamlit_dashboard/pages/3_AIシステム.py`

- [ ] **Step 1: 2_ビジネス.py を作成**

```python
# streamlit_dashboard/pages/2_ビジネス.py
import streamlit as st
from utils import style
from utils.data_loader_v2 import get_business, get_bizdev, get_cx_quality, get_meta, get_push_log

st.set_page_config(page_title="ビジネス | BizDash", layout="wide")
style.inject()

push_log = get_push_log()
st.markdown(f'<div style="text-align:right;">{style.freshness_banner(push_log)}</div>', unsafe_allow_html=True)
st.markdown('<h2 style="color:#cba6f7;">📈 ビジネス</h2>', unsafe_allow_html=True)

business = get_business()
bizdev = get_bizdev()
cx = get_cx_quality()
meta = get_meta()

tab1, tab2, tab3, tab4 = st.tabs(["📊 事業状況", "🚀 BizDev", "🎯 CX品質", "🔄 PDCA"])

with tab1:
    biz_status = business.get("business_status", {})
    if biz_status:
        for k, v in list(biz_status.items())[:20]:
            st.markdown(
                f'<div class="glass-card"><span style="color:#6c7086;">{k}</span><br>'
                f'<span style="color:#cdd6f4;">{v}</span></div>',
                unsafe_allow_html=True
            )
    else:
        st.info("データなし — pusherを実行してください")

with tab2:
    report = bizdev.get("report", {})
    if report:
        for k, v in list(report.items())[:20]:
            st.markdown(
                f'<div class="glass-card"><span style="color:#6c7086;">{k}</span><br>'
                f'<span style="color:#cdd6f4;">{str(v)[:200]}</span></div>',
                unsafe_allow_html=True
            )
    else:
        st.info("BizDevデータなし")

with tab3:
    cx_report = cx.get("cx_report", {})
    levelup = cx.get("levelup_status", {})
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**CXレポート**")
        for k, v in list(cx_report.items())[:10]:
            st.markdown(f'<div class="glass-card"><b>{k}</b>: {v}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("**LevelUp状況**")
        for k, v in list(levelup.items())[:10]:
            st.markdown(f'<div class="glass-card"><b>{k}</b>: {v}</div>', unsafe_allow_html=True)

with tab4:
    pdca = meta.get("pdca", {})
    biz_pdca = meta.get("biz_pdca", {})
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**PDCA**")
        for k, v in list(pdca.items())[:10]:
            st.markdown(f'<div class="glass-card"><b>{k}</b>: {str(v)[:100]}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("**Biz PDCA**")
        for k, v in list(biz_pdca.items())[:10]:
            st.markdown(f'<div class="glass-card"><b>{k}</b>: {str(v)[:100]}</div>', unsafe_allow_html=True)
```

- [ ] **Step 2: 3_AIシステム.py を作成**

```python
# streamlit_dashboard/pages/3_AIシステム.py
import streamlit as st
from utils import style
from utils.data_loader_v2 import get_ai_ops, get_meta, get_content, get_system_health, get_push_log

st.set_page_config(page_title="AI・システム | BizDash", layout="wide")
style.inject()

push_log = get_push_log()
st.markdown(f'<div style="text-align:right;">{style.freshness_banner(push_log)}</div>', unsafe_allow_html=True)
st.markdown('<h2 style="color:#cba6f7;">🤖 AI・システム</h2>', unsafe_allow_html=True)

ai_ops = get_ai_ops()
meta = get_meta()
content = get_content()
health = get_system_health()

tab1, tab2, tab3, tab4 = st.tabs(["🔄 自律ループ", "📊 Eval品質", "🧠 Brain同期", "🏢 システム"])

with tab1:
    loop = ai_ops.get("autonomous_loop", {})
    stats = ai_ops.get("agent_run_stats", {})
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**AutonomousLoop**")
        for k, v in list(loop.items())[:15]:
            st.markdown(f'<div class="glass-card"><b>{k}</b>: {str(v)[:100]}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("**エージェント実行統計**")
        for k, v in list(stats.items())[:15]:
            st.markdown(f'<div class="glass-card"><b>{k}</b>: {v}</div>', unsafe_allow_html=True)

with tab2:
    eval_s = meta.get("eval_status", {})
    failure = meta.get("failure_patterns", {})
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Eval状況**")
        for k, v in list(eval_s.items())[:15]:
            st.markdown(f'<div class="glass-card"><b>{k}</b>: {v}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("**障害パターン**")
        for k, v in list(failure.items())[:10]:
            st.markdown(f'<div class="glass-card"><b>{k}</b>: {str(v)[:100]}</div>', unsafe_allow_html=True)

with tab3:
    brain = content.get("sync_brain", {})
    mp = content.get("mempalace", {})
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Brain同期**")
        for k, v in list(brain.items())[:10]:
            st.markdown(f'<div class="glass-card"><b>{k}</b>: {str(v)[:100]}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("**Mempalace**")
        for k, v in list(mp.items())[:10]:
            st.markdown(f'<div class="glass-card"><b>{k}</b>: {str(v)[:100]}</div>', unsafe_allow_html=True)

with tab4:
    flows = health.get("flows", {})
    scheduler = health.get("scheduler", {})
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**フロー一覧**")
        for name, info in flows.items():
            status = info.get("status", "?") if isinstance(info, dict) else str(info)
            css = "flow-badge-ok" if status == "ok" else "flow-badge-err"
            st.markdown(f'<span class="{css}">{name}: {status}</span>', unsafe_allow_html=True)
    with col2:
        st.markdown("**スケジューラ**")
        entries = scheduler.get("entries", [])
        for entry in entries[:20]:
            st.markdown(f'<div class="glass-card" style="font-size:10px;">{entry[:80]}</div>',
                        unsafe_allow_html=True)
```

- [ ] **Step 3: Streamlitで全4ページを確認**

```bash
streamlit run Home.py --server.port 8502
```
全ページを開いてクラッシュしないこと、データなしでもデフォルト表示されることを確認。

- [ ] **Step 4: コミット**

```bash
git add pages/2_ビジネス.py pages/3_AIシステム.py
git commit -m "feat: 2_ビジネス.py + 3_AIシステム.py 新規作成"
```

---

## Phase 3: クリーンアップ

---

### Task 9: 旧ページ削除・レガシーHTML系削除

**Files:**
- Delete: `streamlit_dashboard/pages/` の 0_〜9_ 9ファイル
- Delete: `scripts/agents/generate_dashboard.py`
- Delete: `scripts/agents/generate_dashboard_safe.py`
- Delete: `scripts/agents/dashboard_sections.py`

**前提条件:** Task 6〜8 で新4ページが動作確認済みであること。

- [ ] **Step 1: 旧Streamlitページを削除**

```bash
cd "C:\Users\0000112191\.claude\scripts\streamlit_dashboard\pages"
# 削除対象を確認してから削除
ls 0_* 1_* 2_* 3_* 4_* 5_* 6_* 7_* 8_* 9_* 2>/dev/null
# 新ページ (1_タスク.py, 2_ビジネス.py, 3_AIシステム.py) は削除しない
rm 0_システム概要.py 1_要対応.py 2_タスクボード.py 3_稼働状況.py \
   4_事業状況.py 5_BizDev.py 6_CX品質.py 7_経営体制.py \
   8_AI管理.py 9_Eval品質.py 2>/dev/null || true
```

- [ ] **Step 2: Streamlitで4ページのみ表示されることを確認**

```bash
streamlit run Home.py --server.port 8502
```
サイドバーに「ホーム / タスク / ビジネス / AI・システム」の4つだけ表示されることを確認。

- [ ] **Step 3: レガシーHTML系3ファイルを削除**

```bash
cd "C:\Users\0000112191\.claude\scripts\agents"
# 削除前にスケジューラから参照されていないか確認
schtasks /query /fo LIST | findstr /i "generate_dashboard"
# 参照がなければ削除
rm generate_dashboard.py generate_dashboard_safe.py dashboard_sections.py
```

- [ ] **Step 4: generate_dashboard_safe.pyへの参照が他にないか確認**

```bash
grep -r "generate_dashboard" "C:\Users\0000112191\.claude\scripts" --include="*.py" -l
```
Expected: 残存参照があれば該当ファイルを確認してコメントアウトまたは削除。

- [ ] **Step 5: 最終動作確認**

```bash
# pusher_v2 を手動実行（自宅NW接続時）
python firebase_pusher_v2.py
# Streamlit起動
streamlit run Home.py --server.port 8502
```
確認項目:
- 鮮度バナーが「更新: X分前」と表示される
- KPI4枚が値付きで表示される
- System Healthにフロー名が表示される
- _push_log.errors が空 or エラー内容が確認できる

- [ ] **Step 6: git push**

```bash
cd "C:\Users\0000112191\.claude\scripts\streamlit_dashboard"
git add -A
git commit -m "feat: ダッシュボード再構築完了 (4ページ/グラスモーフィズム/Firestore10統合/レガシー削除)"
git push origin master
```

---

## 成功基準チェックリスト

- [ ] `_push_log` に `errors` が記録され、反映失敗の原因が一目で分かる
- [ ] Streamlitに表示されるページが4つのみ（Home + 3ページ）
- [ ] Firestoreドキュメントが10個に統合されている
- [ ] スケジューラ追加ゼロ（21:55のみ）
- [ ] 全ページでデータなしでもクラッシュしない
- [ ] グラスモーフィズムUIが全ページで適用されている
- [ ] `generate_dashboard.py` / `generate_dashboard_safe.py` / `dashboard_sections.py` が削除されている
