from __future__ import annotations

from tardis_data_downloader.data.data_manager import (
    TardisDataManager,
    DATA_TYPE,
    EXCHANGE,
)


from pathlib import Path
from dataclasses import dataclass
import streamlit as st
import pandas as pd


# Check if we're running from project (has 'src' in path) or from installed package
current_file_path = Path(__file__).resolve()
path_parts = current_file_path.parts

# If 'src' is in the path, we're in a project - use project-relative path
if "src" in path_parts:
    DEFAULT_DATA_ROOT = Path("./datasets").resolve()
    if not DEFAULT_DATA_ROOT.exists():
        DEFAULT_DATA_ROOT = (
            Path(__file__).parent.parent.parent.parent / "datasets"
        ).resolve()
# If no 'src' in path, we're likely in an installed package - use ~/datasets
else:
    DEFAULT_DATA_ROOT = Path.home() / "datasets"


# TODO: consider if we want to add data_type to the data options
@dataclass
class DataOptions:
    data_root: str = str(DEFAULT_DATA_ROOT)
    exchange: str = EXCHANGE.DERIBIT.value
    date: str = "2023-01-01"
    symbol: str = "BTC-PERPETUAL"


def init_session_state() -> None:
    if "data_options" not in st.session_state:
        st.session_state["data_options"] = DataOptions()


def build_data_manager() -> TardisDataManager:
    init_session_state()

    return TardisDataManager(
        root_dir=st.session_state["data_options"].data_root,
        exchange=st.session_state["data_options"].exchange,
    )


@st.cache_data
def get_data_frame(
    data_type: DATA_TYPE,
    data_options: DataOptions,
) -> pd.DataFrame:
    manager: TardisDataManager = build_data_manager()
    df = manager.get_data(data_type, data_options.date, data_options.symbol)
    return df


EXCHANGE_LIST = [e.value for e in EXCHANGE]


def sidebar_controls() -> DataOptions:
    init_session_state()

    with st.sidebar:
        st.subheader("Data Options")
        data_root = st.text_input(
            "Data Root",
            value=st.session_state["data_options"].data_root,
            help="Root directory, contains exchange/data_type/year-month-day/symbol.csv.gz subdirectories",
        )
        st.session_state["data_options"].data_root = data_root

        exchange = st.selectbox(
            "Exchange",
            options=EXCHANGE_LIST,
            index=EXCHANGE_LIST.index(st.session_state["data_options"].exchange),
        )
        st.session_state["data_options"].exchange = exchange

        # Dynamically list symbols from data root
        manager = build_data_manager()

        dates = manager.list_dates(DATA_TYPE.TRADES)

        if dates:
            date = st.selectbox(
                "Date (YYYY-MM-DD)",
                options=dates,
                index=(
                    dates.index(st.session_state["data_options"].date)
                    if st.session_state["data_options"].date in dates
                    else 0
                ),
            )
        else:
            date = st.text_input(
                "Date (YYYY-MM-DD)", value=st.session_state["data_options"].date
            )

        try:
            symbols = manager.list_symbols(DATA_TYPE.TRADES, date)
        except Exception:
            symbols = []

        default_symbol = st.session_state["data_options"].symbol
        if symbols:
            symbol = st.selectbox(
                "Symbol",
                options=symbols,
                index=(
                    symbols.index(default_symbol) if default_symbol in symbols else 0
                ),
            )
        else:
            symbol = st.text_input(
                "Symbol (e.g. BTC-PERPETUAL)", value=default_symbol or "BTC-PERPETUAL"
            )
        st.session_state["data_options"].symbol = symbol

    return DataOptions(data_root, exchange, date, symbol)
