import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, style
from datetime import datetime, date, timedelta

st.set_page_config(page_title="📊 稼働状況", page_icon="📊", layout="wide")
style.inject()

sys_info       = data_loader.system_info()
pl_status      = data_loader.pipeline_status()
cost_report    = data_loader.pipeline_cost_report()
loop_data      = data_loader.autonomous_loop()
ds             = data_loader.datasource()
token_usage    = data_loader.pipeline_token_usage()
all_tasks      = data_loader.kanban_tasks()
all_outputs    = data_loader.sync_outputs()
agent_run_data = data_loader.agent_run_stats()

# ── ヘッダー（失敗有無でステータスバッジ）──────────────────────────────────────
_counts_pre = pl_status.get("counts", {}) if pl_status else {}
hdr_status = "err" if _counts_pre.get("failed", 0) else "ok"
style.page_header("📊 稼働状況",
                  subtitle="🔄 30秒毎自動更新",
                  updated=data_loader.last_updated(),
                  status=hdr_status)

# ── タブ構成（パイプライン／ループログ／リソース／スケジュール）────────────────
tab_pl, tab_loop, tab_res, tab_sched, tab_agent = st.tabs([
    "⚙️ パイプライン", "🔄 ループログ", "💾 リソース", "⏱️ スケジュール", "🤖 エージェント実績"
])

