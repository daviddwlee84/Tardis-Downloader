from typing import Final
from pathlib import Path
from enum import StrEnum
import pandas as pd
from datetime import datetime
from tardis_data_downloader.utils.date_utils import DATE_TYPE, to_date_string
from loguru import logger


# TODO: find all exchange set
class EXCHANGE(StrEnum):
    DERIBIT = "deribit"
    BINANCE = "binance"
    BINANCE_FUTURES = "binance-futures"
    BINANCE_DELIVERY = "binance-delivery"
    BITMEX = "bitmex"
    BYBIT = "bybit"
    OKEX = "okex"


class DATA_TYPE(StrEnum):
    TRADES = "trades"
    INCREMENTAL_BOOK_L2 = "incremental_book_L2"
    BOOK_SNAPSHOT_25 = "book_snapshot_25"
    BOOK_SNAPSHOT_5 = "book_snapshot_5"
    OPTIONS_CHAIN = "options_chain"
    QUOTES = "quotes"
    DERIVATIVE_TICKER = "derivative_ticker"
    LIQUIDATIONS = "liquidations"


class TardisDataManager:
    """
    Out path schema:

    root_dir / exchange / data_type / year-month-day / symbol.csv.gz
    """

    def __init__(
        self,
        root_dir: str | Path = "./datasets",
        exchange: EXCHANGE = EXCHANGE.DERIBIT,
        format: str = "csv",
    ):
        self.root_dir = Path(root_dir)
        self.exchange = exchange
        self.format = format
        self.logger = logger.bind()

    @staticmethod
    def default_file_name(
        exchange: str, data_type: str, date: datetime, symbol: str, format: str
    ):
        """
        :exchange/:dataType/:year/:month/:day/:symbol.csv.gz

        NOTE: this will be passed to tardis-dev.datasets.download's get_filename parameter
        """
        return (
            f"{exchange}/{data_type}/{date.strftime('%Y-%m-%d')}/{symbol}.{format}.gz"
        )

    def get_path(
        self,
        data_type: DATA_TYPE,
        date: DATE_TYPE | None = None,
        symbol: str | None = None,
    ) -> Path:
        # Use unified date conversion utility
        date_str = to_date_string(date)

        path = self.root_dir / self.exchange / data_type

        if date_str is not None:
            path /= date_str
        else:
            return path

        if symbol is not None:
            path /= symbol + f".{self.format}.gz"
        else:
            return path

        return path

    # TODO: maybe add mode to return full path or return pandas Index or DateTimeIndex
    def list_symbols(
        self,
        data_type: DATA_TYPE,
        date: DATE_TYPE | None = None,
    ) -> list[str]:
        if date is None:
            date = self.list_dates(data_type)[-1]

        path = self.get_path(data_type, date)
        return sorted([f.stem for f in path.glob(f".{self.format}.gz")])

    def list_dates(
        self,
        data_type: DATA_TYPE,
    ) -> list[str]:

        path = self.get_path(data_type)
        return sorted([f.stem for f in path.iterdir() if f.is_dir()])

    def get_data(
        self,
        data_type: DATA_TYPE,
        date: DATA_TYPE,
        symbol: str,
    ) -> pd.DataFrame:
        path = self.get_path(data_type, date, symbol)
        match self.format:
            case "csv":
                df = pd.read_csv(path)
            case _:
                raise ValueError(f"Unsupported format: {self.format}")
        return df

    # === Online Data ===

    def download_data(
        self,
        data_type: DATA_TYPE,
        date: DATE_TYPE,
        symbol: str,
        skip_existing: bool = True,
        http_proxy: str | None = None,
    ) -> bool:
        from tardis_dev import datasets
        from dotenv import load_dotenv, find_dotenv
        import os

        _ = load_dotenv(find_dotenv())

        try:
            if skip_existing and self.get_path(data_type, date, symbol).exists():
                self.logger.info(
                    f"Data already exists: {self.get_path(data_type, date, symbol)}. Skip downloading."
                )
                return True
            datasets.download(
                exchange=self.exchange,
                data_types=[data_type],
                symbols=[symbol],
                from_date=date,
                to_date=date,
                download_dir=self.root_dir,
                get_filename=self.default_file_name,
                api_key=os.getenv("TARDIS_API_KEY"),
                http_proxy=http_proxy,
            )
        except Exception as e:
            self.logger.error(f"Error downloading data: {e}")
            return False
        return True

    def get_exchange_details(self, http_proxy: str | None = None) -> dict:
        from tardis_dev.get_exchange_details import get_exchange_details

        return get_exchange_details(self.exchange, http_proxy)

    def list_exchange_symbols(self) -> list[str]:
        # TODO: wrapper of get_exchange_details
        pass
