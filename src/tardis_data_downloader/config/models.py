"""
Pydantic models for Tardis Data Downloader configuration.

Supports both YAML and TOML configuration formats.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class StorageConfig(BaseModel):
    """Storage configuration for downloaded data."""

    root_dir: str = Field(default="./datasets", description="Root directory for data storage")
    format: Literal["csv"] = Field(default="csv", description="Data format (csv only for SSOT)")


class DateRangeConfig(BaseModel):
    """Date range configuration for downloads."""

    start: str = Field(..., description="Start date in YYYY-MM-DD format")
    end: str | None = Field(default=None, description="End date (null = today)")

    @field_validator("start", "end", mode="before")
    @classmethod
    def validate_date_format(cls, v: str | None) -> str | None:
        if v is None:
            return None
        # Validate date format
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError(f"Invalid date format: {v}. Expected YYYY-MM-DD")
        return v

    def get_end_date(self) -> str:
        """Get end date, defaulting to today if None."""
        if self.end is None:
            return date.today().isoformat()
        return self.end


class DownloadProfile(BaseModel):
    """Download profile defining what data to download."""

    description: str = Field(default="", description="Profile description")
    exchanges: list[str] = Field(..., description="List of exchanges to download from")
    data_types: list[str] = Field(..., description="List of data types to download")
    symbols: dict[str, list[str]] = Field(
        ..., description="Mapping of exchange to list of symbols"
    )
    date_range: DateRangeConfig = Field(..., description="Date range for download")

    @model_validator(mode="after")
    def validate_symbols_match_exchanges(self) -> "DownloadProfile":
        """Ensure all exchanges have symbols defined."""
        for exchange in self.exchanges:
            if exchange not in self.symbols:
                raise ValueError(
                    f"Exchange '{exchange}' listed in exchanges but has no symbols defined"
                )
        return self


class IncrementalConfig(BaseModel):
    """Configuration for incremental downloads."""

    enabled: bool = Field(default=True, description="Enable incremental downloads")
    state_file: str = Field(
        default=".tardis_download_state.json",
        description="Path to state tracking file",
    )
    auto_continue: bool = Field(
        default=True,
        description="Automatically continue from last downloaded date",
    )


class DownloadSettings(BaseModel):
    """Download behavior settings."""

    concurrency: int = Field(default=5, ge=1, le=20, description="Concurrent downloads")
    skip_existing: bool = Field(default=True, description="Skip already downloaded files")
    retry_attempts: int = Field(default=3, ge=1, description="Number of retry attempts")
    timeout_seconds: int = Field(default=300, ge=30, description="Download timeout in seconds")


class TardisMachineConfig(BaseModel):
    """Configuration for Tardis Machine compatibility."""

    enabled: bool = Field(default=False, description="Enable Tardis Machine symlinks")
    symlink_dir: str = Field(
        default="./tardis_cache",
        description="Directory for Tardis Machine format symlinks",
    )


class IndexConfig(BaseModel):
    """Configuration for metadata indexing."""

    enabled: bool = Field(default=True, description="Enable metadata indexing")
    index_file: str = Field(
        default=".tardis_index.json",
        description="Path to the metadata index file (legacy JSON)",
    )
    auto_update: bool = Field(
        default=True,
        description="Automatically update index after downloads",
    )
    db_file: str = Field(
        default=".tardis.db",
        description="Path to the SQLite database file",
    )
    existing_check: Literal["index", "filesystem", "override"] = Field(
        default="filesystem",
        description="Method for checking existing files: "
        "'index' uses SQLite DB, 'filesystem' uses Path.exists(), "
        "'override' redownloads all",
    )


class DownloadConfig(BaseModel):
    """Root configuration model for Tardis Data Downloader."""

    version: str = Field(default="1.0", description="Config file version")
    storage: StorageConfig = Field(default_factory=StorageConfig)
    profiles: dict[str, DownloadProfile] = Field(
        default_factory=dict, description="Named download profiles"
    )
    incremental: IncrementalConfig = Field(default_factory=IncrementalConfig)
    download: DownloadSettings = Field(default_factory=DownloadSettings)
    tardis_machine: TardisMachineConfig = Field(default_factory=TardisMachineConfig)
    index: IndexConfig = Field(default_factory=IndexConfig)

    def get_profile(self, name: str) -> DownloadProfile:
        """Get a download profile by name."""
        if name not in self.profiles:
            available = ", ".join(self.profiles.keys()) if self.profiles else "none"
            raise ValueError(f"Profile '{name}' not found. Available profiles: {available}")
        return self.profiles[name]

    def list_profiles(self) -> list[str]:
        """List all available profile names."""
        return list(self.profiles.keys())
