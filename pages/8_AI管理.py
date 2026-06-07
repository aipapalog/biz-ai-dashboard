import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, style

st.set_page_config(page_title="🧠 AI管理", page_icon="🧠", layout="wide")
style.inject()

style.page_header("🧠 AI管理", updated=data_loader.last_updated())

tab_mem, tab_lv, tab_rule, tab_obsidian, tab_ctx, tab_learn, tab_outputs = st.tabs([
    "🧠 mempalace × Obsidian", "🚀 レベルアップ", "⚙️ ルールエンジン",
    "📖 エージェント体制", "📋 Sync/ai コンテキスト", "🛡️ 4層学習システム", "📦 生成物一覧"
])

# ── mempalace × Obsidian ──────────────────────────────────────────────────────
with tab_mem:
    style.section_card_start("🧠 mempalace ナレッジ成長（直近14日）")
    mem = data_loader.mempalace()
    if mem:
        rows    = mem.get("rows", [])
        if rows:
            import pandas as pd
            df_m = pd.DataFrame(rows)
            last = rows[-1] if rows else {}
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("ルーム数",      last.get("rooms", "-"))
            with c2: st.metric("エンティティ数", last.get("entities", "-"))
            with c3: st.metric("トリプル数",     last.get("triples", "-"))
            style.section_title("📊 mempalace成長推移")
            if "date" in df_m.columns:
                num_cols = [c for c in df_m.columns if c != "date"]
                try:
                    for c in num_cols: df_m[c] = pd.to_numeric(df_m[c], errors="coerce")
                    st.line_chart(df_m.set_index("date")[num_cols])
                except Exception: pass
            st.dataframe(df_m, use_container_width=True)
    else:
        st.info("mempalaceデータがありません")
    style.section_card_end()

    style.section_card_start("📦 mempalace ルーム別ナレッジ分布")
    rooms_data = data_loader.mempalace_rooms()
    if rooms_data:
        rooms      = rooms_data.get("rooms", {})
        latest_date = rooms_data.get("latest_date", "")
        history    = rooms_data.get("history", [])
        st.caption(f"最終更新: {latest_date}")
        if rooms:
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
            total = sum(rooms.values()) if rooms else 0
            cols = st.columns(min(len(rooms), 4))
            for i, (room, cnt) in enumerate(sorted(rooms.items(), key=lambda x: -x[1])):
                pct   = (cnt / total * 100) if total else 0
                label = ROOM_LABELS.get(room, room)
                icon  = ROOM_COLORS.get(room, "⬜")
                with cols[i % 4]:
                    st.metric(f"{icon} {label}", cnt, help=f"{pct:.1f}%")
            st.progress(1.0, text=f"合計 {total} ドロワー")

            issues = []
            if rooms.get("general", 0) / max(total, 1) > 0.8:
                issues.append("⚠️ general集中度が高い — 製品/戦略/学習カテゴリへの再分類を推奨")
            for room in ("products", "strategy", "lessons"):
                if rooms.get(room, 0) < 5:
                    issues.append(f"⚠️ {ROOM_LABELS.get(room, room)}が{rooms.get(room,0)}件のみ — 構造化ナレッジを優先追加")
            for iss in issues[:3]:
                st.warning(iss)

            if history:
                import pandas as pd
                style.section_title("📅 ルーム別ドロワー数推移（直近14日）")
                df_hist = pd.DataFrame(history)
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

    obs = data_loader.obsidian_stats()
    if obs:
        o1, o2 = st.columns(2)
        o1.metric("📝 総ノート数", obs.get("total_notes", 0))
        o2.metric("🆕 直近14日追加", obs.get("recent_14d", 0))
        folders = obs.get("folders", {})
        if folders:
            style.section_title("📁 Vault フォルダ構成")
            rows = [{"フォルダ": k, "件数": v} for k, v in sorted(folders.items(), key=lambda x: -x[1])]
            import pandas as pd
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    style.section_title("📁 フォルダ構成")
    cols = st.columns(3)
    for i, (folder, icon, desc) in enumerate(OBSIDIAN_FOLDERS):
        with cols[i % 3]:
            st.markdown(f"{icon} **{folder}**  \n{desc}")
    style.section_card_end()

