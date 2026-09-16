from __future__ import annotations

import pandas as pd
import streamlit as st

from rxguard.store import claims


@st.cache_data(show_spinner=False)
def load_valid_claims() -> pd.DataFrame:
    return claims(valid_only=True)


def page_header(title: str, description: str) -> None:
    st.title(title)
    st.caption(description)


def filter_claims(frame: pd.DataFrame, key: str) -> pd.DataFrame:
    with st.sidebar:
        st.markdown("### Portfolio filters")
        client_options = sorted(frame["client_name"].dropna().unique().tolist())
        selected_clients = st.multiselect("Clients", client_options, default=client_options, key=f"{key}_clients")
        min_date, max_date = frame["service_date"].min().date(), frame["service_date"].max().date()
        date_range = st.date_input("Service date", value=(min_date, max_date), min_value=min_date, max_value=max_date, key=f"{key}_dates")
    if len(date_range) != 2:
        start, end = min_date, max_date
    else:
        start, end = date_range
    return frame[
        frame["client_name"].isin(selected_clients)
        & frame["service_date"].dt.date.between(start, end)
    ].copy()


def no_data_guard(frame: pd.DataFrame) -> None:
    if frame.empty:
        st.warning("No claims match the current filters.")
        st.stop()


def metric_value(value: float | int | None, kind: str = "number") -> str:
    if value is None or pd.isna(value):
        return "n.a."
    if kind == "currency":
        return f"${value:,.0f}"
    if kind == "percent":
        return f"{value:.1%}"
    return f"{int(value):,}"
