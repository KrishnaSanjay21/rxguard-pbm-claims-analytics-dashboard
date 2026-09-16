from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def test_all_six_dashboard_pages_render():
    app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
    assert not app.exception
    assert app.title[0].value == "Executive Summary"
    assert len(app.metric) == 8

    expected = {
        "pages/client_reporting.py": "Client Reporting",
        "pages/drug_analysis.py": "Drug Analysis",
        "pages/claims_operations.py": "Claims Operations",
        "pages/adherence.py": "Adherence",
        "pages/data_quality.py": "Data Quality",
    }
    for path, title in expected.items():
        app.switch_page(path).run()
        assert not app.exception
        assert app.title[0].value == title
