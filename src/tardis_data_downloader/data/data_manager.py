from pathlib import Path
from enum import StrEnum
import pandas as pd
from datetime import datetime
from tardis_data_downloader.utils.date_utils import DATE_TYPE, to_date_string
from loguru import logger
import requests
import time
import hashlib
from tardis_data_downloader.data.models import SYMBOL_TYPE, SymbolInfo
import tardis_data_downloader.utils as utils


class EXCHANGE(StrEnum):
    BITMEX = "bitmex"
    DERIBIT = "deribit"
    BINANCE_FUTURES = "binance-futures"
    BINANCE_DELIVERY = "binance-delivery"
    BINANCE_OPTIONS = "binance-options"
    BINANCE_EUROPEAN_OPTIONS = "binance-european-options"
    BINANCE = "binance"
    FTX = "ftx"
    OKEX_FUTURES = "okex-futures"
    OKEX_OPTIONS = "okex-options"
    OKEX_SWAP = "okex-swap"
    OKEX = "okex"
    OKEX_SPREADS = "okex-spreads"
    HUOBI_DM = "huobi-dm"
    HUOBI_DM_SWAP = "huobi-dm-swap"
    HUOBI_DM_LINEAR_SWAP = "huobi-dm-linear-swap"
    HUOBI_DM_OPTIONS = "huobi-dm-options"
    HUOBI = "huobi"
    BITFINEX_DERIVATIVES = "bitfinex-derivatives"
    BITFINEX = "bitfinex"
    COINBASE = "coinbase"
    COINBASE_INTERNATIONAL = "coinbase-international"
    CRYPTOFACILITIES = "cryptofacilities"
    KRAKEN = "kraken"
    BITSTAMP = "bitstamp"
    GEMINI = "gemini"
    POLONIEX = "poloniex"
    UPBIT = "upbit"
    BYBIT = "bybit"
    BYBIT_SPOT = "bybit-spot"
    BYBIT_OPTIONS = "bybit-options"
    PHEMEX = "phemex"
    ASCENDEX = "ascendex"
    KUCOIN = "kucoin"
    KUCOIN_FUTURES = "kucoin-futures"
    SERUM = "serum"
    MANGO = "mango"
    DYDX = "dydx"
    DYDX_V4 = "dydx-v4"
    DELTA = "delta"
    FTX_US = "ftx-us"
    BINANCE_US = "binance-us"
    GATE_IO_FUTURES = "gate-io-futures"
    GATE_IO = "gate-io"
    OKCOIN = "okcoin"
    BITFLYER = "bitflyer"
    HITBTC = "hitbtc"
    COINFLEX = "coinflex"
    CRYPTO_COM = "crypto-com"
    CRYPTO_COM_DERIVATIVES = "crypto-com-derivatives"
    BINANCE_JERSEY = "binance-jersey"
    BINANCE_DEX = "binance-dex"
    STAR_ATLAS = "star-atlas"
    BITNOMIAL = "bitnomial"
    WOO_X = "woo-x"
    BLOCKCHAIN_COM = "blockchain-com"
    BITGET = "bitget"
    BITGET_FUTURES = "bitget-futures"
    HYPERLIQUID = "hyperliquid"


class DATA_TYPE(StrEnum):
    TRADES = "trades"
    INCREMENTAL_BOOK_L2 = "incremental_book_L2"
    BOOK_SNAPSHOT_25 = "book_snapshot_25"
    BOOK_SNAPSHOT_5 = "book_snapshot_5"
    OPTIONS_CHAIN = "options_chain"
    QUOTES = "quotes"
    DERIVATIVE_TICKER = "derivative_ticker"
    LIQUIDATIONS = "liquidations"


class SimpleCache:
    """
    Simple in-memory cache with TTL support

    TODO: default unlimited ttl
    """

    def __init__(self, default_ttl_seconds: int = 3600):
        self.cache = {}
        self.default_ttl = default_ttl_seconds

    def _get_cache_key(self, url: str) -> str:
        """Generate a cache key from URL"""
        return hashlib.md5(url.encode()).hexdigest()

    def get(self, url: str) -> dict | None:
        """Get cached data if available and not expired"""
        key = self._get_cache_key(url)
        if key in self.cache:
            data, timestamp, ttl = self.cache[key]
            if time.time() - timestamp < ttl:
                return data
            else:
                # Remove expired entry
                del self.cache[key]
        return None

    def set(self, url: str, data: dict, ttl_seconds: int | None = None) -> None:
        """Cache data with optional TTL"""
        key = self._get_cache_key(url)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        self.cache[key] = (data, time.time(), ttl)

    def clear(self) -> None:
        """Clear all cached data"""
        self.cache.clear()

    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_entries = len(self.cache)
        expired_entries = 0
        current_time = time.time()

        for key, (data, timestamp, ttl) in self.cache.items():
            if current_time - timestamp >= ttl:
                expired_entries += 1

        return {
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "active_entries": total_entries - expired_entries,
        }