# ── レベルアップ ──────────────────────────────────────────────────────────────
with tab_lv:
    style.section_card_start("🚀 エージェント レベルアップ状況")
    status = data_loader.levelup_status()
    if status:
        if isinstance(status, dict):
            for key, val in status.items():
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
    history = data_loader.levelup_history()
    if history:
        for h in sorted(history, key=lambda x: x.get("date",""), reverse=True):
            date    = h.get("date", "?")
            content = h.get("content", "")
            with st.expander(f"📅 {date}", expanded=False):
                if content: st.markdown(content[:2000])
    else:
        st.info("レベルアップ履歴がありません")
    style.section_card_end()

# ── ルールエンジン ────────────────────────────────────────────────────────────
with tab_rule:
    rule   = data_loader.rule_engine()
    style.section_card_start("⚙️ ルールエンジン状態")
    if rule:
        r1, r2, r3 = st.columns(3)
        with r1: st.metric("🪝 フック数",      rule.get("hook_count", 0))
        with r2: st.metric("✅ 許可ルール数",   rule.get("allow_count", 0))
        with r3: st.metric("🔒 デフォルトモード", rule.get("default_mode", "-"))
        st.caption(f"最終更新: {rule.get('updated_at','')[:16]}")
        hook_types = rule.get("hook_types", [])
        if hook_types:
            style.section_title("🪝 登録フック")
            for ht in hook_types: st.write(f"• **{ht}**")
    else:
        st.info("ルールエンジンデータがありません")
    style.section_card_end()

    style.section_card_start("📋 主要ルール（CLAUDE.mdより）")
    rules = [
        ("🔴 会社NW接続時は完全停止",     "SWing/SWingS 検出→全ツール停止"),
        ("🔴 自動化スクリプトでOpus禁止",  "claude-haiku-4-5 推奨。Opusは自動化禁止"),
        ("🔴 subprocess.run直接禁止",       "safe_run/safe_popen に差し替え必須"),
        ("🔴 AtLogonトリガー禁止",          "BSOD防止。21:00〜21:30の定時スケジューラのみ"),
        ("🔴 Microsoft Store禁止",          "管理者権限なし。pip/scoopを使う"),
        ("🔴 新規スクリプトはclaude -pのみ","APIクレジット消費禁止。CLIは無料"),
        ("🟡 Haiku委譲（閾値9）",           "スコア≤9のタスクは全てHaiku"),
        ("🟡 ダッシュボードはpython実行必須","mdファイル書き込み≠ダッシュボード反映"),
        ("🟡 新規スクリプト追加は会長明示指示のみ","システムシンプル化原則"),
    ]
    for rule_name, desc in rules:
        st.markdown(f"**{rule_name}**  \n　{desc}")
    style.section_card_end()

# ── エージェント体制サマリー ──────────────────────────────────────────────────
with tab_obsidian:
    agents_ctx = data_loader.agents_context()
    insights   = data_loader.agent_insights()
    style.section_card_start("📖 エージェント体制・施策サマリー")
    if agents_ctx.get("content"):
        st.markdown(agents_ctx["content"])
    else:
        st.info("エージェントコンテキストがありません")

    patterns = insights.get("success_patterns", {}) if insights else {}
    if patterns:
        style.section_title("🌟 成功パターンライブラリ")
        for cat, items in patterns.items():
            if not isinstance(items, list): continue
            with st.expander(f"**{cat}** （{len(items)}件）"):
                for item in items[-5:]:
                    if isinstance(item, dict):
                        score   = item.get("score", 0)
                        summary = item.get("summary", "")
                        ts      = (item.get("ts") or "")[:10]
                        color   = "🟢" if score >= 8 else "🟡" if score >= 6 else "🔴"
                        st.write(f"{color} {ts} スコア{score}: {summary[:100]}")
    style.section_card_end()

