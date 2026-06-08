# ダッシュボード再構築設計書

**日付:** 2026-06-09  
**対象:** `streamlit_dashboard/` — biz-ai-dashboard.streamlit.app  
**目的:** 反映不具合の根絶・シンプル化・グラスモーフィズムUIへのモダン化

---

## 背景と課題

- `biz-ai-dashboard.web.app`（Firebase Hosting HTML系）は不具合多発のため Streamlit へ移管済み
- 現行Streamlitダッシュボードで「古い値が残り続ける」不具合が継続発生
- 根本原因：Firestoreドキュメント45件分散 + pusherの失敗が見えない + レガシーHTML系コードが残存
- ページ数11（Home + 9ページ）で情報分散・ナビ往復が多い

---

## 設計方針

1. **レガシーHTML系を完全削除** — 不具合の温床となっているコードを根絶
2. **Firestoreドキュメントを45 → 10に統合** — pusher失敗箇所を特定しやすくする
3. **4ページに集約** — グラスモーフィズムUIで見やすく再構築
4. **PC負荷ゼロ増** — スケジューラ追加なし・自動リフレッシュなし・pusherは21:55のみ

---

## Section 1：アーキテクチャ

### 削除対象（レガシーHTML系）
```
scripts/agents/generate_dashboard.py        # 削除
scripts/agents/generate_dashboard_safe.py   # 削除
scripts/agents/dashboard_sections.py        # 削除（400KB）
```

### 新規・改修対象
```
scripts/agents/firebase_pusher_v2.py        # 新規（既存pusherのリファクタ）
streamlit_dashboard/utils/data_loader_v2.py # 新規（10関数に統合）
streamlit_dashboard/utils/style.py          # 改修（グラスモーフィズムCSS追加）
streamlit_dashboard/Home.py                 # 改修
streamlit_dashboard/pages/                  # 4ページに再構成
```

### データフロー
```
ローカルJSON（整理後）
    ↓
firebase_pusher_v2.py（21:55スケジューラのみ・手動実行も可）
    ↓ 10ドキュメント統合push
    ↓ 完了後 _push_log に {timestamp, success_count, fail_count, errors[]} を書き込み
Firestore: dashboard/ コレクション（10ドキュメント）
    ↓
data_loader_v2.py（@st.cache_data ttl=3600、全関数デフォルト値返却）
    ↓
Streamlit 4ページ（鮮度バナー付き）
```

---

## Section 2：Firestoreドキュメント統合（45 → 10）

| 新ドキュメントID | 統合元（旧ドキュメント群） |
|----------------|--------------------------|
| `system_health` | pipeline_status, pipeline_logs, pipeline_merged, scheduler, health_check, flow_status, execution_times |
| `tasks` | kanban_summary, kanban_active（kanban_tasksコレクションは維持） |
| `business` | business_status, pf_watch, freelance_report |
| `bizdev` | bizdev_report, bizdev_trend |
| `cx_quality` | cx_report, levelup_status, levelup_history |
| `ai_ops` | autonomous_loop, agent_run_stats, agent_insights, agents_context |
| `finance` | api_budget, pipeline_cost_report, pipeline_token_usage |
| `content` | mempalace, mempalace_rooms, obsidian_stats, sync_brain, sync_tasks, sync_outputs |
| `meta` | risk_report, failure_patterns, code_health, rule_engine, datasource, biz_pdca_reports, pdca, learning_system, eval_status, lessons_learned, routines |
| `_push_log` | 新設：最終push時刻・成功/失敗件数・エラー詳細 |

**維持（変更なし）:**
- `kanban_tasks` コレクション（Streamlitからの書き込みあり）
- `comments` / `dashboard_comments`（削除・上書き禁止ルールあり）
- `commands` コレクション（Streamlit→パイプラインへの指示送信用）

---

## Section 3：firebase_pusher_v2.py 設計

```python
# スケジュール: 21:55のみ（タスクスケジューラ）。5分毎・頻繁実行禁止
# 手動実行: python firebase_pusher_v2.py でいつでも即反映可能

def collect_system_health() -> dict: ...   # pipeline_status + scheduler + health_check + flow_status
def collect_tasks() -> dict: ...            # kanban_summary + kanban_active
def collect_business() -> dict: ...         # business_status + pf_watch + freelance
def collect_bizdev() -> dict: ...           # bizdev_report + trend
def collect_cx_quality() -> dict: ...       # cx_report + levelup
def collect_ai_ops() -> dict: ...           # autonomous_loop + agent_stats
def collect_finance() -> dict: ...          # api_budget + cost
def collect_content() -> dict: ...          # mempalace + obsidian + brain
def collect_meta() -> dict: ...             # risk + failure_patterns + eval

def push_all():
    results = {}
    for doc_id, collector in COLLECTORS.items():
        try:
            data = collector()
            if data:
                firestore_patch(f"dashboard/{doc_id}", data)
                results[doc_id] = "ok"
        except Exception as e:
            results[doc_id] = str(e)   # 失敗しても続行
            log_error(doc_id, e)

    # 最後に _push_log を書き込む
    push_log = {
        "timestamp": now_iso(),
        "success_count": sum(1 for v in results.values() if v == "ok"),
        "fail_count": sum(1 for v in results.values() if v != "ok"),
        "errors": {k: v for k, v in results.items() if v != "ok"}
    }
    firestore_patch("dashboard/_push_log", push_log)

    # StreamlitからのコマンドをFirestoreのcommandsコレクションから取り出して実行
    # 既存の execute_pending_commands() ロジックをそのまま移植
    execute_pending_commands()
```

