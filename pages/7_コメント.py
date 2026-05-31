import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader, firebase_client

st.set_page_config(page_title="コメント", page_icon="💬", layout="wide")
st_autorefresh(interval=60_000, key="comments_refresh")
st.title("💬 ダッシュボードコメント")

data = data_loader.comments()
comment_list = data.get("comments", [])
total = data.get("total", 0)
real_count = data.get("real_count", 0)
last_upd = data.get("last_updated", "")

st.caption(f"総コメント数: {total:,} 件  ｜  実コメント: {real_count} 件  ｜  最終更新: {last_upd[:16]}")
st.caption("※ AI返信は自律ループが自動生成します。")

# ── 新規コメント投稿 ──────────────────────────────────────────────────────────
with st.expander("✏️ 新規コメントを投稿", expanded=False):
    with st.form("new_comment_form", clear_on_submit=True):
        nc_title   = st.text_input("タイトル（件名）", placeholder="例: パイプラインの異常について")
        nc_section = st.text_input("セクション", placeholder="例: パイプライン, タスク, ビジネス")
        nc_comment = st.text_area("コメント内容 *", placeholder="内容を入力してください", height=100)
        nc_submit  = st.form_submit_button("📨 投稿する", use_container_width=True)
        if nc_submit:
            if not nc_comment.strip():
                st.error("コメント内容を入力してください")
            else:
                now = datetime.now().isoformat()
                doc_id = f"comment_{datetime.now().timestamp():.0f}"
                new_c = {
                    "id":           doc_id,
                    "item_title":   nc_title or "（無題）",
                    "section":      nc_section or "general",
                    "user_comment": nc_comment.strip(),
                    "ai_reply":     "",
                    "timestamp":    now,
                    "status":       "pending",
                    "source":       "streamlit",
                }
                ok = firebase_client.patch_doc("dashboard_comments", doc_id, new_c)
                if ok:
                    st.success("✅ 投稿しました。AI返信は自律ループが自動生成します。")
                    st.rerun()
                else:
                    st.error("❌ 投稿に失敗しました")

st.divider()

# ── フィルター ────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    status_f = st.selectbox("ステータス", ["すべて", "pending", "resolved"])
with col2:
    kw = st.text_input("キーワード検索", placeholder="コメント内容・タイトル")

filtered = comment_list
if status_f != "すべて":
    filtered = [c for c in filtered if c.get("status") == status_f]
if kw:
    kw_l = kw.lower()
    filtered = [c for c in filtered
                if kw_l in (c.get("user_comment", "") + c.get("item_title", "")).lower()]

st.caption(f"表示中: {len(filtered)} 件（最新100件から）")

# ── コメント一覧（新しい順） ──────────────────────────────────────────────────
for c in reversed(filtered):
    ts        = c.get("timestamp", "")[:16]
    title     = c.get("item_title", "（無題）")
    section   = c.get("section", "")
    comment   = c.get("user_comment", "")
    reply     = c.get("ai_reply", "")
    status    = c.get("status", "")
    s_icon    = "✅" if status == "resolved" else "🟡"

    with st.expander(f"{s_icon} **{title}** — {ts}  ｜  {section}", expanded=False):
        st.markdown(f"**💬 コメント:** {comment}")
        if reply:
            st.success(f"**🤖 AI返信:** {reply}")
        else:
            st.caption("（AI返信待ち）")
        col1, col2 = st.columns(2)
        with col1: st.caption(f"ステータス: {status}")
        with col2: st.caption(f"投稿日時: {ts}")
