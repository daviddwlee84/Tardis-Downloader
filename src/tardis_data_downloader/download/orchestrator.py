"""
Download orchestrator for coordinating batch and incremental downloads.

Integrates with config, state tracking, and the core download functionality.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Generator

from loguru import logger

from tardis_data_downloader.config.models import DownloadConfig, DownloadProfile
from tardis_data_downloader.download.state import DownloadState


def date_range(
    start: str | date, end: str | date, inclusive: str = "left"
) -> Generator[date, None, None]:
    """
    Generate dates between start and end.

    Args:
        start: Start date
        end: End date
        inclusive: "left", "right", "both", or "neither"

    Yields:
        date objects in range
    """
    if isinstance(start, str):
        start = date.fromisoformat(start)
    if isinstance(end, str):
        end = date.fromisoformat(end)

    current = start
    while current < end:
        yield current
        current += timedelta(days=1)

    if inclusive in ("right", "both"):
        yield end


class DownloadOrchestrator:
    """
    Orchestrates downloads based on configuration.

    Handles:
    - Batch downloads for full date ranges
    - Incremental downloads (continue from last state)
    - Progress tracking
    - Parallel execution
    """

    def __init__(
        self,
        config: DownloadConfig,
        state: DownloadState | None = None,
    ):
        """
        Initialize orchestrator.

        Args:
            config: Download configuration
            state: Optional state tracker (created from config if not provided)
        """
        self.config = config
        self.state = state or DownloadState(config.incremental.state_file)

    def _get_file_path(
        self,
        exchange: str,
        data_type: str,
        download_date: date,
        symbol: str,
    ) -> Path:
        """Get the expected file path for a download."""
        return (
            Path(self.config.storage.root_dir)
            / exchange
            / data_type
            / download_date.strftime("%Y-%m-%d")
            / f"{symbol}.{self.config.storage.format}.gz"
        )

    def _file_exists(
        self,
        exchange: str,
        data_type: str,
        download_date: date,
        symbol: str,
    ) -> bool:
        """Check if a file already exists."""
        return self._get_file_path(exchange, data_type, download_date, symbol).exists()

    def download_profile(
        self,
        profile_name: str,
        incremental: bool = False,
        dry_run: bool = False,
    ) -> dict:
        """
        Download data for a profile.

        Args:
            profile_name: Name of the profile to download
            incremental: If True, continue from last downloaded date
            dry_run: If True, only calculate what would be downloaded

        Returns:
            Download results summary
        """
        profile = self.config.get_profile(profile_name)

        logger.info(f"Starting download for profile: {profile_name}")
        logger.info(f"Description: {profile.description}")

        # Calculate download tasks
        tasks = self._calculate_tasks(profile_name, profile, incremental)

        if dry_run:
            return self._dry_run_summary(tasks)

        # Execute downloads
        return self._execute_downloads(profile_name, tasks)

    def _calculate_tasks(
        self,
        profile_name: str,
        profile: DownloadProfile,
        incremental: bool,
    ) -> list[dict]:
        """
        Calculate all download tasks for a profile.

        Returns:
            List of task dicts with exchange, data_type, symbol, dates
        """
        tasks = []
        end_date = profile.date_range.get_end_date()

        for exchange in profile.exchanges:
            symbols = profile.symbols.get(exchange, [])

            for symbol in symbols:
                for data_type in profile.data_types:
                    # Determine start date
                    if incremental and self.config.incremental.auto_continue:
                        last_date = self.state.get_last_date(
                            profile_name, exchange, symbol, data_type
                        )
                        if last_date:
                            # Start from day after last downloaded
                            start = (
                                date.fromisoformat(last_date) + timedelta(days=1)
                            ).isoformat()
                        else:
                            start = profile.date_range.start
                    else:
                        start = profile.date_range.start

                    # Generate dates
                    dates_to_download = []
                    for d in date_range(start, end_date, inclusive="left"):
                        if self.config.download.skip_existing:
                            if self._file_exists(exchange, data_type, d, symbol):
                                continue
                        dates_to_download.append(d)

                    if dates_to_download:
                        tasks.append(
                            {
                                "exchange": exchange,
                                "data_type": data_type,
                                "symbol": symbol,
                                "dates": dates_to_download,
                                "start": min(dates_to_download),
                                "end": max(dates_to_download),
                            }
                        )

        return tasks

    def _dry_run_summary(self, tasks: list[dict]) -> dict:
        """Generate a summary for dry run."""
        total_files = sum(len(t["dates"]) for t in tasks)

        summary = {
            "mode": "dry_run",
            "total_files": total_files,
            "tasks": [],
        }

        for task in tasks:
            summary["tasks"].append(
                {
                    "exchange": task["exchange"],
                    "data_type": task["data_type"],
                    "symbol": task["symbol"],
                    "files_count": len(task["dates"]),
                    "date_range": f"{task['start']} to {task['end']}",
                }
            )

        logger.info(f"Dry run: {total_files} files would be downloaded")
        return summary

    def _execute_downloads(
        self,
        profile_name: str,
        tasks: list[dict],
    ) -> dict:
        """Execute download tasks."""
        from tardis_dev.datasets.download import download as tardis_download

        import os
        from dotenv import load_dotenv, find_dotenv

        load_dotenv(find_dotenv())
        api_key = os.getenv("TARDIS_API_KEY")

        if not api_key:
            raise ValueError(
                "TARDIS_API_KEY environment variable not set. "
                "Please set it or add to .env file."
            )

        results = {
            "mode": "download",
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "details": [],
        }

        total_files = sum(len(t["dates"]) for t in tasks)
        logger.info(f"Downloading {total_files} files...")

        try:
            from tqdm import tqdm

            progress = tqdm(total=total_files, desc="Downloading")
        except ImportError:
            progress = None
            logger.warning("tqdm not installed. Progress bar disabled.")

        for task in tasks:
            exchange = task["exchange"]
            data_type = task["data_type"]
            symbol = task["symbol"]
            dates = task["dates"]

            if not dates:
                continue

            start_date = min(dates).isoformat()
            end_date = (max(dates) + timedelta(days=1)).isoformat()

            try:
                logger.debug(
                    f"Downloading {exchange}/{data_type}/{symbol} "
                    f"from {start_date} to {end_date}"
                )

                tardis_download(
                    exchange=exchange,
                    data_types=[data_type],
                    symbols=[symbol],
                    from_date=start_date,
                    to_date=end_date,
                    format=self.config.storage.format,
                    api_key=api_key,
                    download_dir=self.config.storage.root_dir,
                    concurrency=self.config.download.concurrency,
                    get_filename=self._get_filename,
                )

                # Update state
                self.state.update(
                    profile=profile_name,
                    exchange=exchange,
                    symbol=symbol,
                    data_type=data_type,
                    last_date=max(dates).isoformat(),
                    files_count=len(dates),
                )
                self.state.save()

                results["success"] += len(dates)
                results["details"].append(
                    {
                        "exchange": exchange,
                        "data_type": data_type,
                        "symbol": symbol,
                        "status": "success",
                        "files": len(dates),
                    }
                )

            except Exception as e:
                logger.error(
                    f"Failed to download {exchange}/{data_type}/{symbol}: {e}"
                )
                results["failed"] += len(dates)
                results["details"].append(
                    {
                        "exchange": exchange,
                        "data_type": data_type,
                        "symbol": symbol,
                        "status": "failed",
                        "error": str(e),
                    }
                )

            if progress:
                progress.update(len(dates))

        if progress:
            progress.close()

        logger.info(
            f"Download complete: {results['success']} success, "
            f"{results['failed']} failed, {results['skipped']} skipped"
        )

        return results

    @staticmethod
    def _get_filename(
        exchange: str,
        data_type: str,
        download_date: datetime,
        symbol: str,
        format: str,
    ) -> str:
        """
        Generate filename in our standard format.

        Format: exchange/data_type/YYYY-MM-DD/symbol.csv.gz
        """
        return (
            f"{exchange}/{data_type}/"
            f"{download_date.strftime('%Y-%m-%d')}/{symbol}.{format}.gz"
        )

    def estimate_storage(self, profile_name: str) -> dict:
        """
        Estimate storage requirements for a profile.

        Note: This is a rough estimate based on average file sizes.
        Actual sizes vary significantly by exchange, symbol, and date.

        Returns:
            Estimation dict with file counts and size estimates
        """
        profile = self.config.get_profile(profile_name)

        # Average compressed file sizes (rough estimates in MB)
        size_estimates = {
            "trades": 5,  # ~5 MB per day
            "quotes": 2,  # ~2 MB per day
            "incremental_book_L2": 50,  # ~50 MB per day (varies a lot)
            "book_snapshot_25": 20,  # ~20 MB per day
            "book_snapshot_5": 10,  # ~10 MB per day
            "derivative_ticker": 1,  # ~1 MB per day
            "liquidations": 0.5,  # ~0.5 MB per day
            "options_chain": 5,  # ~5 MB per day
        }

        total_files = 0
        total_size_mb = 0
        breakdown = {}

        end_date = profile.date_range.get_end_date()
        start = date.fromisoformat(profile.date_range.start)
        end = date.fromisoformat(end_date)
        days = (end - start).days

        for exchange in profile.exchanges:
            symbols = profile.symbols.get(exchange, [])
            breakdown[exchange] = {}

            for data_type in profile.data_types:
                files = len(symbols) * days
                size = files * size_estimates.get(data_type, 5)

                breakdown[exchange][data_type] = {
                    "files": files,
                    "estimated_size_mb": size,
                }

                total_files += files
                total_size_mb += size

        return {
            "profile": profile_name,
            "date_range": f"{profile.date_range.start} to {end_date}",
            "days": days,
            "total_files": total_files,
            "estimated_size_mb": total_size_mb,
            "estimated_size_gb": round(total_size_mb / 1024, 2),
            "breakdown": breakdown,
            "note": "Sizes are rough estimates. Actual sizes vary significantly.",
        }

    def get_status(self, profile_name: str | None = None) -> dict:
        """
        Get download status summary.

        Args:
            profile_name: Optional specific profile, or all profiles if None

        Returns:
            Status summary dict
        """
        self.state.load()

        if profile_name:
            profiles = [profile_name]
        else:
            profiles = list(self.state.state.profiles.keys())

        status = {
            "last_updated": self.state.state.last_updated,
            "profiles": {},
        }

        for name in profiles:
            summary = self.state.get_profile_summary(name)
            total_files = self.state.get_total_files(name)

            status["profiles"][name] = {
                "total_files": total_files,
                "exchanges": summary,
            }

        return status
