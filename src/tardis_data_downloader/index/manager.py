"""
Metadata index manager for building and querying the data index.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Generator

from loguru import logger

from tardis_data_downloader.index.models import (
    DataTypeIndex,
    ExchangeIndex,
    IndexQueryResult,
    MetadataIndex,
    SymbolIndex,
)


class MetadataIndexManager:
    """
    Manages the metadata index for downloaded data files.

    The index tracks:
    - All available exchanges, data types, and symbols
    - Date ranges for each combination
    - File counts and sizes
    """

    def __init__(
        self,
        root_dir: str | Path,
        index_file: str | Path | None = None,
    ):
        """
        Initialize the index manager.

        Args:
            root_dir: Root directory containing the data
            index_file: Path to the index file. Defaults to root_dir/.tardis_index.json
        """
        self.root_dir = Path(root_dir)
        self.index_file = (
            Path(index_file)
            if index_file
            else self.root_dir / ".tardis_index.json"
        )
        self._index: MetadataIndex | None = None

    def load(self) -> MetadataIndex:
        """Load index from file or create empty index."""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._index = MetadataIndex.model_validate(data)
                logger.debug(f"Loaded index from {self.index_file}")
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Failed to load index file: {e}. Starting fresh.")
                self._index = MetadataIndex(root_dir=str(self.root_dir))
        else:
            logger.debug(f"No index file found at {self.index_file}. Starting fresh.")
            self._index = MetadataIndex(root_dir=str(self.root_dir))
        return self._index

    def save(self) -> None:
        """Save current index to file."""
        if self._index is None:
            return

        self._index.last_updated = datetime.utcnow().isoformat() + "Z"
        self._index.recalculate_totals()

        # Ensure parent directory exists
        self.index_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(self._index.model_dump(), f, indent=2)
        logger.info(f"Saved index to {self.index_file}")

    @property
    def index(self) -> MetadataIndex:
        """Get current index (load if not loaded)."""
        if self._index is None:
            return self.load()
        return self._index

    def build(self, show_progress: bool = True) -> MetadataIndex:
        """
        Build the index by scanning the root directory.

        Expected directory structure:
        root_dir/
          exchange/
            data_type/
              YYYY-MM-DD/
                SYMBOL.csv.gz

        Args:
            show_progress: Whether to show progress bar

        Returns:
            The built MetadataIndex
        """
        logger.info(f"Building index from {self.root_dir}")

        self._index = MetadataIndex(root_dir=str(self.root_dir))

        if not self.root_dir.exists():
            logger.warning(f"Root directory does not exist: {self.root_dir}")
            return self._index

        # Scan exchanges
        exchanges = [
            d for d in self.root_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]

        try:
            from tqdm import tqdm
            exchange_iter = tqdm(exchanges, desc="Scanning exchanges") if show_progress else exchanges
        except ImportError:
            exchange_iter = exchanges

        for exchange_dir in exchange_iter:
            exchange_name = exchange_dir.name
            self._index.exchanges[exchange_name] = ExchangeIndex()

            # Scan data types
            data_type_dirs = [
                d for d in exchange_dir.iterdir()
                if d.is_dir() and not d.name.startswith(".")
            ]

            for data_type_dir in data_type_dirs:
                data_type_name = data_type_dir.name
                self._index.exchanges[exchange_name].data_types[data_type_name] = DataTypeIndex()

                # Collect all files by symbol
                symbol_files: dict[str, list[tuple[str, int]]] = {}  # symbol -> [(date, size), ...]

                # Scan date directories
                date_dirs = [
                    d for d in data_type_dir.iterdir()
                    if d.is_dir() and not d.name.startswith(".")
                ]

                for date_dir in date_dirs:
                    date_str = date_dir.name  # YYYY-MM-DD

                    # Scan files
                    for file_path in date_dir.iterdir():
                        if file_path.is_file() and file_path.name.endswith(".csv.gz"):
                            symbol = file_path.name.replace(".csv.gz", "")
                            size = file_path.stat().st_size

                            if symbol not in symbol_files:
                                symbol_files[symbol] = []
                            symbol_files[symbol].append((date_str, size))

                # Build symbol index entries
                for symbol, files in symbol_files.items():
                    if not files:
                        continue

                    dates = sorted([f[0] for f in files])
                    total_size = sum(f[1] for f in files)

                    self._index.exchanges[exchange_name].data_types[data_type_name].symbols[symbol] = SymbolIndex(
                        first_date=dates[0],
                        last_date=dates[-1],
                        file_count=len(files),
                        total_size_bytes=total_size,
                    )

        self._index.recalculate_totals()
        logger.info(
            f"Index built: {self._index.total_files} files, "
            f"{self._index.total_size_gb:.2f} GB across {self._index.exchange_count} exchanges"
        )

        return self._index

    def update_symbol(
        self,
        exchange: str,
        data_type: str,
        symbol: str,
        date: str,
        file_size: int,
    ) -> None:
        """
        Update index for a single downloaded file.

        Args:
            exchange: Exchange name
            data_type: Data type
            symbol: Symbol name
            date: Date string (YYYY-MM-DD)
            file_size: Size of the file in bytes
        """
        index = self.index

        # Ensure exchange exists
        if exchange not in index.exchanges:
            index.exchanges[exchange] = ExchangeIndex()

        # Ensure data type exists
        if data_type not in index.exchanges[exchange].data_types:
            index.exchanges[exchange].data_types[data_type] = DataTypeIndex()

        data_type_idx = index.exchanges[exchange].data_types[data_type]

        # Update or create symbol index
        if symbol in data_type_idx.symbols:
            sym_idx = data_type_idx.symbols[symbol]
            # Update date range
            if date < sym_idx.first_date:
                sym_idx.first_date = date
            if date > sym_idx.last_date:
                sym_idx.last_date = date
            sym_idx.file_count += 1
            sym_idx.total_size_bytes += file_size
        else:
            data_type_idx.symbols[symbol] = SymbolIndex(
                first_date=date,
                last_date=date,
                file_count=1,
                total_size_bytes=file_size,
            )

    def query(
        self,
        exchange: str | None = None,
        data_type: str | None = None,
        symbol: str | None = None,
    ) -> Generator[IndexQueryResult, None, None]:
        """
        Query the index with optional filters.

        Args:
            exchange: Filter by exchange (optional)
            data_type: Filter by data type (optional)
            symbol: Filter by symbol (optional)

        Yields:
            IndexQueryResult for each matching entry
        """
        index = self.index

        exchanges = [exchange] if exchange else list(index.exchanges.keys())

        for ex in exchanges:
            if ex not in index.exchanges:
                continue

            ex_idx = index.exchanges[ex]
            data_types = [data_type] if data_type else list(ex_idx.data_types.keys())

            for dt in data_types:
                if dt not in ex_idx.data_types:
                    continue

                dt_idx = ex_idx.data_types[dt]
                symbols = [symbol] if symbol else list(dt_idx.symbols.keys())

                for sym in symbols:
                    if sym not in dt_idx.symbols:
                        continue

                    sym_idx = dt_idx.symbols[sym]
                    yield IndexQueryResult(
                        exchange=ex,
                        data_type=dt,
                        symbol=sym,
                        first_date=sym_idx.first_date,
                        last_date=sym_idx.last_date,
                        file_count=sym_idx.file_count,
                        total_size_bytes=sym_idx.total_size_bytes,
                    )

    def get_status(self) -> dict:
        """Get a summary of the index status."""
        index = self.index

        return {
            "version": index.version,
            "root_dir": index.root_dir,
            "last_updated": index.last_updated,
            "total_files": index.total_files,
            "total_size_bytes": index.total_size_bytes,
            "total_size_gb": round(index.total_size_gb, 2),
            "total_size_tb": round(index.total_size_tb, 4),
            "exchange_count": index.exchange_count,
            "exchanges": {
                ex: {
                    "data_types": len(ex_idx.data_types),
                    "symbols": len(ex_idx.get_all_symbols()),
                    "files": ex_idx.file_count,
                    "size_gb": round(ex_idx.total_size_bytes / (1024**3), 2),
                }
                for ex, ex_idx in index.exchanges.items()
            },
        }

    def verify(self) -> dict:
        """
        Verify index against actual files on disk.

        Returns:
            Dict with verification results including missing/extra files
        """
        logger.info("Verifying index against disk...")

        results = {
            "verified": True,
            "index_files": self.index.total_files,
            "disk_files": 0,
            "missing_from_disk": [],
            "missing_from_index": [],
        }

        # Count actual files on disk
        disk_files = set()
        if self.root_dir.exists():
            for exchange_dir in self.root_dir.iterdir():
                if not exchange_dir.is_dir() or exchange_dir.name.startswith("."):
                    continue
                for data_type_dir in exchange_dir.iterdir():
                    if not data_type_dir.is_dir() or data_type_dir.name.startswith("."):
                        continue
                    for date_dir in data_type_dir.iterdir():
                        if not date_dir.is_dir() or date_dir.name.startswith("."):
                            continue
                        for file_path in date_dir.iterdir():
                            if file_path.is_file() and file_path.name.endswith(".csv.gz"):
                                rel_path = file_path.relative_to(self.root_dir)
                                disk_files.add(str(rel_path))

        results["disk_files"] = len(disk_files)

        # Build set of indexed files
        indexed_files = set()
        for exchange, ex_idx in self.index.exchanges.items():
            for data_type, dt_idx in ex_idx.data_types.items():
                for symbol, sym_idx in dt_idx.symbols.items():
                    # Note: We don't have individual file dates stored,
                    # so we can only verify counts, not individual files
                    pass

        # Compare counts
        if results["index_files"] != results["disk_files"]:
            results["verified"] = False
            results["difference"] = results["disk_files"] - results["index_files"]

        logger.info(
            f"Verification complete: index={results['index_files']}, "
            f"disk={results['disk_files']}, verified={results['verified']}"
        )

        return results

    def get_date_coverage(
        self, exchange: str, data_type: str, symbol: str
    ) -> dict | None:
        """
        Get detailed date coverage for a symbol.

        Note: This requires scanning the disk as the index only stores
        first/last dates, not individual dates.

        Returns:
            Dict with date coverage info or None if not found
        """
        sym_idx = self.index.get_symbol_info(exchange, data_type, symbol)
        if not sym_idx:
            return None

        # Scan actual files to get all dates
        symbol_dir = self.root_dir / exchange / data_type
        if not symbol_dir.exists():
            return None

        dates = []
        for date_dir in symbol_dir.iterdir():
            if not date_dir.is_dir():
                continue
            file_path = date_dir / f"{symbol}.csv.gz"
            if file_path.exists():
                dates.append(date_dir.name)

        dates.sort()

        # Find gaps
        gaps = []
        if len(dates) > 1:
            from datetime import datetime, timedelta
            for i in range(len(dates) - 1):
                d1 = datetime.strptime(dates[i], "%Y-%m-%d")
                d2 = datetime.strptime(dates[i + 1], "%Y-%m-%d")
                diff = (d2 - d1).days
                if diff > 1:
                    gaps.append({
                        "start": dates[i],
                        "end": dates[i + 1],
                        "missing_days": diff - 1,
                    })

        return {
            "exchange": exchange,
            "data_type": data_type,
            "symbol": symbol,
            "first_date": dates[0] if dates else None,
            "last_date": dates[-1] if dates else None,
            "total_dates": len(dates),
            "gaps": gaps,
            "has_gaps": len(gaps) > 0,
        }
