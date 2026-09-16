import plotly.express as px
import streamlit as st

from rxguard.charts import finish
from rxguard.config import COLORS
from rxguard.ui import filter_claims, load_valid_claims, metric_value, no_data_guard, page_header

page_header(
    "Claims Operations",
    "Paid, rejected, and reversed claims with processing trends and rejection reasons.",
)
data = filter_claims(load_valid_claims(), "operations")
no_data_guard(data)
status = data.groupby("claim_status", as_index=False).agg(claims=("claim_id", "count"))
rejected = data[data["claim_status"] == "REJECTED"]
reversed = data[data["claim_status"] == "REVERSED"]

cols = st.columns(4)
cols[0].metric("Paid claims", metric_value((data["claim_status"] == "PAID").sum()))
cols[1].metric("Rejected claims", metric_value(len(rejected)))
cols[2].metric("Reversed claims", metric_value(len(reversed)))
cols[3].metric("Average processing lag", f"{(data['processed_at'] - data['service_date']).dt.days.mean():.1f} days")

left, right = st.columns(2, gap="large")
with left:
    st.subheader("Claim status")
    fig = px.bar(status, x="claim_status", y="claims", color="claim_status",
                 color_discrete_map={"PAID": COLORS["green"], "REJECTED": COLORS["amber"], "REVERSED": COLORS["red"]})
    fig.update_layout(showlegend=False)
    st.plotly_chart(finish(fig, x_title="Status", y_title="Claims"), width="stretch")
with right:
    st.subheader("Rejection reasons")
    reasons = rejected.groupby("rejection_reason", as_index=False).agg(claims=("claim_id", "count")).sort_values("claims")
    fig = px.bar(reasons, x="claims", y="rejection_reason", orientation="h", color_discrete_sequence=[COLORS["amber"]])
    st.plotly_chart(finish(fig, x_title="Rejected claims", y_title="Reason"), width="stretch")

st.subheader("Weekly processing volume")
trend = data.assign(week=data["processed_at"].dt.to_period("W").dt.start_time).groupby(["week", "claim_status"], as_index=False).agg(claims=("claim_id", "count"))
fig = px.line(trend, x="week", y="claims", color="claim_status", markers=False,
              color_discrete_map={"PAID": COLORS["green"], "REJECTED": COLORS["amber"], "REVERSED": COLORS["red"]})
st.plotly_chart(finish(fig, x_title="Processing week", y_title="Claims"), width="stretch")

st.subheader("Recent rejected and reversed claims")
exceptions = data[data["claim_status"].isin(["REJECTED", "REVERSED"])].sort_values("service_date", ascending=False)
st.dataframe(exceptions[["claim_id", "client_name", "member_id", "service_date", "drug_name", "claim_status", "rejection_reason", "gross_cost"]].head(100),
             hide_index=True, width="stretch", column_config={"service_date": st.column_config.DateColumn(format="YYYY-MM-DD"), "gross_cost": st.column_config.NumberColumn(format="$%.2f")})
