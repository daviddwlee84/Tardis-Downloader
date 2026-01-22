"""
Pydantic models for the metadata index.

Index Schema:
{
  "version": "1.0",
  "root_dir": "/mnt/raid/crypto",
  "last_updated": "2026-01-22T10:00:00Z",
  "total_files": 123456,
  "total_size_bytes": 6200000000000,
  "exchanges": {
    "binance-futures": {
      "trades": {
        "BTCUSDT": {
          "first_date": "2019-11-17",
          "last_date": "2026-01-22",
          "file_count": 2258,
          "total_size_bytes": 11290000000
        }
      }
    }
  }
}
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class IndexVersion(BaseModel):
    """Version information for the index format."""

    major: int = 1
    minor: int = 0

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}"

    @classmethod
    def from_string(cls, version_str: str) -> "IndexVersion":
        """Parse version from string like '1.0'."""
        parts = version_str.split(".")
        return cls(major=int(parts[0]), minor=int(parts[1]) if len(parts) > 1 else 0)


class SymbolIndex(BaseModel):
    """Index entry for a single symbol within a data type."""

    first_date: str = Field(..., description="First available date (YYYY-MM-DD)")
    last_date: str = Field(..., description="Last available date (YYYY-MM-DD)")
    file_count: int = Field(default=0, ge=0, description="Number of files")
    total_size_bytes: int = Field(default=0, ge=0, description="Total size in bytes")

    @property
    def total_size_mb(self) -> float:
        """Get size in MB."""
        return self.total_size_bytes / (1024 * 1024)

    @property
    def total_size_gb(self) -> float:
        """Get size in GB."""
        return self.total_size_bytes / (1024 * 1024 * 1024)


class DataTypeIndex(BaseModel):
    """Index entry for a data type within an exchange."""

    # symbol -> SymbolIndex
    symbols: dict[str, SymbolIndex] = Field(default_factory=dict)

    @property
    def file_count(self) -> int:
        """Total files across all symbols."""
        return sum(s.file_count for s in self.symbols.values())

    @property
    def total_size_bytes(self) -> int:
        """Total size across all symbols."""
        return sum(s.total_size_bytes for s in self.symbols.values())

    @property
    def symbol_count(self) -> int:
        """Number of symbols."""
        return len(self.symbols)


class ExchangeIndex(BaseModel):
    """Index entry for an exchange."""

    # data_type -> DataTypeIndex
    data_types: dict[str, DataTypeIndex] = Field(default_factory=dict)

    @property
    def file_count(self) -> int:
        """Total files across all data types."""
        return sum(dt.file_count for dt in self.data_types.values())

    @property
    def total_size_bytes(self) -> int:
        """Total size across all data types."""
        return sum(dt.total_size_bytes for dt in self.data_types.values())

    @property
    def data_type_count(self) -> int:
        """Number of data types."""
        return len(self.data_types)

    def get_all_symbols(self) -> set[str]:
        """Get all unique symbols across all data types."""
        symbols = set()
        for dt in self.data_types.values():
            symbols.update(dt.symbols.keys())
        return symbols


class MetadataIndex(BaseModel):
    """Root metadata index model."""

    version: str = Field(default="1.0", description="Index format version")
    root_dir: str = Field(..., description="Root directory of the data")
    last_updated: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="Last update timestamp (ISO 8601)",
    )
    total_files: int = Field(default=0, ge=0, description="Total number of files")
    total_size_bytes: int = Field(default=0, ge=0, description="Total size in bytes")

    # exchange -> ExchangeIndex
    exchanges: dict[str, ExchangeIndex] = Field(default_factory=dict)

    @property
    def total_size_gb(self) -> float:
        """Get total size in GB."""
        return self.total_size_bytes / (1024 * 1024 * 1024)

    @property
    def total_size_tb(self) -> float:
        """Get total size in TB."""
        return self.total_size_bytes / (1024 * 1024 * 1024 * 1024)

    @property
    def exchange_count(self) -> int:
        """Number of exchanges."""
        return len(self.exchanges)

    def recalculate_totals(self) -> None:
        """Recalculate total_files and total_size_bytes from exchange data."""
        self.total_files = sum(ex.file_count for ex in self.exchanges.values())
        self.total_size_bytes = sum(ex.total_size_bytes for ex in self.exchanges.values())

    def get_symbol_info(
        self, exchange: str, data_type: str, symbol: str
    ) -> SymbolIndex | None:
        """Get index info for a specific symbol."""
        try:
            return self.exchanges[exchange].data_types[data_type].symbols[symbol]
        except KeyError:
            return None

    def list_exchanges(self) -> list[str]:
        """List all indexed exchanges."""
        return list(self.exchanges.keys())

    def list_data_types(self, exchange: str) -> list[str]:
        """List all data types for an exchange."""
        if exchange not in self.exchanges:
            return []
        return list(self.exchanges[exchange].data_types.keys())

    def list_symbols(self, exchange: str, data_type: str) -> list[str]:
        """List all symbols for an exchange/data_type combination."""
        try:
            return list(self.exchanges[exchange].data_types[data_type].symbols.keys())
        except KeyError:
            return []


class IndexQueryResult(BaseModel):
    """Result from an index query."""

    exchange: str
    data_type: str
    symbol: str
    first_date: str
    last_date: str
    file_count: int
    total_size_bytes: int

    @property
    def total_size_mb(self) -> float:
        return self.total_size_bytes / (1024 * 1024)
