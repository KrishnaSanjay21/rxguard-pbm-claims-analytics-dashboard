import plotly.express as px
import streamlit as st

from rxguard.charts import finish
from rxguard.config import CHART_COLORS, COLORS
from rxguard.metrics import generic_opportunity, unusual_cost_increases
from rxguard.ui import filter_claims, load_valid_claims, no_data_guard, page_header

page_header(
    "Drug Analysis",
    "High-cost drugs, therapeutic class mix, brand-to-generic opportunities, and unusual price movement.",
)
data = filter_claims(load_valid_claims(), "drug")
no_data_guard(data)
paid = data[data["claim_status"] == "PAID"]
drug = paid.groupby(["drug_name", "therapeutic_class", "brand_generic"], as_index=False).agg(
    paid_claims=("claim_id", "count"), gross_cost=("gross_cost", "sum"), plan_cost=("plan_payment", "sum"),
    average_cost=("gross_cost", "mean"),
).sort_values("plan_cost", ascending=False)
class_mix = paid.groupby("therapeutic_class", as_index=False).agg(plan_cost=("plan_payment", "sum"), paid_claims=("claim_id", "count"))

left, right = st.columns(2, gap="large")
with left:
    st.subheader("Top drugs by plan cost")
    top = drug.head(12).sort_values("plan_cost")
    fig = px.bar(top, x="plan_cost", y="drug_name", orientation="h", color="therapeutic_class",
                 color_discrete_sequence=CHART_COLORS)
    fig.update_traces(hovertemplate="%{y}: $%{x:,.0f}<extra></extra>")
    st.plotly_chart(finish(fig, x_title="Plan cost (USD)", y_title="Drug"), width="stretch")
with right:
    st.subheader("Therapeutic class cost")
    fig = px.treemap(class_mix, path=["therapeutic_class"], values="plan_cost", color="plan_cost",
                     color_continuous_scale=["#D7E9F7", COLORS["blue"], COLORS["navy"]])
    fig.update_traces(hovertemplate="%{label}<br>$%{value:,.0f}<extra></extra>")
    st.plotly_chart(finish(fig), width="stretch")

opportunity = generic_opportunity(data)
st.subheader("Brand claims with a synthetic generic-equivalent flag")
if opportunity.empty:
    st.info("No flagged generic opportunities match the current filters.")
else:
    opportunity_display = opportunity.copy()
    st.dataframe(opportunity_display, hide_index=True, width="stretch", column_config={
        "gross_cost": st.column_config.NumberColumn("Gross cost", format="$%.0f"),
        "plan_cost": st.column_config.NumberColumn("Plan cost", format="$%.0f"),
        "average_cost": st.column_config.NumberColumn("Average cost", format="$%.2f"),
        "paid_claims": st.column_config.NumberColumn("Paid claims", format="%d"),
    })

st.subheader("Unusual average-cost increases")
anomalies = unusual_cost_increases(data)
if anomalies.empty:
    st.info("No drug exceeded the 20% latest-month versus prior-three-month threshold.")
else:
    st.dataframe(anomalies, hide_index=True, width="stretch", column_config={
        "flagged_month": st.column_config.DateColumn("Flagged month", format="MMM YYYY"),
        "flagged_average_cost": st.column_config.NumberColumn("Flagged average", format="$%.2f"),
        "prior_3_month_average": st.column_config.NumberColumn("Prior 3-month average", format="$%.2f"),
        "increase_rate": st.column_config.NumberColumn("Increase", format="%.1f%%"),
    })
st.caption("Opportunity flags and cost anomalies are portfolio analytics signals, not formulary or clinical recommendations.")
