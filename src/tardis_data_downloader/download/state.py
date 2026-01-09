"""
State tracking for incremental downloads.

Tracks the last downloaded date for each exchange/symbol/data_type combination
to enable incremental updates.
"""

from __future__ import annotations

import json
from datetime import datetime, date
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from loguru import logger


class SymbolState(BaseModel):
    """State for a single symbol's data type."""

    last_date: str = Field(..., description="Last downloaded date (YYYY-MM-DD)")
    files_count: int = Field(default=0, description="Number of files downloaded")
    last_updated: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="Last update timestamp",
    )


class ExchangeState(BaseModel):
    """State for all symbols in an exchange."""

    # symbol -> data_type -> SymbolState
    symbols: dict[str, dict[str, SymbolState]] = Field(default_factory=dict)


class ProfileState(BaseModel):
    """State for a download profile."""

    # exchange -> ExchangeState
    exchanges: dict[str, ExchangeState] = Field(default_factory=dict)


class DownloadStateData(BaseModel):
    """Root state data model."""

    last_updated: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z"
    )
    profiles: dict[str, ProfileState] = Field(default_factory=dict)


class DownloadState:
    """
    Manages download state for incremental updates.

    State file structure:
    {
        "last_updated": "2024-01-15T10:30:00Z",
        "profiles": {
            "hft_core": {
                "exchanges": {
                    "binance-futures": {
                        "symbols": {
                            "BTCUSDT": {
                                "trades": {"last_date": "2024-01-14", "files_count": 14},
                                "quotes": {"last_date": "2024-01-14", "files_count": 14}
                            }
                        }
                    }
                }
            }
        }
    }
    """

    def __init__(self, state_file: str | Path = ".tardis_download_state.json"):
        """
        Initialize state manager.

        Args:
            state_file: Path to state file
        """
        self.state_file = Path(state_file)
        self._state: DownloadStateData | None = None

    def load(self) -> DownloadStateData:
        """Load state from file or create empty state."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._state = DownloadStateData.model_validate(data)
                logger.debug(f"Loaded state from {self.state_file}")
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Failed to load state file: {e}. Starting fresh.")
                self._state = DownloadStateData()
        else:
            logger.debug(f"No state file found at {self.state_file}. Starting fresh.")
            self._state = DownloadStateData()
        return self._state

    def save(self) -> None:
        """Save current state to file."""
        if self._state is None:
            return

        self._state.last_updated = datetime.utcnow().isoformat() + "Z"

        # Ensure parent directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self._state.model_dump(), f, indent=2)
        logger.debug(f"Saved state to {self.state_file}")

    @property
    def state(self) -> DownloadStateData:
        """Get current state (load if not loaded)."""
        if self._state is None:
            return self.load()
        return self._state

    def get_last_date(
        self,
        profile: str,
        exchange: str,
        symbol: str,
        data_type: str,
    ) -> str | None:
        """
        Get the last downloaded date for a specific combination.

        Returns:
            Last date string (YYYY-MM-DD) or None if not found
        """
        try:
            return (
                self.state.profiles[profile]
                .exchanges[exchange]
                .symbols[symbol][data_type]
                .last_date
            )
        except KeyError:
            return None

    def update(
        self,
        profile: str,
        exchange: str,
        symbol: str,
        data_type: str,
        last_date: str,
        files_count: int = 1,
    ) -> None:
        """
        Update state for a specific combination.

        Args:
            profile: Profile name
            exchange: Exchange name
            symbol: Symbol name
            data_type: Data type
            last_date: Last downloaded date
            files_count: Number of files downloaded (increments existing count)
        """
        state = self.state

        # Ensure profile exists
        if profile not in state.profiles:
            state.profiles[profile] = ProfileState()

        profile_state = state.profiles[profile]

        # Ensure exchange exists
        if exchange not in profile_state.exchanges:
            profile_state.exchanges[exchange] = ExchangeState()

        exchange_state = profile_state.exchanges[exchange]

        # Ensure symbol exists
        if symbol not in exchange_state.symbols:
            exchange_state.symbols[symbol] = {}

        symbol_data = exchange_state.symbols[symbol]

        # Get existing count or start at 0
        existing_count = 0
        if data_type in symbol_data:
            existing_count = symbol_data[data_type].files_count

        # Update or create state
        symbol_data[data_type] = SymbolState(
            last_date=last_date,
            files_count=existing_count + files_count,
            last_updated=datetime.utcnow().isoformat() + "Z",
        )

    def get_profile_summary(self, profile: str) -> dict[str, Any]:
        """
        Get a summary of download state for a profile.

        Returns:
            Dict with exchange -> symbol -> data_type -> last_date
        """
        if profile not in self.state.profiles:
            return {}

        profile_state = self.state.profiles[profile]
        summary = {}

        for exchange, exchange_state in profile_state.exchanges.items():
            summary[exchange] = {}
            for symbol, symbol_data in exchange_state.symbols.items():
                summary[exchange][symbol] = {
                    dt: state.last_date for dt, state in symbol_data.items()
                }

        return summary

    def get_total_files(self, profile: str | None = None) -> int:
        """Get total number of files downloaded."""
        total = 0
        profiles = (
            [self.state.profiles[profile]]
            if profile and profile in self.state.profiles
            else self.state.profiles.values()
        )

        for profile_state in profiles:
            for exchange_state in profile_state.exchanges.values():
                for symbol_data in exchange_state.symbols.values():
                    for state in symbol_data.values():
                        total += state.files_count

        return total

    def clear_profile(self, profile: str) -> None:
        """Clear state for a specific profile."""
        if profile in self.state.profiles:
            del self.state.profiles[profile]
            logger.info(f"Cleared state for profile: {profile}")

    def clear_all(self) -> None:
        """Clear all state."""
        self._state = DownloadStateData()
        logger.info("Cleared all download state")
