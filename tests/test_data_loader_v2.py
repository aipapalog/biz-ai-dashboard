import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))

# st.cache_data デコレータをモック
import streamlit as st
st.cache_data = lambda ttl=None: (lambda f: f)

def _mock_get_doc(collection, doc_id):
    return None  # Firestore応答なし = デフォルト値テスト

def test_get_system_health_returns_default_on_empty():
    with patch("utils.firebase_client.get_doc", side_effect=_mock_get_doc):
        from utils.data_loader_v2 import get_system_health
        result = get_system_health()
    assert isinstance(result, dict)
    assert "flows" in result
    assert "alerts" in result
    assert isinstance(result["alerts"], list)

def test_get_tasks_returns_default_on_empty():
    with patch("utils.firebase_client.get_doc", side_effect=_mock_get_doc):
        from utils.data_loader_v2 import get_tasks
        result = get_tasks()
    assert isinstance(result, dict)
    assert "total" in result

def test_get_push_log_no_cache():
    """get_push_log はキャッシュなしで常にFirestoreを叩く"""
    call_count = [0]
    def counting_get(col, doc):
        call_count[0] += 1
        return None
    with patch("utils.data_loader_v2.get_doc", side_effect=counting_get):
        from utils.data_loader_v2 import get_push_log
        get_push_log()
        get_push_log()
    assert call_count[0] >= 2  # キャッシュされていない

def test_no_function_raises_key_error():
    """全get_*関数がKeyError/AttributeErrorを起こさない"""
    with patch("utils.firebase_client.get_doc", side_effect=_mock_get_doc):
        import utils.data_loader_v2 as dl
        for name in ["get_system_health","get_tasks","get_business","get_bizdev",
                     "get_cx_quality","get_ai_ops","get_finance","get_content","get_meta"]:
            result = getattr(dl, name)()
            assert isinstance(result, dict), f"{name} should return dict"
