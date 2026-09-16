"""RxGuard public portfolio dashboard. All data is synthetic."""
import streamlit as st

st.set_page_config(
    page_title="RxGuard PBM Analytics",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.markdown("## RxGuard")
st.sidebar.caption("Synthetic PBM claims analytics")

page = st.navigation([
    st.Page("pages/executive_summary.py", title="Executive Summary", icon="📊", default=True),
    st.Page("pages/client_reporting.py", title="Client Reporting", icon="🏢"),
    st.Page("pages/drug_analysis.py", title="Drug Analysis", icon="💊"),
    st.Page("pages/claims_operations.py", title="Claims Operations", icon="⚙️"),
    st.Page("pages/adherence.py", title="Adherence", icon="📅"),
    st.Page("pages/data_quality.py", title="Data Quality", icon="✅"),
])
page.run()
