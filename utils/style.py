"""全ページ共通のUIスタイル。各ページ冒頭で inject() を呼ぶ。"""
import streamlit as st

# ダークテーマに合わせたカード・バッジ・テーブルの統一スタイル
GLOBAL_CSS = """
<style>
    /* ── 余白・最大幅 ───────────────────────────────── */
    .block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1400px; }

    /* ── メトリクスカード（st.metric を枠付きカード化） ─ */
    div[data-testid="stMetric"] {
        background: #161b26;
        border: 1px solid #2a3140;
        border-radius: 10px;
        padding: 14px 16px;
    }
    div[data-testid="stMetricValue"] { font-size: 1.9rem; font-weight: 700; }
    div[data-testid="stMetricLabel"] p { font-size: 0.82rem; color: #9aa4b2; }

    /* ── タブ ───────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        font-size: 14px;
        padding: 8px 16px;
        border-radius: 8px 8px 0 0;
    }
    .stTabs [aria-selected="true"] { background: #1c2430; }

    /* ── エクスパンダー ─────────────────────────────── */
    div[data-testid="stExpander"] {
        border: 1px solid #2a3140;
        border-radius: 10px;
    }

    /* ── データフレーム角丸 ─────────────────────────── */
    div[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }

    /* ── ステータスバッジ（マークダウンで使用） ───────── */
    .status-green  { color: #A6E3A1; font-weight: 700; }
    .status-red    { color: #F38BA8; font-weight: 700; }
    .status-yellow { color: #F9E2AF; font-weight: 700; }

    /* ── ページ見出し下のキャプション余白調整 ─────────── */
    h1 { padding-bottom: 0.2rem; }
</style>
"""


def inject():
    """共通CSSをページに適用する。"""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", updated: str = ""):
    """統一されたページ見出し（タイトル＋サブ＋最終更新）を描画する。"""
    inject()
    st.title(title)
    parts = []
    if subtitle:
        parts.append(subtitle)
    if updated:
        parts.append(f"最終更新: {updated}")
    if parts:
        st.caption("　｜　".join(parts))
