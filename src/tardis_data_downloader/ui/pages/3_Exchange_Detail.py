import streamlit as st
from tardis_data_downloader.data.data_manager import (
    EXCHANGE,
    TardisDataManager,
)

st.title("Exchange Detail")
st.set_page_config(layout="wide")


EXCHANGE_LIST = [e.value for e in EXCHANGE]
exchange = st.selectbox(
    "Exchange",
    options=EXCHANGE_LIST,
)
# Optional parameters in expander
with st.expander("Advanced Options"):
    http_proxy = st.text_input(
        "HTTP Proxy", help="HTTP proxy URL (leave empty if not required)"
    )

manager = TardisDataManager(exchange=exchange)
exchange_detail = manager.get_exchange_details(http_proxy)

st.json(exchange_detail)

import ipdb

ipdb.set_trace()
