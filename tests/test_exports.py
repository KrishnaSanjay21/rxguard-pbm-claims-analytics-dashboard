from io import BytesIO
import zipfile

import pandas as pd

from rxguard.exports import build_client_report
from rxguard.store import claims


def test_excel_export_is_valid_xlsx_with_expected_sheets():
    data = claims(valid_only=True)
    client = data["client_name"].dropna().iloc[0]
    output = build_client_report(data, client)
    assert output[:2] == b"PK"
    with zipfile.ZipFile(BytesIO(output)) as archive:
        workbook_xml = archive.read("xl/workbook.xml").decode("utf-8")
    for sheet in ["KPI Summary", "Monthly Trend", "Drug Spend", "Claims Detail", "KPI Dictionary"]:
        assert sheet in workbook_xml