# ══════════════════════════════════════════════════════════════════════════════
# ⚙️ パイプライン
# ══════════════════════════════════════════════════════════════════════════════
with tab_pl:
    pipelines = pl_status.get("pipelines", [])
    counts    = pl_status.get("counts", {})
    upd       = pl_status.get("updated_at", "")

    style.section_card_start("⚙️ パイプライン稼働状況",
                             "失敗あり" if counts.get("failed", 0) else "正常",
                             "err" if counts.get("failed", 0) else "ok")
    if upd:
        st.caption(f"自動突合: {upd[:16]}  ｜  PIPELINES_DEF定義数: {pl_status.get('total',0)}")

    # 概況メトリクス
    if counts:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            style.kpi_wrap_start("ok")
            st.metric("✅ 正常", counts.get("ok", 0))
            style.kpi_wrap_end()
        with c2:
            style.kpi_wrap_start("critical" if counts.get("failed", 0) else "ok")
            st.metric("❌ 失敗", counts.get("failed", 0))
            style.kpi_wrap_end()
        with c3:
            st.metric("🆕 未実行", counts.get("never_ran", 0) + counts.get("not_registered", 0))
        with c4:
            st.metric("⏸ 停止中", counts.get("stopped", 0))

    ICON = {"ok":"✅","failed":"❌","never_ran":"🆕","not_registered":"⚠️",
            "stopped":"⏸","integrated":"🔗","unknown":"❓"}
    # overall → バッジクラス・ラベル
    BADGE = {
        "ok":            ("badge-ok",   "正常"),
        "failed":        ("badge-err",  "失敗"),
        "never_ran":     ("badge-info", "未実行"),
        "not_registered":("badge-warn", "未登録"),
        "stopped":       ("badge-warn", "停止"),
        "integrated":    ("badge-info", "統合"),
        "unknown":       ("badge-info", "不明"),
    }

    # カテゴリ絞り込み
    categories = sorted({p.get("category","") for p in pipelines if p.get("category")})
    sel_cat = st.selectbox("カテゴリ絞込", ["すべて"] + categories, key="pl_cat")
    filtered = [p for p in pipelines if sel_cat == "すべて" or p.get("category") == sel_cat]
    filtered_sorted = sorted(filtered,
        key=lambda p: p.get("log_last_run") or p.get("sched_last_run") or "", reverse=True)

    output_files = (all_outputs or {}).get("files", [])

    # ── 全パイプラインを table-like な行で一覧表示 ─────────────────────────────
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
                tok_str = f"🪙{tok['total']:,} (${tok.get('cost_usd',0):.3f})"
            style.trow(icon, pname, str(last)[:16], badge_label, badge_cls, tok_str)
    else:
        st.info("該当するパイプラインがありません")

    # ── クリックした1件だけ詳細展開 ────────────────────────────────────────────
    if filtered_sorted:
        names = [p.get("name", "") for p in filtered_sorted]
        sel_name = st.selectbox("詳細を表示するパイプライン", ["（選択）"] + names, key="pl_detail")
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
                related_tasks = sorted(related_tasks, key=lambda t: t.get("updated_at",""), reverse=True)[:3]
                related_outputs = [f for f in output_files
                                   if pname and pname.replace("_","-") in f["name"].lower()
                                   or pname in f["name"].lower()][:3]

                with st.expander(f"{icon} **{pname}**  🕐{last}", expanded=True):
                    st.caption(f"カテゴリ: {p.get('category','')}  ｜  スケジュール: {p.get('schedule','')}")

                    script_ok = "✅" if p.get("script_exists") else "❌"
                    sched_ok  = {"ok":"✅","never":"🆕","not_registered":"⚠️","integrated":"🔗"}.get(p.get("sched_status",""), "❓")
                    log_ok    = {"success":"✅","failed":"❌","no_log":"—","unknown":"❓"}.get(p.get("log_status",""), "❓")
                    st.write(f"スクリプト{script_ok}  スケジューラ{sched_ok}({p.get('sched_state','')})  ログ{log_ok}")

                    if p.get("next_run"):
                        st.caption(f"⏰ 次回: **{p['next_run']}**")

                    if tok and tok.get("total", 0) > 0:
                        cost  = tok.get("cost_usd", 0)
                        model = tok.get("model", "")
                        ts    = (tok.get("ts", "") or "")[:10]
                        st.caption(
                            f"🪙 直近トークン: {tok.get('total',0):,}  "
                            f"（in:{tok.get('input',0):,} / out:{tok.get('output',0):,}）"
                            f"  💰 推定課金: ${cost:.4f}  ｜  {ts} {model}"
                        )
                    else:
                        ts_raw = tok.get("ts", "") if tok else ""
                        ts_str = (ts_raw or "")[:10]
                        st.caption(f"🪙 直近トークン: —（計測なし）" + (f"  ｜  {ts_str}" if ts_str else ""))

                    st.markdown("**📋 直近起票タスク**")
                    if related_tasks:
                        for t in related_tasks:
                            tid    = t.get("id","")
                            tname  = t.get("name","")[:40]
                            status = t.get("status","")
                            s_icon = {"open":"🔵","in_progress":"🟡","to_verify":"🟠","closed":"✅"}.get(status,"⬜")
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
                        if st.button(f"▶ 今すぐ実施", key=f"run_{pname}"):
                            ok = data_loader.send_pipeline_command(pname, task_name)
                            if ok:
                                st.success(f"✅ コマンド送信完了。次回pusher実行時に {task_name} を起動します。")
                            else:
                                st.error("❌ コマンド送信失敗")
    style.section_card_end()

    # ── 削減候補（KT-649）─────────────────────────────────────────────────────
    if cost_report:
        reduction = cost_report.get("reduction_candidates", [])
        high_cost = cost_report.get("high_cost_pipelines", [])
        upd_cr    = cost_report.get("updated", "")
        if reduction or high_cost:
            style.section_card_start("🔻 削減候補・高コストパイプライン", "要確認", "warn")
            st.caption(f"分析日: {upd_cr}  ｜  対象パイプライン: {cost_report.get('total', 0)}本")
            if reduction:
                st.markdown(f"**⚠️ 削減候補（直近30日アクティビティなし・非収益系）: {len(reduction)}件**")
                import pandas as pd
                df_red = pd.DataFrame([{
                    "パイプライン名": r["name"],
                    "カテゴリ":       r["category"],
                    "スケジュール":   r["schedule"],
                } for r in reduction])
                st.dataframe(df_red, use_container_width=True, hide_index=True)
            if high_cost:
                st.markdown(f"**🔥 高コスト（直近30日50回以上のclaude呼び出し）: {len(high_cost)}件**")
                df_hc = pd.DataFrame([{
                    "パイプライン名":       h["name"],
                    "claude呼び出し(30d)": h["claude_calls_30d"],
                    "カテゴリ":             h["category"],
                    "収益貢献":             "✅" if h["revenue_contrib"] else "❌",
                } for h in high_cost])
                st.dataframe(df_hc, use_container_width=True, hide_index=True)
            style.section_card_end()

