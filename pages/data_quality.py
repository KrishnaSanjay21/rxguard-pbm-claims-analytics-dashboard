import plotly.express as px
import streamlit as st

from rxguard.charts import finish
from rxguard.config import COLORS
from rxguard.etl import read_refresh_log, refresh
from rxguard.store import claims, quality_details, quality_summary
from rxguard.ui import page_header

page_header(
    "Data Quality",
    "SQL-driven duplicate, identifier, amount, date, reference, status, and reconciliation checks.",
)

with st.sidebar:
    if st.button("Run data refresh", width="stretch"):
        result = refresh()
        st.cache_data.clear()
        st.success(f"Refresh complete: {result['valid_claims']:,} valid claims and {result['quality_issues']:,} issue flags.")

summary = quality_summary()
detail = quality_details()
all_claims = claims(valid_only=False)
valid = int(all_claims["is_valid_claim"].sum())
invalid = len(all_claims) - valid

cols = st.columns(4)
cols[0].metric("Source claims", f"{len(all_claims):,}")
cols[1].metric("Valid claims", f"{valid:,}")
cols[2].metric("Rows with issues", f"{invalid:,}")
cols[3].metric("Total issue flags", f"{int(summary['issue_count'].sum()):,}")

left, right = st.columns([1.15, 1], gap="large")
with left:
    st.subheader("Issue counts by rule")
    chart = summary.assign(check_name=summary["check_name"].str.replace("_", " ").str.title()).sort_values("issue_count")
    fig = px.bar(chart, x="issue_count", y="check_name", orientation="h", color_discrete_sequence=[COLORS["red"]])
    st.plotly_chart(finish(fig, x_title="Issue flags", y_title="SQL rule"), width="stretch")
with right:
    st.subheader("Refresh log")
    log = read_refresh_log()
    if log.empty:
        st.info("Run a refresh to create the audit log.")
    else:
        st.dataframe(log, hide_index=True, width="stretch")

st.subheader("Rows requiring review")
columns = ["claim_id", "client_id", "member_id", "service_date", "ndc", "claim_status",
           "duplicate_claim", "missing_identifier", "invalid_amount", "inconsistent_date",
           "reconciliation_failure", "reference_failure", "status_reason_failure", "issue_count"]
st.dataframe(detail[columns], hide_index=True, width="stretch")
st.download_button("Download quality exceptions CSV", data=detail.to_csv(index=False), file_name="rxguard-quality-exceptions.csv", mime="text/csv")
st.caption("Deliberately broken synthetic rows are included so the monitoring view and SQL rules can be demonstrated. Invalid rows are excluded from analytical KPIs.")