**制約（CLAUDE.md準拠）:**
- `from subprocess_wrapper import safe_run` 使用
- 外部HTTP: `User-Agent: Claude-Script/1.0`
- ループ内高頻度HTTP禁止 → 各ドキュメント1回のみ

---

## Section 4：data_loader_v2.py 設計

```python
@st.cache_data(ttl=3600)   # 1時間キャッシュ → Firestoreアクセス最小化
def get_system_health() -> dict:
    data = firestore_get("dashboard/system_health")
    return data or DEFAULT_SYSTEM_HEALTH   # 必ずdictを返す・Noneなし

@st.cache_data(ttl=3600)
def get_tasks() -> dict: ...

@st.cache_data(ttl=3600)
def get_business() -> dict: ...

# ... 同様に10関数

def get_push_log() -> dict:
    """鮮度表示用。キャッシュなし（毎回最新を読む）"""
    return firestore_get("dashboard/_push_log") or {"timestamp": None}
```

**設計原則:**
- 全関数がデフォルト値を返す → `AttributeError` / `KeyError` ゼロ
- `get_push_log()` のみキャッシュなし（鮮度表示のため）
- 自動リフレッシュなし・ポーリングなし

---

## Section 5：4ページ構成

### ナビゲーション（全ページ共通）
```
BizDash  |  🏠 ホーム  |  ✅ タスク  |  📈 ビジネス  |  🤖 AI・システム
                                                        [● 更新: 昨日 21:55]
```

### Page 1 — ホーム（Home.py）
- 鮮度バナー：`_push_log.timestamp` → 「更新: X分前」/ 2時間超で⚠️ / 24時間超で🔴
- アラートバナー：要対応件数・停止フロー名を赤帯表示
- KPIカード4枚（グラスカード）：パイプライン稼働数 / Kanban進行中 / API予算残 / Eval成功率
- System Health：4フローのステータスバッジ

### Page 2 — タスク（1_タスク.py）
- 左カラム：要対応リスト（`system_health.alerts` + `tasks.high_priority`）
- 右カラム：Kanbanボード（TODO / IN PROGRESS / DONE の3列）
- タスク詳細・編集機能：現行の `2_タスクボード.py` の機能をそのまま移植

### Page 3 — ビジネス（2_ビジネス.py）
- 事業状況KPI（`business`）
- BizDevレポート・トレンド（`bizdev`）
- CX品質スコア（`cx_quality`）
- PDCAサイクル状況（`meta.pdca`）

### Page 4 — AI・システム（3_AIシステム.py）
- 自律ループ・エージェント稼働状況（`ai_ops`）
- Eval品質・エラー率（`meta.eval_status`）
- Mempalace / Brain同期状態（`content`）
- 経営体制・パイプライン一覧（`system_health` / `meta`）

---

## Section 6：グラスモーフィズムCSS（style.py）

```css
/* ベーステーマ */
background: linear-gradient(135deg, #0f0f17, #1a1a2e, #16213e);

/* グラスカード */
.glass-card {
  background: rgba(255, 255, 255, 0.07);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
}

/* ステータスカラー */
--color-ok:      #a6e3a1;   /* 緑 */
--color-warn:    #f9e2af;   /* 黄 */
--color-error:   #f38ba8;   /* 赤 */
--color-accent:  #cba6f7;   /* 紫 */
--color-info:    #89b4fa;   /* 青 */

/* 鮮度バナー */
.freshness-ok   { background: rgba(166,227,161,0.15); border-color: rgba(166,227,161,0.4); }
.freshness-warn { background: rgba(249,226,175,0.15); border-color: rgba(249,226,175,0.4); }
.freshness-stale{ background: rgba(243,139,168,0.15); border-color: rgba(243,139,168,0.4); }
```

---

## PC負荷への配慮（制約）

| 項目 | 方針 |
|------|------|
| pusherスケジュール | 21:55のみ（1日1回）。追加スケジュール禁止 |
| Streamlit自動リフレッシュ | なし（手動リロードのみ） |
| Firestoreキャッシュ | `ttl=3600`（1時間）でアクセス最小化 |
| ポーリング | 一切禁止 |
| バックグラウンドプロセス | 追加しない |

---

## 移行手順（概要）

1. `firebase_pusher_v2.py` 作成・単体テスト
2. `data_loader_v2.py` 作成
3. 4ページ新規作成（グラスモーフィズム）
4. 旧ページ削除（0_〜9_ の9ファイル）
5. レガシーHTML系3ファイル削除
6. 手動で `firebase_pusher_v2.py` を実行して動作確認
7. タスクスケジューラの21:55エントリを `firebase_pusher_v2.py` に向け替え

---

## 成功基準

- [ ] 古い値が残り続ける問題：`_push_log` の失敗ログで原因が特定できる
- [ ] ページ数：11 → 4
- [ ] Firestoreドキュメント：45 → 10
- [ ] PC負荷：スケジューラ追加ゼロ
- [ ] AttributeError / KeyError：ゼロ（全関数デフォルト値返却）
- [ ] グラスモーフィズムUIが全ページに適用される
