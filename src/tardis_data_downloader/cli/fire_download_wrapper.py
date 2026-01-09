"""
Tardis Data Downloader CLI

Provides commands for downloading market data from Tardis.dev.
Supports both direct downloads and config-file based downloads.
"""

import json
import shutil
import sys
from pathlib import Path

import fire
from dotenv import find_dotenv, load_dotenv
from tardis_dev import datasets
from tardis_dev.get_exchange_details import get_exchange_details

from tardis_data_downloader.data.data_manager import TardisDataManager

_ = load_dotenv(find_dotenv())


class TardisCLI:
    """Tardis Data Downloader CLI

    使用範例:
    ---------
    # 直接下載數據
    td-fire download 'deribit' 'trades,incremental_book_L2' 'BTC-PERPETUAL' '2023-01-01' '2023-01-02'

    # 使用配置文件下載
    td-fire config-download --config configs/download.yaml --profile hft_core

    # 增量下載
    td-fire incremental --config configs/download.yaml --profile hft_core

    # 查看下載狀態
    td-fire status --config configs/download.yaml

    # 估算存儲空間
    td-fire estimate --config configs/download.yaml --profile hft_core

    # 生成配置文件範例
    td-fire init-config --format yaml --output configs/download.yaml

    # 獲取交易所詳情
    td-fire get-exchange-details 'deribit'

    # 顯示幫助
    td-fire --help
    """

    # ========================
    # Direct Download Commands
    # ========================

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
        下載市場數據 (直接模式)

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

            print("開始下載數據...")
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
                get_filename=TardisDataManager.default_file_name,
            )

            print("下載完成！")

        except Exception as e:
            print(f"下載失敗: {e}", file=sys.stderr)
            sys.exit(1)

    # =============================
    # Config-based Download Commands
    # =============================

    def config_download(
        self,
        config: str,
        profile: str,
        dry_run: bool = False,
        root_dir: str = None,
        concurrency: int = None,
    ):
        """
        使用配置文件下載數據

        Args:
            config: 配置文件路徑 (YAML 或 TOML)
            profile: 要使用的 profile 名稱
            dry_run: 僅顯示將要下載的內容，不實際下載
            root_dir: 覆蓋配置中的存儲目錄
            concurrency: 覆蓋配置中的並發數量
        """
        try:
            from tardis_data_downloader.config.loader import ConfigLoader
            from tardis_data_downloader.download.orchestrator import DownloadOrchestrator

            # Load config
            loader = ConfigLoader(config)
            cfg = loader.load()

            # Apply CLI overrides
            if root_dir or concurrency:
                cfg = ConfigLoader.merge_cli_args(
                    cfg, root_dir=root_dir, concurrency=concurrency
                )

            # Create orchestrator and run
            orchestrator = DownloadOrchestrator(cfg)
            results = orchestrator.download_profile(profile, incremental=False, dry_run=dry_run)

            if dry_run:
                print("\n=== Dry Run Summary ===")
                print(f"Total files to download: {results['total_files']}")
                print("\nTasks:")
                for task in results.get("tasks", []):
                    print(
                        f"  - {task['exchange']}/{task['data_type']}/{task['symbol']}: "
                        f"{task['files_count']} files ({task['date_range']})"
                    )
            else:
                print("\n=== Download Complete ===")
                print(f"Success: {results['success']}")
                print(f"Failed: {results['failed']}")
                print(f"Skipped: {results['skipped']}")

        except Exception as e:
            print(f"下載失敗: {e}", file=sys.stderr)
            sys.exit(1)

    def incremental(
        self,
        config: str,
        profile: str,
        dry_run: bool = False,
    ):
        """
        增量下載 (從上次下載的位置繼續)

        Args:
            config: 配置文件路徑
            profile: Profile 名稱
            dry_run: 僅顯示將要下載的內容
        """
        try:
            from tardis_data_downloader.config.loader import ConfigLoader
            from tardis_data_downloader.download.orchestrator import DownloadOrchestrator

            loader = ConfigLoader(config)
            cfg = loader.load()

            orchestrator = DownloadOrchestrator(cfg)
            results = orchestrator.download_profile(profile, incremental=True, dry_run=dry_run)

            if dry_run:
                print("\n=== Incremental Dry Run ===")
                print(f"Total new files to download: {results['total_files']}")
                if results['total_files'] == 0:
                    print("All data is up to date!")
            else:
                print("\n=== Incremental Download Complete ===")
                print(f"Success: {results['success']}")
                print(f"Failed: {results['failed']}")

        except Exception as e:
            print(f"增量下載失敗: {e}", file=sys.stderr)
            sys.exit(1)

    def status(self, config: str, profile: str = None):
        """
        顯示下載狀態

        Args:
            config: 配置文件路徑
            profile: 可選，指定 profile 名稱
        """
        try:
            from tardis_data_downloader.config.loader import ConfigLoader
            from tardis_data_downloader.download.orchestrator import DownloadOrchestrator

            loader = ConfigLoader(config)
            cfg = loader.load()

            orchestrator = DownloadOrchestrator(cfg)
            status = orchestrator.get_status(profile)

            print("\n=== Download Status ===")
            print(f"Last updated: {status['last_updated']}")

            for name, profile_status in status["profiles"].items():
                print(f"\nProfile: {name}")
                print(f"  Total files: {profile_status['total_files']}")

                for exchange, symbols in profile_status["exchanges"].items():
                    print(f"\n  {exchange}:")
                    for symbol, data_types in symbols.items():
                        print(f"    {symbol}:")
                        for data_type, last_date in data_types.items():
                            print(f"      {data_type}: last={last_date}")

            if not status["profiles"]:
                print("\nNo download history found.")
                print("Run 'td-fire config-download' to start downloading.")

        except Exception as e:
            print(f"獲取狀態失敗: {e}", file=sys.stderr)
            sys.exit(1)

    def estimate(self, config: str, profile: str):
        """
        估算存儲空間需求

        Args:
            config: 配置文件路徑
            profile: Profile 名稱
        """
        try:
            from tardis_data_downloader.config.loader import ConfigLoader
            from tardis_data_downloader.download.orchestrator import DownloadOrchestrator

            loader = ConfigLoader(config)
            cfg = loader.load()

            orchestrator = DownloadOrchestrator(cfg)
            estimate = orchestrator.estimate_storage(profile)

            print("\n=== Storage Estimate ===")
            print(f"Profile: {estimate['profile']}")
            print(f"Date range: {estimate['date_range']}")
            print(f"Days: {estimate['days']}")
            print(f"Total files: {estimate['total_files']}")
            print(f"Estimated size: {estimate['estimated_size_gb']} GB")
            print(f"\nNote: {estimate['note']}")

            print("\nBreakdown by exchange and data type:")
            for exchange, data_types in estimate["breakdown"].items():
                print(f"\n  {exchange}:")
                for data_type, info in data_types.items():
                    print(
                        f"    {data_type}: {info['files']} files "
                        f"(~{info['estimated_size_mb']} MB)"
                    )

        except Exception as e:
            print(f"估算失敗: {e}", file=sys.stderr)
            sys.exit(1)

    def init_config(
        self,
        format: str = "yaml",
        output: str = None,
    ):
        """
        生成配置文件範例

        Args:
            format: 配置格式 ('yaml' 或 'toml')
            output: 輸出文件路徑 (預設: configs/download.yaml 或 .toml)
        """
        try:
            # Determine template source
            template_dir = Path(__file__).parent.parent / "config" / "templates"

            if format.lower() == "yaml":
                template_file = template_dir / "download.yaml"
                default_output = "configs/download.yaml"
            elif format.lower() == "toml":
                template_file = template_dir / "download.toml"
                default_output = "configs/download.toml"
            else:
                print(f"不支持的格式: {format}. 請使用 'yaml' 或 'toml'", file=sys.stderr)
                sys.exit(1)

            output_path = Path(output) if output else Path(default_output)

            # Create output directory
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy template
            if template_file.exists():
                shutil.copy(template_file, output_path)
                print(f"已創建配置文件: {output_path}")
                print("\n請編輯配置文件以設置您的下載需求:")
                print(f"  - 修改 profiles 中的 exchanges, symbols, date_range")
                print(f"  - 設置 storage.root_dir 為您的數據目錄")
                print(f"\n然後運行: td-fire config-download --config {output_path} --profile hft_core")
            else:
                print(f"模板文件不存在: {template_file}", file=sys.stderr)
                sys.exit(1)

        except Exception as e:
            print(f"創建配置文件失敗: {e}", file=sys.stderr)
            sys.exit(1)

    def list_profiles(self, config: str):
        """
        列出配置文件中的所有 profiles

        Args:
            config: 配置文件路徑
        """
        try:
            from tardis_data_downloader.config.loader import ConfigLoader

            loader = ConfigLoader(config)
            cfg = loader.load()

            print("\n=== Available Profiles ===")
            for name in cfg.list_profiles():
                profile = cfg.get_profile(name)
                print(f"\n{name}:")
                print(f"  Description: {profile.description}")
                print(f"  Exchanges: {', '.join(profile.exchanges)}")
                print(f"  Data types: {', '.join(profile.data_types)}")
                print(f"  Date range: {profile.date_range.start} to {profile.date_range.get_end_date()}")

        except Exception as e:
            print(f"列出 profiles 失敗: {e}", file=sys.stderr)
            sys.exit(1)

    # =======================
    # Information Commands
    # =======================

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
        print("常見支持的交易所 (Perpetuals 訂閱):")
        exchanges = [
            ("binance-futures", "Binance USDT-M Futures"),
            ("binance-delivery", "Binance COIN-M Futures"),
            ("bybit", "Bybit Perpetuals"),
            ("deribit", "Deribit (BTC/ETH)"),
            ("okex-swap", "OKX Swap"),
            ("bitmex", "BitMEX"),
            ("huobi-dm-swap", "Huobi COIN Swap"),
            ("huobi-dm-linear-swap", "Huobi USDT Swap"),
            ("gate-io-futures", "Gate.io Futures"),
            ("phemex", "Phemex"),
            ("dydx", "dYdX"),
            ("delta", "Delta Exchange"),
        ]
        for exchange_id, name in exchanges:
            print(f"  - {exchange_id:25s} ({name})")

    def list_data_types(self):
        """列出所有可用的數據類型"""
        print("可用的數據類型:")
        data_types = [
            ("trades", "逐筆成交數據"),
            ("quotes", "Top-of-Book 最優報價"),
            ("incremental_book_L2", "L2 增量訂單簿 (體積大)"),
            ("book_snapshot_25", "Top 25 訂單簿快照"),
            ("book_snapshot_5", "Top 5 訂單簿快照"),
            ("derivative_ticker", "衍生品 Ticker (funding rate, mark price)"),
            ("liquidations", "強平數據"),
            ("options_chain", "選擇權鏈 (僅 OPTIONS)"),
        ]
        for data_type, description in data_types:
            print(f"  - {data_type:25s} {description}")


def main():
    fire.Fire(TardisCLI)


if __name__ == "__main__":
    main()