# ── Sync/ai コンテキスト ───────────────────────────────────────────────────────
with tab_ctx:
    brain = data_loader.sync_brain()
    tasks = data_loader.sync_tasks()
    ll    = data_loader.lessons_learned()

    style.section_card_start("📋 Sync/ai コンテキスト")
    st.caption(f"最終更新: {brain.get('updated_at', '')[:16]}")

    sub_now, sub_so, sub_ctx, sub_me, sub_brand, sub_oss, sub_ll = st.tabs([
        "🟢 now.md", "📌 Standing Orders", "🧩 コンテキスト",
        "👤 me.md", "🎨 brand_memory", "🏗️ OSS移行計画", "📚 lessons_learned"
    ])

    with sub_now:
        now_content = brain.get("now", "")
        if now_content:
            st.markdown(now_content)
        else:
            st.info("now.mdデータがありません。firebase_dashboard_pusher.pyを実行してください。")

    with sub_so:
        so_content = tasks.get("standing_orders", "")
        if so_content:
            st.markdown(so_content)
        else:
            st.info("standing_ordersデータがありません。")

    with sub_ctx:
        ctx_content = tasks.get("claude_context", "")
        ws          = tasks.get("work_status", {})
        if ctx_content:
            st.markdown(ctx_content)
        if ws:
            style.section_title("📊 work_status")
            for k, v in ws.items():
                st.write(f"**{k}:** {v}")

    with sub_me:
        me_content = brain.get("me", "")
        if me_content:
            st.markdown(me_content)
        else:
            st.info("me.mdデータがありません。")

    with sub_brand:
        brand_content = brain.get("brand_memory", "")
        if brand_content:
            st.markdown(brand_content)
        else:
            st.info("brand_memoryデータがありません。")

    with sub_oss:
        oss_content = brain.get("oss_migration_plan", "")
        if oss_content:
            st.markdown(oss_content)
        else:
            st.info("OSS移行計画データがありません。")

    with sub_ll:
        ll_content = ll.get("content", "")
        if ll_content:
            st.markdown(ll_content)
        else:
            st.info("lessons_learnedデータがありません。")
    style.section_card_end()

# ── 4層学習システム ───────────────────────────────────────────────────────────
with tab_learn:
    ls = data_loader.learning_system()
    style.section_card_start("🛡️ エラー再発防止・自律学習システム：4層の多層防御")
    st.caption("失敗パターンの再発を防止 + 自律学習フィードバック実装")

    if ls:
        active_count = ls.get("active_count", 0)
        total        = ls.get("total", 4)
        overall      = ls.get("overall", "")
        flow         = ls.get("flow", "")

        c1, c2 = st.columns(2)
        c1.metric("有効レイヤー", f"{active_count}/{total}層",
                  delta="正常" if active_count == total else f"⚠ {total - active_count}層未設定")
        c2.markdown(f"**全体状態:** {overall}")

        layers = ls.get("layers", [])
        for la in layers:
            icon        = "🟢" if la.get("active") else "⚪"
            status_tag  = f"✓ {la['status']}" if la.get("active") else la["status"]
            with st.expander(f"{icon} **Layer {la['layer']}: {la['name']}** — {status_tag}", expanded=la.get("active", False)):
                st.markdown(f"**コンポーネント:** {la.get('components','')}")
                st.markdown(f"**動作内容:** {la.get('desc','')}")
                st.markdown(f"**ステータス:** `{la.get('status','')}`")

        st.markdown(f"**学習フロー:** {flow}")
        st.caption(f"最終更新: {ls.get('updated_at','')[:16]}")
    else:
        st.info("学習システムデータがありません。firebase_dashboard_pusher.pyを実行してください。")
    style.section_card_end()

# ── 生成物一覧 ─────────────────────────────────────────────────────────────────
with tab_outputs:
    outputs = data_loader.sync_outputs()
    style.section_card_start("📦 Sync/ai/outputs/ 生成物一覧")

    if outputs:
        files = outputs.get("files", [])
        total = outputs.get("total", 0)
        st.caption(f"合計 {total} ファイル（最新40件表示）| 最終更新: {outputs.get('updated_at','')[:16]}")

        if files:
            import pandas as pd
            EXT_ICON = {".md": "📝", ".json": "📊", ".txt": "📄"}
            df = pd.DataFrame([{
                "種類": EXT_ICON.get(f["ext"], "📁"),
                "ファイル名": f["name"],
                "サイズ(KB)": f["size_kb"],
                "更新日": f["modified"],
            } for f in files])
            st.dataframe(df, use_container_width=True, hide_index=True)

            note_files = [f for f in files if f["name"].startswith("note_")]
            kdp_files  = [f for f in files if f["name"].startswith("kdp_") or f["name"].startswith("chapter")]
            x_files    = [f for f in files if f["name"].startswith("x_")]

            cols = st.columns(3)
            cols[0].metric("📝 note下書き", len(note_files))
            cols[1].metric("📚 KDP原稿", len(kdp_files))
            cols[2].metric("🐦 X投稿", len(x_files))
    else:
        st.info("生成物データがありません。firebase_dashboard_pusher.pyを実行してください。")
    style.section_card_end()
