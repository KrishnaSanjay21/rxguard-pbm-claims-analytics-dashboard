"""Create styled Excel client-reporting packs in memory for Streamlit downloads."""
from __future__ import annotations

from io import BytesIO

import pandas as pd

from rxguard.metrics import client_summary, monthly_summary


def build_client_report(claims: pd.DataFrame, client_name: str) -> bytes:
    selected = claims[claims["client_name"] == client_name].copy()
    if selected.empty:
        raise ValueError(f"No claims found for {client_name}")
    summary = client_summary(selected)
    monthly = monthly_summary(selected)
    paid = selected[selected["claim_status"] == "PAID"]
    drugs = paid.groupby(["drug_name", "therapeutic_class", "brand_generic"], as_index=False).agg(
        paid_claims=("claim_id", "count"), gross_cost=("gross_cost", "sum"),
        member_cost=("member_payment", "sum"), plan_cost=("plan_payment", "sum"),
    ).sort_values("plan_cost", ascending=False)
    dictionary = pd.DataFrame([
        ("Total claims", "Count of valid paid, rejected, and reversed claims."),
        ("Gross drug cost", "Sum of gross cost for valid paid claims."),
        ("Plan cost", "Sum of plan payment for valid paid claims."),
        ("Generic dispensing rate", "Generic paid claims divided by all paid claims."),
        ("Rejection rate", "Rejected valid claims divided by all valid claims."),
        ("Cost per paid claim", "Gross drug cost divided by paid claims."),
    ], columns=["KPI", "Definition"])

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter", datetime_format="yyyy-mm-dd") as writer:
        summary.to_excel(writer, sheet_name="KPI Summary", index=False)
        monthly.to_excel(writer, sheet_name="Monthly Trend", index=False)
        drugs.to_excel(writer, sheet_name="Drug Spend", index=False)
        detail_columns = ["claim_id", "member_id", "service_date", "ndc", "drug_name", "therapeutic_class",
                          "brand_generic", "days_supply", "claim_status", "rejection_reason", "gross_cost",
                          "member_payment", "plan_payment", "pharmacy_type"]
        selected[detail_columns].to_excel(writer, sheet_name="Claims Detail", index=False)
        dictionary.to_excel(writer, sheet_name="KPI Dictionary", index=False)

        workbook = writer.book
        header = workbook.add_format({"bold": True, "font_color": "white", "bg_color": "#14324A", "border": 0})
        money = workbook.add_format({"num_format": "$#,##0.00"})
        percent = workbook.add_format({"num_format": "0.0%"})
        date_format = workbook.add_format({"num_format": "yyyy-mm-dd"})
        for sheet_name, frame in [("KPI Summary", summary), ("Monthly Trend", monthly), ("Drug Spend", drugs),
                                  ("Claims Detail", selected[detail_columns]), ("KPI Dictionary", dictionary)]:
            worksheet = writer.sheets[sheet_name]
            worksheet.hide_gridlines(2)
            worksheet.freeze_panes(1, 0)
            worksheet.autofilter(0, 0, len(frame), max(len(frame.columns) - 1, 0))
            for col_num, value in enumerate(frame.columns):
                worksheet.write(0, col_num, value, header)
                width = min(max(len(str(value)) + 3, int(frame[value].astype(str).str.len().quantile(0.95)) + 2 if len(frame) else 12), 34)
                worksheet.set_column(col_num, col_num, width)
        for sheet_name in ["KPI Summary", "Monthly Trend", "Drug Spend", "Claims Detail"]:
            worksheet = writer.sheets[sheet_name]
            frame = {"KPI Summary": summary, "Monthly Trend": monthly, "Drug Spend": drugs, "Claims Detail": selected[detail_columns]}[sheet_name]
            for column in [c for c in frame.columns if "cost" in c or "payment" in c]:
                idx = frame.columns.get_loc(column)
                worksheet.set_column(idx, idx, 15, money)
            for column in [c for c in frame.columns if "rate" in c]:
                idx = frame.columns.get_loc(column)
                worksheet.set_column(idx, idx, 18, percent)
            for column in [c for c in frame.columns if "date" in c or c == "month"]:
                idx = frame.columns.get_loc(column)
                worksheet.set_column(idx, idx, 13, date_format)
    return output.getvalue()