# ══════════════════════════════════════════════════════════════════════════════
# 🔄 ループログ
# ══════════════════════════════════════════════════════════════════════════════
with tab_loop:
    # ── 実施中タスク・Claude Code処理状況 ─────────────────────────────────────
    realtime = ds.get("realtime", {}) if ds else {}
    claude   = ds.get("claude_code_status", {}) if ds else {}
    _running = bool(realtime and realtime.get("execution_status")) or \
              bool(claude and claude.get("cpu_percent", 0) > 0)
    style.section_card_start("🔄 実施中タスク・処理",
                             "稼働中" if _running else "待機中",
                             "info" if _running else "ok")
    if realtime and realtime.get("execution_status"):
        st.info(f"**実行状態:** {realtime.get('execution_status','-')}  ｜  **詳細:** {realtime.get('running_detail','-')}")
    elif claude and claude.get("cpu_percent", 0) > 0:
        st.info(f"**Claude Code:** CPU {claude.get('cpu_percent',0):.1f}%  ｜  メモリ {claude.get('memory_mb',0):.0f}MB")
    else:
        st.success("✓ 実施中タスクなし（待機中）")
    style.section_card_end()

    # ── 自律ループ実行ログ ─────────────────────────────────────────────────────
    style.section_card_start("🔄 自律ループ実行ログ")
    if loop_data:
        total  = loop_data.get("total_lines", 0)
        upd    = loop_data.get("updated_at", "")
        last_e = loop_data.get("last_entry", "")
        st.caption(f"累計ログ行数: **{total:,}** 行  ｜  取得時刻: {upd[:16]}")
        if last_e:
            st.info(f"**最終エントリ:** {last_e}")
        lines_text = loop_data.get("lines", "")
        if lines_text:
            style.section_title("最新150行")
            st.code(lines_text, language=None)
    else:
        st.info("自律ループログがありません")
    style.section_card_end()

# ══════════════════════════════════════════════════════════════════════════════
# 💾 リソース
# ══════════════════════════════════════════════════════════════════════════════
with tab_res:
    # ── システムリソース ───────────────────────────────────────────────────────
    style.section_card_start("🖥️ システムリソース")
    if sys_info:
        c1, c2, c3, c4, c5 = st.columns(5)
        bat = sys_info.get("battery_percent", 0)
        chg = sys_info.get("charging", False)
        with c1: st.metric("🔋 バッテリー", f"{bat}%" + (" ⚡" if chg else ""))
        with c2: st.metric("💻 CPU",        f"{sys_info.get('cpu_percent', 0):.1f}%")
        with c3: st.metric("🧠 メモリ",     f"{sys_info.get('memory_percent', 0):.1f}%")
        with c4:
            d_p = sys_info.get("disk_percent", 0)
            d_u = sys_info.get("disk_used_gb", 0)
            d_t = sys_info.get("disk_total_gb", 0)
            st.metric("💾 ディスク(C:)", f"{d_p:.0f}%", help=f"{d_u}GB / {d_t}GB")
        with c5: st.metric("🌐 NW", sys_info.get("ssid", "不明"))
    else:
        st.info("システム情報がありません")
    style.section_card_end()

    # ── ディスク使用率 ─────────────────────────────────────────────────────────
    style.section_card_start("💾 ディスク使用率")
    if ds:
        disk_info = ds.get("disk_usage", {})
        if disk_info:
            for drive, info in (disk_info.items() if isinstance(disk_info, dict) else []):
                if isinstance(info, dict):
                    pct = info.get("percent", 0)
                    col = "🔴" if pct > 85 else "🟡" if pct > 70 else "🟢"
                    st.write(f"{col} **{drive}**: {pct:.0f}%  ({info.get('used_gb',0):.1f}GB / {info.get('total_gb',0):.1f}GB)")
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

    # ── ネットワーク情報 ───────────────────────────────────────────────────────
    _is_company = bool(sys_info) and ("SWing" in sys_info.get("ssid", "") or "SWingS" in sys_info.get("ssid", ""))
    style.section_card_start("🌐 ネットワーク状況",
                             "会社NW" if _is_company else "私用NW",
                             "err" if _is_company else "ok")
    if sys_info:
        ssid = sys_info.get("ssid", "不明")
        icon = "🏢" if _is_company else "🏠"
        nw_type = "会社" if _is_company else "私用"
        st.metric(f"{icon} 現在のNW", ssid, help=f"種別: {nw_type}")
        if _is_company:
            st.error("⛔ 会社ネットワーク（SWing/SWingS）接続中 — Claudeの動作を停止します")
        st.caption("会社NW（swing / 43.x.x.x）接続中はエージェント・パイプラインを自動停止。ネットワーク未接続時も同様。")
    else:
        st.info("ネットワーク情報がありません")
    style.section_card_end()

