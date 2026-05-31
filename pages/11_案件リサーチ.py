import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import data_loader

st.set_page_config(page_title="🔍 案件リサーチ", page_icon="🔍", layout="wide")
st_autorefresh(interval=120_000, key="freelance_refresh")
st.title("🔍 フリーランス案件リサーチ（AI自動化率 Top5）")

report = data_loader.freelance_report()

if report:
    st.caption(f"📅 {report.get('date','')}  ｜  📁 {report.get('filename','')}  ｜  🔄 {report.get('updated_at','')[:16]}")
    content = report.get("content", "")
    if content:
        st.markdown(content[:4000])
    else:
        st.info("レポートの内容がありません")
else:
    st.info("フリーランス案件レポートがありません。freelance_researcherパイプライン実行後に更新されます。")
    st.markdown("""
**対象プラットフォーム:**
- クラウドワークス
- ランサーズ
- Coconala

**調査対象スキル:**
- QAエンジニア
- テスト自動化
- Playwright / Selenium
- Python自動化
- AI活用コンサルティング
""")
