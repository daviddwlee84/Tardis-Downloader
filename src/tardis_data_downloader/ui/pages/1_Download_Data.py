import streamlit as st
from typing import Literal
from datetime import date
from tardis_dev import datasets
from dotenv import load_dotenv, find_dotenv
import os

# Import our components
from tardis_data_downloader.data.data_manager import TardisDataManager, DATA_TYPE
from tardis_data_downloader.ui.shared_components import (
    DEFAULT_DATA_ROOT,
    EXCHANGE_LIST,
)


_ = load_dotenv(find_dotenv())


st.set_page_config(page_title="Download Data", page_icon="📥")


DATA_TYPE_LIST = [dt.value for dt in DATA_TYPE]


def get_data_types(mode: Literal["str", "multiselect"] = "multiselect") -> list[str]:
    match mode:
        case "str":
            # Data types (comma-separated)
            data_types = st.text_input(
                "Data Types",
                value="trades",
                help="Data types to download (comma-separated, e.g., 'trades,incremental_book_L2')",
            )

            # Validate inputs
            if not data_types.strip():
                st.error("❌ Data Types cannot be empty")
                return

            data_types = data_types.split(",")
        case "multiselect":
            data_types = st.multiselect(
                "Data Types",
                options=DATA_TYPE_LIST,
                default=[DATA_TYPE.TRADES.value],
            )
        case _:
            raise ValueError(f"Invalid mode: {mode}")

    return data_types


def main():
    st.title("📥 Download Market Data")

    # Main download parameters
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Required Parameters")

        # Exchange selection
        exchange = st.selectbox(
            "Exchange",
            options=EXCHANGE_LIST,
            help="Select the cryptocurrency exchange to download data from",
        )

        data_types = get_data_types(mode="multiselect")

        # Symbols (comma-separated)
        symbols = st.text_input(
            "Symbols",
            value="BTC-PERPETUAL",
            help="Trading symbols to download (comma-separated, e.g., 'BTC-PERPETUAL,ETH-PERPETUAL')",
        )

    with col2:
        st.subheader("Date Range")

        # Date range selection
        col_date1, col_date2 = st.columns(2)

        with col_date1:
            from_date = st.date_input(
                "From Date", value=date(2023, 1, 1), help="Start date for data download"
            )

        with col_date2:
            to_date = st.date_input(
                "To Date (not inclusive)",
                value=date.today(),
                help="End date for data download (not inclusive)",
            )

    # Optional parameters in expander
    with st.expander("Advanced Options"):
        col_opt1, col_opt2 = st.columns(2)

        with col_opt1:
            format_type = st.selectbox(
                "Format",
                options=["csv", "json"],
                index=0,
                help="Data format for downloaded files",
            )

            api_key = st.text_input(
                "API Key",
                type="password",
                value=os.getenv("TARDIS_API_KEY"),
                help="Tardis API key (leave empty if not required)",
            )

            download_url_base = st.text_input(
                "Download URL Base",
                value="datasets.tardis.dev",
                help="Base URL for downloading data",
            )

        with col_opt2:
            concurrency = st.slider(
                "Concurrency",
                min_value=1,
                max_value=20,
                value=5,
                help="Number of concurrent downloads",
            )

            http_proxy = st.text_input(
                "HTTP Proxy", help="HTTP proxy URL (leave empty if not required)"
            )

    # Download directory info
    st.info(f"📁 Data will be downloaded to: `{DEFAULT_DATA_ROOT}`")

    # Download button
    if st.button("🚀 Start Download", type="primary", use_container_width=True):

        if not symbols.strip():
            st.error("❌ Symbols cannot be empty")
            return

        if from_date > to_date:
            st.error("❌ From Date cannot be after To Date")
            return

        # Format dates
        from_date_str = from_date.isoformat()
        to_date_str = to_date.isoformat()

        # Prepare parameters
        download_params = {
            "exchange": exchange,
            "data_types": data_types,
            "symbols": symbols.split(","),
            "from_date": from_date_str,
            "to_date": to_date_str,
            "format": format_type,
            "api_key": api_key,
            "download_dir": str(DEFAULT_DATA_ROOT),
            "download_url_base": download_url_base,
            "concurrency": concurrency,
            "http_proxy": http_proxy if http_proxy.strip() else None,
        }

        # Create progress container
        progress_container = st.container()
        status_container = st.container()

        with progress_container:
            st.subheader("Download Progress")
            status_text = st.empty()

        with status_container:
            st.subheader("Download Status")

            try:
                # Execute download
                with st.spinner("Downloading data..."):
                    datasets.download(
                        **download_params,
                        get_filename=TardisDataManager.default_file_name,
                    )

                status_text.text("✅ Download completed successfully!")
                st.success("Data downloaded successfully!")

                # Show download summary
                st.info(
                    f"""
                **Download Summary:**
                - Exchange: {exchange}
                - Data Types: {data_types}
                - Symbols: {symbols}
                - Date Range: {from_date_str} to {to_date_str}
                - Downloaded to: {DEFAULT_DATA_ROOT}
                """
                )

            except Exception as e:
                status_text.text("❌ Download failed")
                st.error(f"Download failed: {str(e)}")
                st.exception(e)


if __name__ == "__main__":
    main()
