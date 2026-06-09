"""全ページ共通のUIスタイル。各ページ冒頭で inject() を呼ぶ。freshness_banner()で鮮度バナーを表示。"""
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
    div[data-testid="stMetricValue"] { font-size: 1.45rem; font-weight: 700; line-height: 1.3; }
    div[data-testid="stMetricLabel"] p { font-size: 0.75rem; color: #9aa4b2; white-space: normal !important; word-break: keep-all; line-height: 1.35; }

    /* ── KPI 優先度カラー（左ボーダーで重要度を表現） ───
       使い方: 親 div に kpi-* クラスを当てた上で内部の st.metric を着色する。
       Streamlit の DOM 制約上、対象 metric を kpi-* クラスの要素で包む。 */
    .kpi-critical div[data-testid="stMetric"] { border-left: 4px solid #f38ba8; }
    .kpi-warn     div[data-testid="stMetric"] { border-left: 4px solid #f9e2af; }
    .kpi-ok       div[data-testid="stMetric"] { border-left: 4px solid #a6e3a1; }
    .kpi-info     div[data-testid="stMetric"] { border-left: 4px solid #89dceb; }

    /* ── セクションカード（セクションを丸角ボーダーで囲う）─ */
    .section-card {
        background: #161b26;
        border: 1px solid #2a3140;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 18px;
    }
    /* section-card の直後に続く Streamlit 要素群を視覚的に内包させる余白 */
    .section-card + div[data-testid="stVerticalBlock"] { margin-top: -6px; }

    /* ── セクションタイトル ─────────────────────────── */
    .section-title {
        font-size: 1.05rem;
        color: #9aa4b2;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 700;
        margin: 4px 0 10px 0;
    }
    /* カード内タイトル（バッジと横並び） */
    .section-card-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
    }
    .section-card-head .section-title { margin: 0; }

    /* ── ステータスバッジ ───────────────────────────── */
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 700;
        line-height: 1.2;
        white-space: nowrap;
    }
    .badge-ok   { background: #1e3a2f; color: #a6e3a1; }
    .badge-warn { background: #3a3010; color: #f9e2af; }
    .badge-err  { background: #3a1010; color: #f38ba8; }
    .badge-info { background: #101e3a; color: #89dceb; }

    /* ── テーブル行（パイプライン一覧など） ───────────── */
    .trow {
        display: flex;
        gap: 8px;
        align-items: center;
        padding: 6px 0;
        border-bottom: 1px solid #2a3140;
        font-size: 0.9rem;
    }
    .trow-head {
        color: #9aa4b2;
        font-size: 0.76rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border-bottom: 1px solid #3a4150;
    }
    .trow .c-icon { width: 26px; text-align: center; }
    .trow .c-name { flex: 3; font-weight: 600; }
    .trow .c-time { flex: 2; color: #9aa4b2; }
    .trow .c-stat { flex: 1.4; text-align: left; }
    .trow .c-tok  { flex: 1.6; color: #9aa4b2; text-align: right; }

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

    /* ── ステータスバッジ（旧マークダウン用・後方互換） ─ */
    .status-green  { color: #A6E3A1; font-weight: 700; }
    .status-red    { color: #F38BA8; font-weight: 700; }
    .status-yellow { color: #F9E2AF; font-weight: 700; }

    /* ── ページ見出し（大きすぎるデフォルトh1を抑制）─── */
    h1 { font-size: 1.45rem !important; font-weight: 700; letter-spacing: -0.02em; padding-bottom: 0.3rem; color: #e2e8f0; }
    h2 { font-size: 1.15rem !important; font-weight: 600; color: #cdd6f4; }
    h3 { font-size: 1.0rem !important; font-weight: 600; color: #cdd6f4; }

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
</style>
"""

# status引数 → バッジクラスの対応表
_BADGE_CLASS = {
    "ok":   "badge-ok",
    "warn": "badge-warn",
    "err":  "badge-err",
    "info": "badge-info",
}


def inject():
    """共通CSSをページに適用する。"""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def _badge_html(text: str, status: str = "info") -> str:
    """バッジHTML片を返す（text空なら空文字）。"""
    if not text:
        return ""
    cls = _BADGE_CLASS.get(status, "badge-info")
    return f'<span class="badge {cls}">{text}</span>'


def page_header(title: str, subtitle: str = "", updated: str = "", status: str = ""):
    """統一されたページ見出し（タイトル＋サブ＋最終更新＋右端ステータスバッジ）。

    status: "ok"/"warn"/"err"/"info" を渡すとタイトル右端にバッジを描画する。
    """
    inject()
    badge = _badge_html(status.upper(), status) if status in _BADGE_CLASS else ""
    if badge:
        # タイトルとバッジを横並びにする
        st.markdown(
            f'<div style="display:flex;align-items:center;justify-content:space-between;">'
            f'<h1 style="margin:0;">{title}</h1>{badge}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.title(title)
    parts = []
    if subtitle:
        parts.append(subtitle)
    if updated:
        parts.append(f"最終更新: {updated}")
    if parts:
        st.caption("　｜　".join(parts))


def section_card_start(title: str = "", badge_text: str = "", badge_status: str = "info"):
    """セクションカードの開始タグを描画する（タイトル・バッジ付き）。

    context manager ではなく、開始・終了タグを別々に出す関数として実装。
    使い方:
        style.section_card_start("タイトル", "OK", "ok")
        ... st.metric などのコンテンツ ...
        style.section_card_end()
    """
    badge = _badge_html(badge_text, badge_status)
    head = ""
    if title or badge:
        head = (
            '<div class="section-card-head">'
            f'<div class="section-title">{title}</div>{badge}'
            '</div>'
        )
    st.markdown(f'<div class="section-card">{head}', unsafe_allow_html=True)


def section_card_end():
    """セクションカードの終了タグを描画する。"""
    st.markdown('</div>', unsafe_allow_html=True)


def section_title(title: str):
    """カードを使わずセクションタイトルだけ描画する。"""
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


def kpi_wrap_start(priority: str = "info"):
    """st.metric を優先度カラーで囲む開始タグ。priority: critical/warn/ok/info。"""
    cls = {"critical": "kpi-critical", "warn": "kpi-warn",
           "ok": "kpi-ok", "info": "kpi-info"}.get(priority, "kpi-info")
    st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)


def kpi_wrap_end():
    """kpi_wrap_start の終了タグ。"""
    st.markdown('</div>', unsafe_allow_html=True)


def trow(icon: str, name: str, time: str, status_text: str,
         status_class: str = "badge-info", token: str = ""):
    """パイプライン一覧などの1行（.trow）を描画する。"""
    badge = f'<span class="badge {status_class}">{status_text}</span>' if status_text else ""
    st.markdown(
        f'<div class="trow">'
        f'<div class="c-icon">{icon}</div>'
        f'<div class="c-name">{name}</div>'
        f'<div class="c-time">{time}</div>'
        f'<div class="c-stat">{badge}</div>'
        f'<div class="c-tok">{token}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def trow_head():
    """パイプライン一覧のヘッダー行（.trow-head）を描画する。"""
    st.markdown(
        '<div class="trow trow-head">'
        '<div class="c-icon"></div>'
        '<div class="c-name">パイプライン</div>'
        '<div class="c-time">最終実行</div>'
        '<div class="c-stat">状態</div>'
        '<div class="c-tok">トークン</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def freshness_banner(push_log: dict) -> str:
    """_push_logのtimestampから鮮度バナーHTMLを返す"""
    from datetime import datetime
    ts = push_log.get("timestamp")
    fail = push_log.get("fail_count", 0)

    if not ts:
        return '<span class="freshness-stale">⚠️ データ未取得</span>'

    try:
        from datetime import timezone
        dt = datetime.fromisoformat(ts)
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        minutes = int((now - dt).total_seconds() / 60)
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
