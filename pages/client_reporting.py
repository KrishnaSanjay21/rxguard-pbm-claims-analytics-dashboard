import pandas as pd
import plotly.express as px
import streamlit as st

from rxguard.charts import finish
from rxguard.config import CHART_COLORS
from rxguard.exports import build_client_report
from rxguard.metrics import client_summary, monthly_summary
from rxguard.ui import load_valid_claims, no_data_guard, page_header

page_header(
    "Client Reporting",
    "Compare fictional employer groups, inspect monthly trends, and export a client-ready Excel reporting pack.",
)
data = load_valid_claims()
client_names = sorted(data["client_name"].dropna().unique())
with st.sidebar:
    selected = st.multiselect("Employer clients", client_names, default=client_names, key="report_clients")
filtered = data[data["client_name"].isin(selected)].copy()
no_data_guard(filtered)

summary = client_summary(filtered)
display = summary[["client_name", "total_claims", "gross_drug_cost", "member_cost", "plan_cost",
                   "generic_dispensing_rate", "rejection_rate", "cost_per_paid_claim"]].copy()
display.columns = ["Client", "Claims", "Gross drug cost", "Member cost", "Plan cost",
                   "Generic dispensing rate", "Rejection rate", "Cost per paid claim"]
st.subheader("Client KPI comparison")
st.dataframe(
    display,
    hide_index=True,
    width="stretch",
    column_config={
        "Gross drug cost": st.column_config.NumberColumn(format="$%.0f"),
        "Member cost": st.column_config.NumberColumn(format="$%.0f"),
        "Plan cost": st.column_config.NumberColumn(format="$%.0f"),
        "Cost per paid claim": st.column_config.NumberColumn(format="$%.2f"),
        "Generic dispensing rate": st.column_config.NumberColumn(format="%.1f%%"),
        "Rejection rate": st.column_config.NumberColumn(format="%.1f%%"),
    },
)

monthly = monthly_summary(filtered)
left, right = st.columns(2, gap="large")
with left:
    st.subheader("Monthly plan cost")
    fig = px.line(monthly, x="month", y="plan_cost", color="client_name", markers=True,
                  color_discrete_sequence=CHART_COLORS)
    fig.update_traces(hovertemplate="$%{y:,.0f}<extra></extra>")
    st.plotly_chart(finish(fig, x_title="Month", y_title="Plan cost (USD)"), width="stretch")
with right:
    st.subheader("Generic dispensing rate")
    fig = px.bar(summary.sort_values("generic_dispensing_rate"), x="generic_dispensing_rate", y="client_name",
                 orientation="h", color="client_name", color_discrete_sequence=CHART_COLORS)
    fig.update_layout(showlegend=False)
    fig.update_xaxes(tickformat=".0%")
    st.plotly_chart(finish(fig, x_title="Generic dispensing rate", y_title="Client"), width="stretch")

st.subheader("Excel client reporting pack")
export_client = st.selectbox("Client to export", client_names, key="export_client")
workbook = build_client_report(data, export_client)
safe_name = export_client.lower().replace(" ", "-")
st.download_button(
    "Download Excel report",
    data=workbook,
    file_name=f"rxguard-{safe_name}-client-report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    width="stretch",
)
st.caption("The workbook includes KPI Summary, Monthly Trend, Drug Spend, Claims Detail, and KPI Dictionary sheets.")
