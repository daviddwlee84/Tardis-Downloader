"""
Migration utilities for building SQLite database from existing data.

Supports:
- Building from filesystem scan
- Importing existing JSON state files
- Incremental updates (add only new files)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from loguru import logger

from tardis_data_downloader.db.connection import TardisDB

# Pattern: exchange/data_type/YYYY-MM-DD/symbol.csv.gz
DATE_DIR_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class TardisMigration:
    """Handles migration of existing data into the SQLite database."""

    def __init__(self, db: TardisDB):
        self.db = db

    def build_from_filesystem(self, root_dir: str | Path, show_progress: bool = True) -> int:
        """
        Scan filesystem and populate database with file records.

        Expected structure: root_dir/exchange/data_type/YYYY-MM-DD/symbol.csv.gz

        Args:
            root_dir: Root directory containing downloaded data.
            show_progress: Show progress bar if tqdm is available.

        Returns:
            Number of files indexed.
        """
        root = Path(root_dir)
        if not root.exists():
            logger.warning(f"Root directory does not exist: {root}")
            return 0

        # First pass: count files for progress bar
        logger.info(f"Scanning {root} for data files...")
        files = list(root.glob("*/*/*/*.csv.gz"))
        total = len(files)
        logger.info(f"Found {total:,} files to index")

        if total == 0:
            return 0

        progress = None
        if show_progress:
            try:
                from tqdm import tqdm
                progress = tqdm(total=total, desc="Building DB", unit="files")
            except ImportError:
                pass

        records = []
        batch_size = 5000
        indexed = 0

        for file_path in files:
            parsed = self._parse_file_path(file_path, root)
            if parsed:
                exchange, data_type, date_str, symbol, file_size = parsed
                records.append((exchange, data_type, symbol, date_str, file_size))

            if len(records) >= batch_size:
                self.db.file_repo.bulk_insert_files(records)
                indexed += len(records)
                records = []

            if progress:
                progress.update(1)

        # Insert remaining records
        if records:
            self.db.file_repo.bulk_insert_files(records)
            indexed += len(records)

        if progress:
            progress.close()

        self.db.set_metadata("last_build_root", str(root))
        logger.info(f"Indexed {indexed:,} files into database")
        return indexed

    def incremental_update(self, root_dir: str | Path, show_progress: bool = True) -> int:
        """
        Add only new files that aren't already in the database.

        Args:
            root_dir: Root directory containing downloaded data.
            show_progress: Show progress bar if tqdm is available.

        Returns:
            Number of new files added.
        """
        root = Path(root_dir)
        if not root.exists():
            return 0

        logger.info(f"Scanning {root} for new files...")
        files = list(root.glob("*/*/*/*.csv.gz"))

        progress = None
        if show_progress:
            try:
                from tqdm import tqdm
                progress = tqdm(total=len(files), desc="Checking files", unit="files")
            except ImportError:
                pass

        new_records = []
        batch_size = 5000
        added = 0

        for file_path in files:
            parsed = self._parse_file_path(file_path, root)
            if parsed:
                exchange, data_type, date_str, symbol, file_size = parsed
                if not self.db.file_repo.file_exists(exchange, data_type, symbol, date_str):
                    new_records.append((exchange, data_type, symbol, date_str, file_size))

            if len(new_records) >= batch_size:
                self.db.file_repo.bulk_insert_files(new_records)
                added += len(new_records)
                new_records = []

            if progress:
                progress.update(1)

        if new_records:
            self.db.file_repo.bulk_insert_files(new_records)
            added += len(new_records)

        if progress:
            progress.close()

        logger.info(f"Added {added:,} new files to database")
        return added

    def migrate_json_state(self, state_file: str | Path) -> int:
        """
        Import existing JSON state file into the database.

        Args:
            state_file: Path to .tardis_download_state.json

        Returns:
            Number of state records imported.
        """
        state_path = Path(state_file)
        if not state_path.exists():
            logger.warning(f"State file not found: {state_path}")
            return 0

        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        imported = 0
        profiles = data.get("profiles", {})

        for profile_name, profile_data in profiles.items():
            exchanges = profile_data.get("exchanges", {})
            for exchange_name, exchange_data in exchanges.items():
                symbols = exchange_data.get("symbols", {})
                for symbol_name, symbol_data in symbols.items():
                    for data_type, state_info in symbol_data.items():
                        last_date = state_info.get("last_date")
                        files_count = state_info.get("files_count", 0)
                        if last_date:
                            self.db.state_repo.update_state(
                                profile=profile_name,
                                exchange=exchange_name,
                                symbol=symbol_name,
                                data_type=data_type,
                                last_date=last_date,
                                files_count=files_count,
                            )
                            imported += 1

        logger.info(f"Imported {imported} state records from {state_path}")
        return imported

    def verify_against_filesystem(self, root_dir: str | Path) -> dict:
        """
        Compare database records against actual files on disk.

        Returns:
            Dict with verification results.
        """
        root = Path(root_dir)
        disk_files = set()

        for file_path in root.glob("*/*/*/*.csv.gz"):
            parsed = self._parse_file_path(file_path, root)
            if parsed:
                exchange, data_type, date_str, symbol, _ = parsed
                disk_files.add((exchange, data_type, symbol, date_str))

        # Get all DB records
        db_records = set()
        rows = self.db.execute(
            "SELECT exchange, data_type, symbol, date FROM files"
        ).fetchall()
        for row in rows:
            db_records.add((row["exchange"], row["data_type"], row["symbol"], row["date"]))

        in_db_not_disk = db_records - disk_files
        on_disk_not_db = disk_files - db_records

        return {
            "db_files": len(db_records),
            "disk_files": len(disk_files),
            "verified": len(in_db_not_disk) == 0 and len(on_disk_not_db) == 0,
            "in_db_not_disk": len(in_db_not_disk),
            "on_disk_not_db": len(on_disk_not_db),
            "missing_from_db_samples": sorted(on_disk_not_db)[:10],
            "missing_from_disk_samples": sorted(in_db_not_disk)[:10],
        }

    @staticmethod
    def _parse_file_path(
        file_path: Path, root: Path
    ) -> tuple[str, str, str, str, int] | None:
        """
        Parse a file path into its components.

        Expected: root/exchange/data_type/YYYY-MM-DD/symbol.csv.gz

        Returns:
            Tuple of (exchange, data_type, date, symbol, file_size) or None if invalid.
        """
        try:
            rel = file_path.relative_to(root)
            parts = rel.parts

            if len(parts) != 4:
                return None

            exchange, data_type, date_dir, filename = parts

            # Validate date directory
            if not DATE_DIR_PATTERN.match(date_dir):
                return None

            # Extract symbol from filename (remove .csv.gz)
            if filename.endswith(".csv.gz"):
                symbol = filename[:-7]  # Remove .csv.gz
            else:
                return None

            file_size = file_path.stat().st_size

            return (exchange, data_type, date_dir, symbol, file_size)
        except (ValueError, OSError):
            return None