class TardisApi:
    """
    Tardis API client with optional caching support
    """

    def __init__(
        self,
        http_proxy: str | None = None,
        enable_cache: bool = True,
        cache_ttl_seconds: int = 3600,
    ):
        self.http_proxy = http_proxy
        self.enable_cache = enable_cache
        self.cache_ttl_seconds = cache_ttl_seconds

        if self.enable_cache:
            self.cache = SimpleCache(default_ttl_seconds=cache_ttl_seconds)
        else:
            self.cache = None

    def _call_api(self, url: str) -> dict:
        """Make a GET request to the Tardis API with proxy support and optional caching"""
        # Check cache first if enabled
        if self.enable_cache and self.cache:
            cached_data = self.cache.get(url)
            if cached_data is not None:
                logger.debug(f"Cache hit for URL: {url}")
                return cached_data
            logger.debug(f"Cache miss for URL: {url}")

        # Make the API call
        proxies = (
            {"http": self.http_proxy, "https": self.http_proxy}
            if self.http_proxy
            else None
        )
        response = requests.get(url, proxies=proxies)
        response.raise_for_status()
        data = response.json()

        # Cache the response if caching is enabled
        if self.enable_cache and self.cache:
            self.cache.set(url, data, self.cache_ttl_seconds)
            logger.debug(f"Cached response for URL: {url}")

        return data

    def get_exchange_details(self, exchange: str) -> dict:
        """Get details for a specific exchange"""
        url = f"https://api.tardis.dev/v1/exchanges/{exchange}"
        try:
            return self._call_api(url)
        except Exception as e:
            logger.error(f"Error fetching exchange details for {exchange}: {e}")
            return {}

    def get_exchanges(self) -> dict:
        """Get list of all available exchanges"""
        url = "https://api.tardis.dev/v1/exchanges/"
        try:
            return self._call_api(url)
        except Exception as e:
            logger.error(f"Error fetching exchanges list: {e}")
            return {}

    def clear_cache(self) -> None:
        """Clear all cached data"""
        if self.enable_cache and self.cache:
            self.cache.clear()
            logger.info("Cache cleared successfully")
        else:
            logger.warning("Caching is not enabled")

    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        if self.enable_cache and self.cache:
            return self.cache.get_stats()
        else:
            return {"error": "Caching is not enabled"}

    def invalidate_cache_entry(self, url: str) -> bool:
        """Invalidate a specific cache entry by URL"""
        if self.enable_cache and self.cache:
            # Since our SimpleCache doesn't have a direct invalidate method,
            # we'll use a workaround by checking if the URL exists and then
            # forcing a cache miss by temporarily modifying the cache
            key = hashlib.md5(url.encode()).hexdigest()
            if key in self.cache.cache:
                del self.cache.cache[key]
                logger.debug(f"Invalidated cache entry for URL: {url}")
                return True
            else:
                logger.debug(f"No cache entry found for URL: {url}")
                return False
        else:
            logger.warning("Caching is not enabled")
            return False

    def is_cache_enabled(self) -> bool:
        """Check if caching is enabled"""
        return self.enable_cache


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
        api_key: str | None = None,  # NOTE: for download data only
        http_proxy: str | None = None,
        enable_cache: bool = True,
        cache_ttl_seconds: int = 3600,
    ):
        self.root_dir = Path(root_dir)
        self.exchange = exchange
        self.format = format
        self.logger = logger.bind()
        self.api = TardisApi(
            http_proxy=http_proxy,
            enable_cache=enable_cache,
            cache_ttl_seconds=cache_ttl_seconds,
            # TODO: not sure if we want to pass api_key to TardisApi (construct Bearer token)
        )

        from dotenv import load_dotenv, find_dotenv
        import os

        _ = load_dotenv(find_dotenv())

        self.api_key = api_key or os.getenv("TARDIS_API_KEY")

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
                api_key=self.api_key,
                http_proxy=self.api.http_proxy,
            )
        except Exception as e:
            self.logger.error(f"Error downloading data: {e}")
            return False
        return True

    def batch_download_by_date_range(
        self,
        data_types: list[DATA_TYPE] | None = None,
        symbols: list[str] | None = None,
        symbol_types: list[SYMBOL_TYPE] | None = None,
        start_date: DATE_TYPE | None = None,
        end_date: DATE_TYPE | None = None,
        sequential: bool = True,
    ) -> pd.Series | bool:
        """
        TODO: if None then use all
        TODO: if sequential then use tqdm progress bar
        TODO: even if non-sequential, still need to check completeness of each symbol/data-type/date
        TODO: add skip_existing option (but maybe this only works for sequential mode)
        """
        # if symbols is not None and symbol_types is not None:
        #     raise ValueError("symbol and symbol_types cannot be provided together")

        # if data_types is None:
        # TODO: list exchange data types
        #     data_types = self.list_data_types()

        # if symbols is None:
        #     symbols = self.list_exchange_symbols(symbol_types)

        if sequential:
            results = {}
            for symbol in symbols:
                for data_type in data_types:
                    # NOTE: inclusive left is to match the behavior of tardis-dev.datasets.download
                    for date in utils.date_range(
                        start_date, end_date, inclusive="left"
                    ):
                        results[(data_type, date, symbol)] = self.download_data(
                            data_type, date, symbol
                        )
            return results
        else:
            import asyncio
            import concurrent.futures
            from tardis_dev.datasets.download import download_async, default_timeout

            async def _run_download():
                await download_async(
                    exchange=self.exchange,
                    data_types=data_types,
                    symbols=symbols,
                    from_date=start_date,
                    to_date=end_date,
                    format=self.format,
                    api_key=self.api_key,
                    download_dir=self.root_dir,
                    get_filename=self.default_file_name,
                    timeout=default_timeout,
                    download_url_base="datasets.tardis.dev",
                    concurrency=5,
                    http_proxy=self.api.http_proxy,
                )

            try:
                # Check if we're in an existing event loop (e.g., Jupyter notebook)
                try:
                    asyncio.get_running_loop()
                    # We're in a running event loop, run in a thread to avoid event loop conflicts
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, _run_download())
                        future.result()  # Wait for completion
                except RuntimeError:
                    # No running event loop, use asyncio.run directly
                    asyncio.run(_run_download())
            except Exception as e:
                self.logger.error(f"Error downloading data: {e}")
                return False
            return True

    def list_exchanges(self) -> list[str]:
        raw_exchanges = self.api.get_exchanges()
        exchanges = [e["id"] for e in raw_exchanges]
        if not all(exchange in EXCHANGE for exchange in exchanges):
            self.logger.warning(
                f"Found exchanges not in EXCHANGE Enum, maybe there are some new exchanges, please check."
            )
        return exchanges

    def list_exchange_symbols(
        self, symbol_types: list[SYMBOL_TYPE] | None = None
    ) -> list[str]:
        raw_exchange_details = self.api.get_exchange_details(self.exchange)
        symbols = [symbol for symbol in raw_exchange_details["availableSymbols"]]
        if symbol_types is not None:
            symbols = [symbol for symbol in symbols if symbol["type"] in symbol_types]
        return [symbol["id"] for symbol in symbols]

    def list_exchange_symbol_infos(
        self, symbol_types: list[SYMBOL_TYPE] | None = None
    ) -> list[SymbolInfo]:
        # BUG:
        # pydantic_core._pydantic_core.ValidationError: 1 validation error for SymbolInfo
        # availableTo
        # Field required [type=missing, input_value={'id': 'BTC-PERPETUAL', '...19-03-30T00:00:00.000Z'}, input_type=dict]
        #     For further information visit https://errors.pydantic.dev/2.11/v/missing
        raw_exchange_details = self.api.get_exchange_details(self.exchange)
        symbols = [
            SymbolInfo(**symbol) for symbol in raw_exchange_details["availableSymbols"]
        ]
        if symbol_types is not None:
            symbols = [symbol for symbol in symbols if symbol.type in symbol_types]
        return symbols

    # === Cache Management Methods ===
    def clear_cache(self) -> None:
        """Clear all cached API data"""
        self.api.clear_cache()

    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        return self.api.get_cache_stats()

    def is_cache_enabled(self) -> bool:
        """Check if caching is enabled"""
        return self.api.is_cache_enabled()


if __name__ == "__main__":
    # python -m src.tardis_data_downloader.data.data_manager
    manager = TardisDataManager()
    print(manager.list_exchanges())
    print(len(manager.list_exchanges()))
    print(manager.list_exchange_symbols())
    print(
        manager.batch_download_by_date_range(
            data_types=[DATA_TYPE.TRADES],
            symbols=["BTC-PERPETUAL"],
            start_date="2025-09-15",
            end_date="2025-09-16",
            sequential=False,
        )
    )
    import ipdb

    ipdb.set_trace()
