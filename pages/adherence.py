import plotly.express as px
import streamlit as st

from rxguard.charts import finish
from rxguard.config import COLORS
from rxguard.metrics import adherence_proxy
from rxguard.ui import filter_claims, load_valid_claims, metric_value, no_data_guard, page_header

page_header(
    "Adherence",
    "PDC-style portfolio proxy for maintenance therapies. This is a demonstration, not a certified HEDIS measure.",
)
data = filter_claims(load_valid_claims(), "adherence")
no_data_guard(data)
proxy = adherence_proxy(data, threshold=0.80)
if proxy.empty:
    st.warning("No members have at least two paid maintenance-drug fills in the selected period.")
    st.stop()

below = proxy[proxy["below_threshold"]]
cols = st.columns(4)
cols[0].metric("Eligible member-drug episodes", metric_value(len(proxy)))
cols[1].metric("Average PDC-style proxy", metric_value(proxy["pdc_proxy"].mean(), "percent"))
cols[2].metric("Below 80%", metric_value(len(below)))
cols[3].metric("Below-threshold rate", metric_value(len(below) / len(proxy), "percent"))

left, right = st.columns(2, gap="large")
with left:
    st.subheader("Proxy distribution")
    fig = px.histogram(proxy, x="pdc_proxy", nbins=20, color_discrete_sequence=[COLORS["blue"]])
    fig.add_vline(x=0.80, line_dash="dash", line_color=COLORS["red"], annotation_text="80% threshold")
    fig.update_xaxes(tickformat=".0%")
    st.plotly_chart(finish(fig, x_title="PDC-style proxy", y_title="Member-drug episodes"), width="stretch")
with right:
    st.subheader("Below-threshold episodes by client")
    client = below.groupby("client_name", as_index=False).agg(episodes=("member_id", "count"), average_proxy=("pdc_proxy", "mean")).sort_values("episodes")
    fig = px.bar(client, x="episodes", y="client_name", orientation="h", color_discrete_sequence=[COLORS["amber"]])
    st.plotly_chart(finish(fig, x_title="Episodes below 80%", y_title="Client"), width="stretch")

st.subheader("Members below the demonstration threshold")
display = below[["client_name", "member_id", "drug_name", "fills", "days_supplied", "measurement_days", "pdc_proxy"]].copy()
st.dataframe(display.head(250), hide_index=True, width="stretch", column_config={"pdc_proxy": st.column_config.ProgressColumn("PDC-style proxy", min_value=0.0, max_value=1.0, format="%.1f%%")})

with st.expander("Method and limitation"):
    st.write("The proxy is capped at 100% and equals total days supplied divided by the episode from first fill through the end of the last fill's days supplied. It requires at least two paid fills and does not adjust overlapping fills, inpatient stays, exclusions, continuous enrollment, or formal HEDIS specifications.")
