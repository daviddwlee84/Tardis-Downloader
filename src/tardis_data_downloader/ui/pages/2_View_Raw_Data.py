from __future__ import annotations
from tardis_data_downloader.data.data_manager import DATA_TYPE, EXCHANGE
from tardis_data_downloader.ui.shared_components import sidebar_controls, get_data_frame


import pandas as pd
import streamlit as st

st.title("Raw Data")
st.set_page_config(layout="wide")

data_options = sidebar_controls()


tab1, tab2 = st.tabs(
    ["trades", "to_be_added"]
)  # TODO: add other tabs for other data types


with tab1:
    st.caption("Trades")
    trades_df = get_data_frame(
        DATA_TYPE.TRADES,
        data_options,
    )
    st.dataframe(trades_df, width="content", height=480)
