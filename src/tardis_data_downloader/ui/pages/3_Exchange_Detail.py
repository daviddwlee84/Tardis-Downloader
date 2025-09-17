import streamlit as st
from tardis_data_downloader.data.data_manager import (
    EXCHANGE,
    TardisApi,
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


@st.cache_data
def get_exchange_detail(exchange: str, http_proxy: str | None = None) -> dict:
    api = TardisApi(http_proxy=http_proxy)
    return api.get_exchange_details(exchange)


# Use session state to track fetched data and current exchange
if "exchange_detail" not in st.session_state:
    st.session_state.exchange_detail = None
    st.session_state.current_exchange = None

# Check if exchange changed, clear cache if so
if st.session_state.current_exchange != exchange:
    st.session_state.exchange_detail = None
    st.session_state.current_exchange = exchange

with st.expander("Exchange List"):
    api = TardisApi(http_proxy=http_proxy)
    exchange_list = api.get_exchanges()
    st.json(exchange_list)

# Button to fetch exchange details
if st.button("Get Exchange Details", type="primary"):
    # Fetch with proxy support (not cached for proxy, but data is cached)
    exchange_detail = get_exchange_detail(exchange, http_proxy)
    st.session_state.exchange_detail = exchange_detail

# Display results if we have them
if st.session_state.exchange_detail is not None:
    exchange_detail = st.session_state.exchange_detail

    # Download button - this will persist even after clicks
    st.download_button(
        label="📥 Download Exchange Detail JSON",
        data=json.dumps(exchange_detail, indent=2),
        file_name=f"{exchange}_exchange_detail.json",
        mime="application/json",
        type="secondary",
    )

    # JSON display - this will persist
    st.json(exchange_detail)

    # Show data size info
    data_size_mb = len(json.dumps(exchange_detail).encode("utf-8")) / (1024 * 1024)
    st.info(f"💾 Data size: {data_size_mb:.1f} MB")

    # Clear button
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.session_state.exchange_detail = None
            st.rerun()
    with col2:
        if st.button("🗑️ Clear Display"):
            st.session_state.exchange_detail = None
            st.rerun()
else:
    st.info(
        "👆 Click 'Get Exchange Details' to fetch and display exchange information. Data will be cached for faster subsequent loads."
    )
