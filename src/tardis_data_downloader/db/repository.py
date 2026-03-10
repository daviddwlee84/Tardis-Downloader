"""
Repository classes for accessing SQLite data.

Provides FileRepository for file tracking and StateRepository for download state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tardis_data_downloader.db.connection import TardisDB


class FileRepository:
    """Repository for managing file records in the database."""

    def __init__(self, db: "TardisDB"):
        self.db = db

    def file_exists(self, exchange: str, data_type: str, symbol: str, date: str) -> bool:
        """Check if a specific file record exists."""
        row = self.db.execute(
            "SELECT 1 FROM files WHERE exchange=? AND data_type=? AND symbol=? AND date=?",
            (exchange, data_type, symbol, date),
        ).fetchone()
        return row is not None

    def batch_file_exists(
        self, exchange: str, data_type: str, symbol: str, dates: list[str]
    ) -> set[str]:
        """
        Check which dates already exist for a given exchange/data_type/symbol.

        Returns:
            Set of date strings that already exist in the database.
        """
        if not dates:
            return set()

        # Use batched queries to avoid SQLite variable limit (999)
        existing = set()
        batch_size = 900
        for i in range(0, len(dates), batch_size):
            batch = dates[i : i + batch_size]
            placeholders = ",".join("?" * len(batch))
            rows = self.db.execute(
                f"SELECT date FROM files "
                f"WHERE exchange=? AND data_type=? AND symbol=? "
                f"AND date IN ({placeholders})",
                (exchange, data_type, symbol, *batch),
            ).fetchall()
            existing.update(row["date"] for row in rows)

        return existing

    def insert_file(
        self,
        exchange: str,
        data_type: str,
        symbol: str,
        date: str,
        file_size: int = 0,
    ) -> None:
        """Insert or update a file record."""
        self.db.execute(
            "INSERT OR REPLACE INTO files (exchange, data_type, symbol, date, file_size, created_at) "
            "VALUES (?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))",
            (exchange, data_type, symbol, date, file_size),
        )
        self.db.commit()

    def bulk_insert_files(self, records: list[tuple]) -> int:
        """
        Bulk insert file records.

        Args:
            records: List of (exchange, data_type, symbol, date, file_size) tuples.

        Returns:
            Number of records inserted.
        """
        if not records:
            return 0

        self.db.begin()
        try:
            self.db.executemany(
                "INSERT OR IGNORE INTO files (exchange, data_type, symbol, date, file_size, created_at) "
                "VALUES (?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))",
                records,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return len(records)

    def get_symbol_stats(self, exchange: str, data_type: str, symbol: str) -> dict:
        """Get statistics for a specific symbol."""
        row = self.db.execute(
            "SELECT COUNT(*) as count, "
            "COALESCE(SUM(file_size), 0) as total_size, "
            "MIN(date) as first_date, "
            "MAX(date) as last_date "
            "FROM files WHERE exchange=? AND data_type=? AND symbol=?",
            (exchange, data_type, symbol),
        ).fetchone()

        return {
            "count": row["count"],
            "total_size": row["total_size"],
            "first_date": row["first_date"],
            "last_date": row["last_date"],
        }

    def get_date_range(
        self, exchange: str, data_type: str, symbol: str
    ) -> tuple[str, str] | None:
        """Get the first and last date for a symbol."""
        row = self.db.execute(
            "SELECT MIN(date) as first_date, MAX(date) as last_date "
            "FROM files WHERE exchange=? AND data_type=? AND symbol=?",
            (exchange, data_type, symbol),
        ).fetchone()

        if row and row["first_date"]:
            return (row["first_date"], row["last_date"])
        return None

    def get_all_dates(self, exchange: str, data_type: str, symbol: str) -> list[str]:
        """Get all recorded dates for a symbol, sorted."""
        rows = self.db.execute(
            "SELECT date FROM files "
            "WHERE exchange=? AND data_type=? AND symbol=? "
            "ORDER BY date",
            (exchange, data_type, symbol),
        ).fetchall()
        return [row["date"] for row in rows]

    def get_coverage_gaps(
        self, exchange: str, data_type: str, symbol: str
    ) -> list[dict]:
        """
        Find date coverage gaps for a symbol.

        Returns:
            List of gap dicts with 'start', 'end', and 'days' keys.
        """
        from datetime import date as date_cls, timedelta

        dates = self.get_all_dates(exchange, data_type, symbol)
        if not dates:
            return []

        gaps = []
        for i in range(1, len(dates)):
            prev = date_cls.fromisoformat(dates[i - 1])
            curr = date_cls.fromisoformat(dates[i])
            diff = (curr - prev).days
            if diff > 1:
                gap_start = (prev + timedelta(days=1)).isoformat()
                gap_end = (curr - timedelta(days=1)).isoformat()
                gaps.append(
                    {"start": gap_start, "end": gap_end, "days": diff - 1}
                )

        return gaps

    def query(
        self,
        exchange: str | None = None,
        data_type: str | None = None,
        symbol: str | None = None,
    ) -> list[dict]:
        """
        Query file records with optional filters.

        Returns aggregated stats grouped by exchange/data_type/symbol.
        """
        conditions = []
        params = []
        if exchange:
            conditions.append("exchange=?")
            params.append(exchange)
        if data_type:
            conditions.append("data_type=?")
            params.append(data_type)
        if symbol:
            conditions.append("symbol=?")
            params.append(symbol)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        rows = self.db.execute(
            f"SELECT exchange, data_type, symbol, "
            f"COUNT(*) as file_count, "
            f"COALESCE(SUM(file_size), 0) as total_size, "
            f"MIN(date) as first_date, "
            f"MAX(date) as last_date "
            f"FROM files {where} "
            f"GROUP BY exchange, data_type, symbol "
            f"ORDER BY exchange, data_type, symbol",
            tuple(params),
        ).fetchall()

        return [dict(row) for row in rows]

    def get_total_stats(self) -> dict:
        """Get total database statistics."""
        row = self.db.execute(
            "SELECT COUNT(*) as total_files, "
            "COALESCE(SUM(file_size), 0) as total_size, "
            "COUNT(DISTINCT exchange) as exchanges, "
            "COUNT(DISTINCT data_type) as data_types, "
            "COUNT(DISTINCT symbol) as symbols "
            "FROM files"
        ).fetchone()

        return dict(row)

    def get_file_count(self) -> int:
        """Get total number of file records."""
        row = self.db.execute("SELECT COUNT(*) as count FROM files").fetchone()
        return row["count"]


class StateRepository:
    """Repository for managing download state in the database."""

    def __init__(self, db: "TardisDB"):
        self.db = db

    def get_last_date(
        self, profile: str, exchange: str, symbol: str, data_type: str
    ) -> str | None:
        """Get the last downloaded date for a specific combination."""
        row = self.db.execute(
            "SELECT last_date FROM download_state "
            "WHERE profile=? AND exchange=? AND symbol=? AND data_type=?",
            (profile, exchange, symbol, data_type),
        ).fetchone()
        return row["last_date"] if row else None

    def update_state(
        self,
        profile: str,
        exchange: str,
        symbol: str,
        data_type: str,
        last_date: str,
        files_count: int = 0,
    ) -> None:
        """Update or insert download state for a specific combination."""
        self.db.execute(
            "INSERT OR REPLACE INTO download_state "
            "(profile, exchange, symbol, data_type, last_date, files_count, last_updated) "
            "VALUES (?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))",
            (profile, exchange, symbol, data_type, last_date, files_count),
        )
        self.db.commit()

    def get_profile_summary(self, profile: str) -> dict:
        """
        Get summary of download state for a profile.

        Returns:
            Dict with exchange -> symbol -> data_type -> last_date
        """
        rows = self.db.execute(
            "SELECT exchange, symbol, data_type, last_date, files_count "
            "FROM download_state WHERE profile=? "
            "ORDER BY exchange, symbol, data_type",
            (profile,),
        ).fetchall()

        summary: dict = {}
        for row in rows:
            exchange = row["exchange"]
            symbol = row["symbol"]
            data_type = row["data_type"]

            if exchange not in summary:
                summary[exchange] = {}
            if symbol not in summary[exchange]:
                summary[exchange][symbol] = {}
            summary[exchange][symbol][data_type] = {
                "last_date": row["last_date"],
                "files_count": row["files_count"],
            }

        return summary

    def get_total_files(self, profile: str | None = None) -> int:
        """Get total files count from state records."""
        if profile:
            row = self.db.execute(
                "SELECT COALESCE(SUM(files_count), 0) as total "
                "FROM download_state WHERE profile=?",
                (profile,),
            ).fetchone()
        else:
            row = self.db.execute(
                "SELECT COALESCE(SUM(files_count), 0) as total FROM download_state"
            ).fetchone()
        return row["total"]

    def get_all_profiles(self) -> list[str]:
        """Get all profile names."""
        rows = self.db.execute(
            "SELECT DISTINCT profile FROM download_state ORDER BY profile"
        ).fetchall()
        return [row["profile"] for row in rows]
