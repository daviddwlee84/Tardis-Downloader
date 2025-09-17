from __future__ import annotations
from tardis_data_downloader.data.data_manager import DATA_TYPE, EXCHANGE
from tardis_data_downloader.ui.shared_components import sidebar_controls, get_data_frame


import pandas as pd
import streamlit as st

st.title("Raw Data")
st.set_page_config(layout="wide")

data_options = sidebar_controls()

# Data type configuration
DATA_TYPE_CONFIG = {
    DATA_TYPE.TRADES: "Trades",
    DATA_TYPE.INCREMENTAL_BOOK_L2: "Incremental Book L2",
    DATA_TYPE.BOOK_SNAPSHOT_25: "Book Snapshot 25",
    DATA_TYPE.BOOK_SNAPSHOT_5: "Book Snapshot 5",
    DATA_TYPE.OPTIONS_CHAIN: "Options Chain",
    DATA_TYPE.QUOTES: "Quotes",
    DATA_TYPE.DERIVATIVE_TICKER: "Derivative Ticker",
    DATA_TYPE.LIQUIDATIONS: "Liquidations",
}

# Create tabs for all data types
tab_names = list(DATA_TYPE_CONFIG.values())
tabs = st.tabs(tab_names)

# Create content for each tab
for i, (data_type, display_name) in enumerate(DATA_TYPE_CONFIG.items()):
    with tabs[i]:
        st.caption(display_name)
        try:
            df = get_data_frame(data_type, data_options)
            st.dataframe(df, width="content", height=480)
        except Exception as e:
            st.error(f"Failed to load {display_name.lower()} data: {str(e)}")
            st.info("Please check your data selection and try again.")
