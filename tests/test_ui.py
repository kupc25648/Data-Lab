"""Integration smoke test, enabled only where streamlit is installed."""
import pytest

def test_streamlit_home_smoke():
    st=pytest.importorskip('streamlit')
    from streamlit.testing.v1 import AppTest
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    test=AppTest.from_file(str(root/'app.py'),default_timeout=15)
    test.run()
    assert not test.exception
    assert any('DataSci Studio V3' in s for s in test.markdown.values)
