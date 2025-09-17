import fire
from tardis_dev import datasets
from tardis_dev.get_exchange_details import get_exchange_details
from dotenv import load_dotenv, find_dotenv
import sys


_ = load_dotenv(find_dotenv())


class TardisCLI:
    """Tardis Data Downloader CLI

    使用範例:
    ---------
    # 下載數據
    td-fire download 'deribit' 'trades,incremental_book_L2' 'BTC-PERPETUAL' '2023-01-01' '2023-01-02'

    # 獲取交易所詳情
    td-fire get-exchange-details 'deribit'

    # 顯示幫助
    td-fire --help
    td-fire download --help
    """

    def download(
        self,
        exchange: str,
        data_types: str,
        symbols: str,
        from_date: str,
        to_date: str,
        format: str = "csv",
        api_key: str = "",
        download_dir: str = "./datasets",
        download_url_base: str = "datasets.tardis.dev",
        concurrency: int = 5,
        http_proxy: str = None,
    ):
        """
        下載市場數據

        Args:
            exchange: 交易所名稱 (例如: 'deribit', 'binance', 'bitmex')
            data_types: 數據類型，用逗號分隔 (例如: 'trades,incremental_book_L2')
            symbols: 交易對，用逗號分隔 (例如: 'BTC-PERPETUAL,BTC-27DEC23')
            from_date: 開始日期 (ISO格式，例如: '2023-01-01')
            to_date: 結束日期 (ISO格式，例如: '2023-01-02')
            format: 數據格式 (預設: 'csv')
            api_key: API 金鑰 (可選)
            download_dir: 下載目錄 (預設: './datasets')
            download_url_base: 下載 URL 基礎 (預設: 'datasets.tardis.dev')
            concurrency: 並發下載數量 (預設: 5)
            http_proxy: HTTP 代理 (可選)
        """
        try:
            # 將逗號分隔的字符串轉換為列表
            data_types_list = [dt.strip() for dt in data_types.split(",")]
            symbols_list = [sym.strip() for sym in symbols.split(",")]

            print(f"開始下載數據...")
            print(f"交易所: {exchange}")
            print(f"數據類型: {', '.join(data_types_list)}")
            print(f"交易對: {', '.join(symbols_list)}")
            print(f"日期範圍: {from_date} 到 {to_date}")
            print(f"格式: {format}")
            print(f"下載目錄: {download_dir}")
            print()

            datasets.download(
                exchange=exchange,
                data_types=data_types_list,
                symbols=symbols_list,
                from_date=from_date,
                to_date=to_date,
                format=format,
                api_key=api_key,
                download_dir=download_dir,
                download_url_base=download_url_base,
                concurrency=concurrency,
                http_proxy=http_proxy,
            )

            print("下載完成！")

        except Exception as e:
            print(f"下載失敗: {e}", file=sys.stderr)
            sys.exit(1)

    def get_exchange_details(self, exchange: str, http_proxy: str = None):
        """
        獲取交易所詳情

        Args:
            exchange: 交易所名稱 (例如: 'deribit', 'binance')
            http_proxy: HTTP 代理 (可選)
        """
        try:
            print(f"獲取 {exchange} 交易所詳情...")
            details = get_exchange_details(exchange, http_proxy)

            print("\n交易所詳情:")
            print(f"名稱: {details.get('name', 'N/A')}")
            print(f"ID: {details.get('id', 'N/A')}")
            print(f"可用數據類型: {', '.join(details.get('availableDataTypes', []))}")
            print(f"可用交易對數量: {len(details.get('availableSymbols', []))}")

            if details.get("availableSymbols"):
                print("\n前 10 個可用交易對:")
                for symbol in details["availableSymbols"][:10]:
                    print(f"  - {symbol}")

        except Exception as e:
            print(f"獲取交易所詳情失敗: {e}", file=sys.stderr)
            sys.exit(1)

    def list_exchanges(self):
        """列出所有支持的交易所"""
        print("常見支持的交易所:")
        exchanges = [
            "deribit",
            "binance",
            "binance-futures",
            "binance-delivery",
            "bitmex",
            "bybit",
            "okex",
            "huobi",
            "kraken",
            "ftx",
        ]
        for exchange in exchanges:
            print(f"  - {exchange}")


def main():
    fire.Fire(TardisCLI)


if __name__ == "__main__":
    main()
