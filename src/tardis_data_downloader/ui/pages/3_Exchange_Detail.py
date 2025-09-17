import streamlit as st
from tardis_data_downloader.data.data_manager import (
    EXCHANGE,
    TardisDataManager,
)
import json

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

if st.button("Get Exchange Details", type="primary"):
    with st.spinner("Getting exchange details..."):
        exchange_detail = manager.get_exchange_details(http_proxy)

    st.download_button(
        label="Download Exchange Detail JSON",
        data=json.dumps(exchange_detail, indent=2),
        file_name=f"{exchange}_exchange_detail.json",
        mime="application/json",
        type="secondary",
    )

    st.json(exchange_detail)
