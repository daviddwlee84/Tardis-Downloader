from __future__ import annotations
from tardis_data_downloader.data.data_manager import (
    DATA_TYPE,
    EXCHANGE,
    TardisDataManager,
)
from tardis_data_downloader.ui.shared_components import (
    sidebar_controls,
    get_data_frame,
    build_data_manager,
)


import pandas as pd
import streamlit as st

st.title("Raw Data")
st.set_page_config(layout="wide")

data_options = sidebar_controls()

with st.sidebar:
    max_rows = st.number_input(
        "Max Rows",
        value=100,
        min_value=0,
        help="Max rows to display. 0 means no limit.",
    )

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

manager: TardisDataManager = build_data_manager()


def display_dataframe(df: pd.DataFrame, max_rows: int | None = None) -> None:
    try:
        if max_rows is not None:
            df = df.head(max_rows)
        st.dataframe(df, width="content", height=480)
    except Exception as e:
        # MessageSizeError: Data of size 354.3 MB exceeds the message size limit of 200.0 MB.
        # This is often caused by a large chart or dataframe. Please decrease the amount of data sent to the browser, or increase the limit by setting the config option server.maxMessageSize. Click here to learn more about config options.
        # Note that increasing the limit may lead to long loading times and large memory consumption of the client's browser and the Streamlit server.
        st.error(e)
        st.dataframe(df.head(100), width="content", height=480)
        st.caption("Data is too large to display. Displaying first 100 rows.")


# Create content for each tab
for i, (data_type, display_name) in enumerate(DATA_TYPE_CONFIG.items()):
    with tabs[i]:
        st.caption(display_name)
        if not manager.get_path(
            data_type, data_options.date, data_options.symbol
        ).exists():
            if st.button(
                "Adhoc Download Data",
                key=f"adhoc_download_{data_type}",
                type="primary",
            ):
                with st.spinner("Downloading data..."):
                    manager.download_data(
                        data_type, data_options.date, data_options.symbol
                    )
                df = get_data_frame(data_type, data_options)
                display_dataframe(df, max_rows)
            else:
                st.error(
                    f"Data not found: {manager.get_path(data_type, data_options.date, data_options.symbol)}"
                )
                st.info("Please download the data first.")
        else:
            df = get_data_frame(data_type, data_options)
            display_dataframe(df, max_rows)
