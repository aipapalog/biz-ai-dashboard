import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, style

st.set_page_config(page_title="😊 CX・品質", page_icon="😊", layout="wide")
style.inject()
st.title("😊 CX・品質・リスク")

tab_cx, tab_risk, tab_health, tab_token, tab_comments = st.tabs([
    "🎯 顧客体験(CX)", "⚠️ リスク", "🩺 ヘルスチェック", "🪙 トークン管理", "💬 コメント"
])

# ── CX ────────────────────────────────────────────────────────────────────────
with tab_cx:
    cx = data_loader.cx_report()
    st.subheader("🎯 顧客体験（CX）分析レポート")
    if cx:
        st.caption(f"📅 {cx.get('date','')}  ｜  🔄 {cx.get('updated_at','')[:16]}")
        content = cx.get("content", "")
        if content: st.markdown(content[:3000])
    else:
        st.info("CXレポートがありません。cx_improverパイプライン実行後に更新されます。")

# ── リスク ────────────────────────────────────────────────────────────────────
with tab_risk:
    risk = data_loader.risk_report()
    st.subheader("⚠️ リスク評価レポート")
    if risk:
        st.caption(f"📅 {risk.get('date','')}  ｜  🔄 {risk.get('updated_at','')[:16]}")
        content = risk.get("content", "")
        if "HIGH" in (content or "").upper():
            st.error("🔴 Highリスクあり")
        if content: st.markdown(content[:3000])
    else:
        st.info("リスクレポートがありません。risk_managerパイプライン実行後に更新されます。")

# ── ヘルスチェック ────────────────────────────────────────────────────────────
with tab_health:
    health = data_loader.health_check()
    code_health = data_loader.code_health()
    st.subheader("🩺 エージェント・パイプライン健全性")
    if health:
        st.caption(f"📅 {health.get('date','')}  ｜  🔄 {health.get('updated_at','')[:16]}")
        content = health.get("content", "")
        if content:
            with st.expander("ヘルスチェック詳細", expanded=True):
                st.markdown(content[:2000])
    else:
        st.info("ヘルスチェックデータがありません")

    if code_health:
        st.subheader("🔍 コードヘルス")
        date = (code_health.get("generated_at") or code_health.get("date") or "")[:10]
        st.caption(f"最終チェック: {date}")
        issues = code_health.get("issues", [])
        highs  = [x for x in issues if isinstance(x,dict) and x.get("severity") in ("high","critical")]
        mids   = [x for x in issues if isinstance(x,dict) and x.get("severity") == "medium"]
        lc1, lc2, lc3 = st.columns(3)
        with lc1: st.metric("🔴 高度",  len(highs))
        with lc2: st.metric("🟡 中度",  len(mids))
        with lc3: st.metric("📁 総件数", len(issues))
        for iss in highs[:5]:
            st.warning(f"**{iss.get('file','?')}** — {iss.get('message','')}")

# ── トークン管理 ──────────────────────────────────────────────────────────────
with tab_token:
    budget = data_loader.api_budget()
    st.subheader("🪙 トークン使用上限到達回避策")
    if budget:
        providers = [(k, v) for k, v in budget.items() if isinstance(v, dict)]
        if providers:
            for name, info in providers:
                used  = info.get("used_usd", 0)
                limit = info.get("budget_usd", 0)
                pct   = (used / limit * 100) if limit else 0
                st.progress(min(pct / 100, 1.0), text=f"{name}: ${used:.3f} / ${limit:.2f}  ({pct:.1f}%)")
        else:
            used  = budget.get("used_usd", 0)
            limit = budget.get("budget_usd", 0)
            pct   = (used / limit * 100) if limit else 0
            st.progress(min(pct / 100, 1.0), text=f"API消費: ${used:.3f} / ${limit:.2f}  ({pct:.1f}%)")
    strategies = [
        ("✅ Haiku委譲（閾値9）",           "スコア≤9のタスクは全てHaiku。Sonnetは複雑実装のみ"),
        ("✅ WebSearch/WebFetch はHaiku限定", "HTML全文がコンテキストに積まれるのを防ぐ"),
        ("✅ 同一ファイルを2回読まない",     "初回読み込みで記憶。以降はメモリ参照"),
        ("✅ バッチ委譲原則",                "複数確認作業は1回のHaiku agentにまとめる"),
    ]
    st.markdown("**1日の判断回数削減策:**")
    for s, d in strategies:
        st.markdown(f"**{s}**  \n　{d}")

# ── コメント ──────────────────────────────────────────────────────────────────
with tab_comments:
    from datetime import datetime
    from utils import firebase_client
    data = data_loader.comments()
    comment_list = data.get("comments", [])
    total = data.get("total", 0)
    real_count = data.get("real_count", 0)
    last_upd = data.get("last_updated", "")
    st.subheader("💬 ダッシュボードコメント")
    st.caption(f"総コメント数: {total:,} 件  ｜  実コメント: {real_count} 件  ｜  最終更新: {last_upd[:16] if last_upd else '-'}")
    st.caption("※ AI返信は自律ループが自動生成します。")

    with st.expander("✏️ 新規コメントを投稿", expanded=False):
        with st.form("new_comment_form", clear_on_submit=True):
            nc_title   = st.text_input("タイトル（件名）")
            nc_section = st.text_input("セクション", placeholder="例: CX, タスク, ビジネス")
            nc_comment = st.text_area("コメント内容 *", height=80)
            if st.form_submit_button("📨 投稿する", use_container_width=True):
                if not nc_comment.strip():
                    st.error("コメント内容を入力してください")
                else:
                    now = datetime.now().isoformat()
                    doc_id = f"comment_{datetime.now().timestamp():.0f}"
                    new_c = {"id": doc_id, "item_title": nc_title or "（無題）", "section": nc_section or "general", "user_comment": nc_comment.strip(), "ai_reply": "", "timestamp": now, "status": "pending", "source": "streamlit"}
                    ok = firebase_client.patch_doc("dashboard_comments", doc_id, new_c)
                    if ok:
                        st.success("✅ 投稿しました。AI返信は自律ループが自動生成します。"); st.rerun()
                    else:
                        st.error("❌ 投稿に失敗しました（Firebase接続を確認）")

    if comment_list:
        for c in reversed(comment_list[-20:]):
            if not isinstance(c, dict): continue
            ts    = (c.get("timestamp") or "")[:16]
            title = c.get("item_title", "")
            sec   = c.get("section", "")
            user  = c.get("user_comment", "")
            ai    = c.get("ai_reply", "")
            with st.expander(f"💬 {ts}  [{sec}] {title[:40]}"):
                st.write(f"👤 **ユーザー:** {user}")
                if ai: st.write(f"🤖 **AI返信:** {ai}")
    else:
        st.info("コメントがありません")
