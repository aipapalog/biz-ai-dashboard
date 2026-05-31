"""Firebase Realtime DB接続。Streamlit Community Cloud（secrets）とローカル（ファイル）の両方に対応。"""
import json
from pathlib import Path

_initialized = False
_available = False
LOCAL_SA = Path(r"C:\Users\0000112191\.claude\secrets\dashboard_sa_key.json")
DB_URL = "https://ai-agent-dashboard-5810b.firebaseio.com"


def _init() -> bool:
    global _initialized, _available
    if _initialized:
        return _available
    _initialized = True
    try:
        import firebase_admin
        from firebase_admin import credentials

        if firebase_admin._apps:
            _available = True
            return True

        # Streamlit Community Cloud: secrets.toml の [firebase_sa] セクション
        cred = None
        try:
            import streamlit as st
            if "firebase_sa" in st.secrets:
                cred = credentials.Certificate(dict(st.secrets["firebase_sa"]))
        except Exception:
            pass

        # ローカル: サービスアカウントJSONファイル
        if cred is None and LOCAL_SA.exists():
            cred = credentials.Certificate(str(LOCAL_SA))

        if cred is None:
            return False

        firebase_admin.initialize_app(cred, {"databaseURL": DB_URL})
        _available = True
        return True
    except Exception:
        return False


def get(path: str, default=None):
    if not _init():
        return default
    try:
        from firebase_admin import db
        val = db.reference(path).get()
        return val if val is not None else default
    except Exception:
        return default


def get_dashboard() -> dict:
    data = get("/dashboard", {})
    return data if isinstance(data, dict) else {}


def is_available() -> bool:
    return _init()
