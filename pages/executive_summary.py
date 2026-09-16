import pandas as pd
import plotly.express as px
import streamlit as st

from rxguard.charts import finish
from rxguard.config import CHART_COLORS, COLORS
from rxguard.metrics import client_summary, executive_kpis, monthly_summary
from rxguard.ui import filter_claims, load_valid_claims, metric_value, no_data_guard, page_header

page_header(
    "Executive Summary",
    "Portfolio cost, utilization, generic dispensing, and claims outcomes. All records are synthetic.",
)
data = filter_claims(load_valid_claims(), "executive")
no_data_guard(data)
kpis = executive_kpis(data)

row1 = st.columns(4)
row1[0].metric("Total claims", metric_value(kpis["total_claims"]))
row1[1].metric("Gross drug cost", metric_value(kpis["gross_drug_cost"], "currency"))
row1[2].metric("Member cost", metric_value(kpis["member_cost"], "currency"))
row1[3].metric("Plan cost", metric_value(kpis["plan_cost"], "currency"))
row2 = st.columns(4)
row2[0].metric("Generic dispensing rate", metric_value(kpis["generic_dispensing_rate"], "percent"))
row2[1].metric("Rejection rate", metric_value(kpis["rejection_rate"], "percent"))
row2[2].metric("Cost per paid claim", metric_value(kpis["cost_per_paid_claim"], "currency"))
row2[3].metric("Paid claims", metric_value(kpis["paid_claims"]))

monthly = monthly_summary(data).groupby("month", as_index=False).agg(
    total_claims=("total_claims", "sum"), plan_cost=("plan_cost", "sum"), gross_drug_cost=("gross_drug_cost", "sum")
)
clients = client_summary(data)

left, right = st.columns([1.45, 1], gap="large")
with left:
    st.subheader("Monthly paid-claim cost")
    fig = px.area(monthly, x="month", y="plan_cost", color_discrete_sequence=[COLORS["blue"]])
    fig.update_traces(hovertemplate="%{x|%b %Y}: $%{y:,.0f}<extra></extra>")
    st.plotly_chart(finish(fig, x_title="Month", y_title="Plan cost (USD)"), width="stretch")
with right:
    st.subheader("Claim status mix")
    status = data.groupby("claim_status", as_index=False).agg(claims=("claim_id", "count"))
    fig = px.pie(status, names="claim_status", values="claims", hole=0.58, color="claim_status",
                 color_discrete_map={"PAID": COLORS["green"], "REJECTED": COLORS["amber"], "REVERSED": COLORS["red"]})
    fig.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(finish(fig), width="stretch")

left, right = st.columns(2, gap="large")
with left:
    st.subheader("Plan cost by client")
    fig = px.bar(clients.sort_values("plan_cost"), x="plan_cost", y="client_name", orientation="h",
                 color="client_name", color_discrete_sequence=CHART_COLORS)
    fig.update_layout(showlegend=False)
    fig.update_traces(hovertemplate="%{y}: $%{x:,.0f}<extra></extra>")
    st.plotly_chart(finish(fig, x_title="Plan cost (USD)", y_title="Client"), width="stretch")
with right:
    st.subheader("Generic rate and paid-claim cost")
    fig = px.scatter(clients, x="generic_dispensing_rate", y="cost_per_paid_claim", size="paid_claims",
                     color="client_name", color_discrete_sequence=CHART_COLORS,
                     hover_data={"client_name": True, "plan_cost": ":$,.0f", "paid_claims": ":,"})
    fig.update_xaxes(tickformat=".0%")
    st.plotly_chart(finish(fig, x_title="Generic dispensing rate", y_title="Cost per paid claim (USD)"), width="stretch")

st.caption("Gross, member, and plan cost metrics include valid paid claims only. Reversed claims are reported in operations and excluded from paid-cost KPIs.")
