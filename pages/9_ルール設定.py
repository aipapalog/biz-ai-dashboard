import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader

st.set_page_config(page_title="ルール・設定", page_icon="⚙️", layout="wide")
st_autorefresh(interval=120_000, key="rule_refresh")
st.title("⚙️ ルールエンジン・設定・トークン管理")

rule = data_loader.rule_engine()
budget = data_loader.api_budget()
sys_info = data_loader.system_info()

tab1, tab2, tab3 = st.tabs(["🔧 ルールエンジン状態", "💰 API・トークン管理", "🌐 ネットワーク詳細"])

# ── ルールエンジン状態 ────────────────────────────────────────────────────────
with tab1:
    st.subheader("🔧 ルールエンジン状態")
    if rule:
        r1, r2, r3 = st.columns(3)
        with r1: st.metric("🪝 フック数",     rule.get("hook_count", 0))
        with r2: st.metric("✅ 許可ルール数",  rule.get("allow_count", 0))
        with r3: st.metric("🔒 デフォルトモード", rule.get("default_mode", "-"))
        st.caption(f"最終更新: {rule.get('updated_at','')[:16]}")

        hook_types = rule.get("hook_types", [])
        if hook_types:
            st.subheader("🪝 登録フック")
            for ht in hook_types:
                st.write(f"• **{ht}**")
    else:
        st.info("ルールエンジンデータがありません")

    st.divider()
    st.subheader("📋 主要ルール（CLAUDE.mdより）")
    rules = [
        ("🔴 会社NW接続時は完全停止", "SWing/SWingS 検出→全ツール停止"),
        ("🔴 自動化スクリプトでOpus禁止", "claude-haiku-4-5 推奨。Opusは自動化禁止"),
        ("🔴 subprocess.run/Popen直接禁止", "safe_run/safe_popen に差し替え必須"),
        ("🔴 AtLogonトリガー禁止", "BSOD防止。21:00〜21:30の定時スケジューラのみ"),
        ("🔴 Microsoft Store禁止", "管理者権限なし。pip/scoopを使う"),
        ("🔴 新規スクリプトはclaude -pのみ", "APIクレジット消費禁止。CLIは無料"),
        ("🟡 Haiku委譲（閾値9）", "ファイル読み込み・検索・ログ解析は全てHaikuへ"),
        ("🟡 ダッシュボードはpython実行必須", "mdファイル書き込み≠ダッシュボード反映"),
        ("🟡 新規スクリプト追加は会長明示指示のみ", "システムシンプル化原則"),
        ("🟡 to_verify 3日超過→open自動リサイクル", "蓄積防止"),
    ]
    for rule_name, desc in rules:
        st.markdown(f"**{rule_name}**  \n　{desc}")

# ── API・トークン管理 ─────────────────────────────────────────────────────────
with tab2:
    st.subheader("💰 API・トークン使用上限到達回避策")
    if budget:
        providers = [(k, v) for k, v in budget.items() if isinstance(v, dict)]
        if providers:
            for name, info in providers:
                used  = info.get("used_usd", 0)
                limit = info.get("budget_usd", 0)
                pct   = (used / limit * 100) if limit else 0
                st.progress(min(pct / 100, 1.0),
                            text=f"{name}: ${used:.3f} / ${limit:.2f}  ({pct:.1f}%)")
        else:
            used  = budget.get("used_usd", 0)
            limit = budget.get("budget_usd", 0)
            pct   = (used / limit * 100) if limit else 0
            st.progress(min(pct / 100, 1.0),
                        text=f"API消費: ${used:.3f} / ${limit:.2f}  ({pct:.1f}%)")

    st.divider()
    st.subheader("📋 トークン使用上限到達回避策")
    strategies = [
        ("✅ Haiku委譲（閾値9）", "スコア≤9のタスクは全てHaiku。Sonnetは複雑実装のみ"),
        ("✅ WebSearch/WebFetch は Haiku 限定", "HTML全文がコンテキストに積まれるのを防ぐ"),
        ("✅ 同一ファイルを2回読まない", "初回読み込みで記憶。以降はメモリ参照"),
        ("✅ バッチ委譲原則", "複数確認作業は1回のHaiku agentにまとめる"),
        ("✅ コードブロック全体を出力しない", "変更差分と結果だけ伝える"),
        ("✅ 1セッション5〜8タスクまで", "それ以上はnow.mdに記録して次セッションへ"),
        ("✅ claude -p でAPI無消費", "自動化スクリプトはCLI経由でクレジット消費ゼロ"),
    ]
    for name, desc in strategies:
        st.markdown(f"**{name}**  \n　{desc}")

    st.divider()
    st.subheader("📊 1日の判断回数と削減案")
    st.info("decisions_log.json は未生成（パイプライン未稼働）。以下は設計値です。")
    decisions = [
        ("確認不要（即実行）", "ローカルファイル操作・Python実行・タスクスケジューラ・ブラウザ操作"),
        ("確認必要", "git push・外部サービス送信・決済・ファイル一括削除（10件以上）"),
        ("自律クローズ", "会長起票でない・リスクなし・完了済みの条件を全て満たすタスク"),
        ("削減策", "タスク一括承認ルール: タスク内の個々ステップは追加確認なし"),
    ]
    for name, desc in decisions:
        with st.expander(f"**{name}**"):
            st.write(desc)

# ── ネットワーク詳細 ──────────────────────────────────────────────────────────
with tab3:
    st.subheader("🌐 ネットワーク状況詳細")
    if sys_info:
        ssid = sys_info.get("ssid", "不明")
        is_company = "SWing" in ssid or "SWingS" in ssid

        n1, n2 = st.columns(2)
        with n1:
            icon = "🏢" if is_company else "🏠"
            st.metric(f"{icon} 接続NW", ssid)
            if is_company:
                st.error("⛔ 会社ネットワーク検出 — Claude動作停止中")
            else:
                st.success("✅ 私用ネットワーク — 正常動作中")
        with n2:
            st.write("**ネットワーク判定ルール:**")
            st.write("• SSID に `SWing` または `SWingS` → 会社NW → 完全停止")
            st.write("• IP 上位が `43.` → 会社NW → 完全停止")
            st.write("• それ以外 → 私用NW → 通常動作")

        st.divider()
        st.subheader("🖥️ システムリソース詳細")
        s1, s2, s3, s4 = st.columns(4)
        with s1: st.metric("CPU",    f"{sys_info.get('cpu_percent',0):.1f}%")
        with s2: st.metric("メモリ", f"{sys_info.get('memory_percent',0):.1f}%")
        with s3:
            d_p = sys_info.get("disk_percent", 0)
            d_u = sys_info.get("disk_used_gb", 0)
            d_t = sys_info.get("disk_total_gb", 0)
            st.metric("ディスク(C:)", f"{d_p:.0f}%", help=f"{d_u}GB / {d_t}GB")
        with s4:
            bat = sys_info.get("battery_percent", 0)
            chg = sys_info.get("charging", False)
            st.metric("バッテリー", f"{bat}%" + (" ⚡" if chg else ""))
    else:
        st.info("システム情報がありません")