# ══════════════════════════════════════════════════════════════════════════════
# ⏱️ スケジュール（旧 8_スケジュール.py の内容を移植）
# ══════════════════════════════════════════════════════════════════════════════
with tab_sched:
    scheduler  = data_loader.scheduler_tasks()
    exec_times = data_loader.execution_times()

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

    # ── 今日 / 明日 / 今週（next_run ベース）─────────────────────────────────
    style.section_card_start("📅 直近の実行予定")
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
    style.section_card_end()

    # ── タスクスケジューラ実データ ────────────────────────────────────────────
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

    # ── 定義ベース スケジュール ───────────────────────────────────────────────
    style.section_card_start("📋 スケジュール定義（パイプライン別）")
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
    style.section_card_end()

    # ── 実行統計 ──────────────────────────────────────────────────────────────
    style.section_card_start("⏱️ パイプライン実行統計")
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
    style.section_card_end()

# ══════════════════════════════════════════════════════════════════════════════
# 🤖 エージェント実績（Langfuse代替ローカルログ）
# ══════════════════════════════════════════════════════════════════════════════
with tab_agent:
    import pandas as pd

    s24 = agent_run_data.get("last_24h", {})
    s7d = agent_run_data.get("last_7d", {})
    upd = agent_run_data.get("updated_at", "")

    if not s24 or s24.get("error"):
        st.info("エージェント実行ログがまだありません。次回パイプライン実行後に反映されます。")
    else:
        style.section_card_start("🤖 エージェント実績（直近24h）", "", "ok")
        if upd:
            st.caption(f"最終更新: {upd[:16]}")

        # サマリーメトリクス
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("総呼び出し",   s24.get("total", 0))
        c2.metric("スキップ",     s24.get("skipped", 0))
        c3.metric("エラー",       s24.get("errors", 0),
                  delta=None if not s24.get("errors") else f"要確認",
                  delta_color="inverse")
        c4.metric("平均レイテンシ", f"{s24.get('avg_latency_ms', 0):,} ms")
        c5.metric("合計コスト",    f"${s24.get('total_cost_usd', 0):.4f}")

        # エージェント別テーブル
        by_agent_24 = s24.get("by_agent", {})
        if by_agent_24:
            rows = []
            for ag, v in by_agent_24.items():
                err_rate = v["errors"] / v["count"] if v["count"] else 0
                rows.append({
                    "エージェント":   ag,
                    "呼び出し回数":   v["count"],
                    "平均レイテンシ(ms)": v["avg_latency_ms"],
                    "エラー率":       f"{err_rate:.0%}",
                    "コスト($)":      f"{v['cost_usd']:.5f}",
                    "⚠️":            "🔴" if err_rate > 0.2 or v["avg_latency_ms"] > 30000 else "",
                })
            df24 = pd.DataFrame(rows)
            st.dataframe(df24, use_container_width=True)

            # 要改善エージェントをハイライト
            problems = [r for r in rows if r["⚠️"]]
            if problems:
                st.warning(f"**自動改善対象**: {', '.join(r['エージェント'] for r in problems)}  "
                           f"（エラー率>20% または 平均レイテンシ>30s → 次回 mempalace_maintenance で自動改善）")
        style.section_card_end()

        # 7日間サマリー
        if s7d and not s7d.get("error"):
            style.section_card_start("📅 直近7日間サマリー", "", "ok")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("総呼び出し(7d)", s7d.get("total", 0))
            c2.metric("エラー(7d)",     s7d.get("errors", 0))
            c3.metric("平均レイテンシ(7d)", f"{s7d.get('avg_latency_ms', 0):,} ms")
            c4.metric("合計コスト(7d)", f"${s7d.get('total_cost_usd', 0):.4f}")

            by_agent_7d = s7d.get("by_agent", {})
            if by_agent_7d:
                rows7 = []
                for ag, v in by_agent_7d.items():
                    err_rate = v["errors"] / v["count"] if v["count"] else 0
                    rows7.append({
                        "エージェント": ag,
                        "呼び出し回数": v["count"],
                        "平均レイテンシ(ms)": v["avg_latency_ms"],
                        "エラー率": f"{err_rate:.0%}",
                        "コスト($)": f"{v['cost_usd']:.5f}",
                    })
                st.dataframe(pd.DataFrame(rows7), use_container_width=True)
            style.section_card_end()
