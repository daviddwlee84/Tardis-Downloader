"""
Configuration loader supporting YAML and TOML formats.

Features:
- Load from YAML or TOML files
- Environment variable substitution (${VAR_NAME})
- CLI argument merging
- Validation via Pydantic models
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from loguru import logger

from tardis_data_downloader.config.models import DownloadConfig


class ConfigLoader:
    """Load and validate configuration from YAML or TOML files."""

    ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")

    def __init__(self, config_path: str | Path | None = None):
        """
        Initialize the config loader.

        Args:
            config_path: Path to configuration file (YAML or TOML)
        """
        self.config_path = Path(config_path) if config_path else None
        self._config: DownloadConfig | None = None

    def load(self) -> DownloadConfig:
        """
        Load configuration from file.

        Returns:
            Validated DownloadConfig object
        """
        if self.config_path is None:
            logger.info("No config file specified, using defaults")
            return DownloadConfig()

        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        suffix = self.config_path.suffix.lower()
        raw_config = self._load_file(suffix)

        # Substitute environment variables
        raw_config = self._substitute_env_vars(raw_config)

        # Validate and create config object
        self._config = DownloadConfig.model_validate(raw_config)
        logger.info(f"Loaded config from {self.config_path}")
        return self._config

    def _load_file(self, suffix: str) -> dict[str, Any]:
        """Load raw config data from file based on extension."""
        if suffix in (".yaml", ".yml"):
            return self._load_yaml()
        elif suffix == ".toml":
            return self._load_toml()
        else:
            raise ValueError(f"Unsupported config format: {suffix}. Use .yaml, .yml, or .toml")

    def _load_yaml(self) -> dict[str, Any]:
        """Load YAML configuration file."""
        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML is required for YAML config files. Install with: pip install pyyaml")

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data or {}

    def _load_toml(self) -> dict[str, Any]:
        """Load TOML configuration file."""
        try:
            import tomllib
        except ImportError:
            # Python < 3.11 fallback
            try:
                import tomli as tomllib
            except ImportError:
                raise ImportError(
                    "tomli is required for TOML config files on Python < 3.11. "
                    "Install with: pip install tomli"
                )

        with open(self.config_path, "rb") as f:
            data = tomllib.load(f)
        return data

    def _substitute_env_vars(self, data: Any) -> Any:
        """Recursively substitute ${VAR_NAME} with environment variables."""
        if isinstance(data, dict):
            return {k: self._substitute_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._substitute_env_vars(item) for item in data]
        elif isinstance(data, str):
            return self._substitute_string(data)
        return data

    def _substitute_string(self, value: str) -> str:
        """Substitute environment variables in a string."""

        def replace_env_var(match: re.Match) -> str:
            var_name = match.group(1)
            env_value = os.environ.get(var_name)
            if env_value is None:
                logger.warning(f"Environment variable '{var_name}' not set, using empty string")
                return ""
            return env_value

        return self.ENV_VAR_PATTERN.sub(replace_env_var, value)

    @classmethod
    def merge_cli_args(
        cls,
        config: DownloadConfig,
        root_dir: str | None = None,
        concurrency: int | None = None,
        skip_existing: bool | None = None,
    ) -> DownloadConfig:
        """
        Merge CLI arguments into existing config (CLI takes precedence).

        Args:
            config: Base configuration
            root_dir: Override storage root directory
            concurrency: Override download concurrency
            skip_existing: Override skip existing files setting

        Returns:
            Updated DownloadConfig with CLI overrides applied
        """
        # Create a copy of the config data
        config_data = config.model_dump()

        if root_dir is not None:
            config_data["storage"]["root_dir"] = root_dir

        if concurrency is not None:
            config_data["download"]["concurrency"] = concurrency

        if skip_existing is not None:
            config_data["download"]["skip_existing"] = skip_existing

        return DownloadConfig.model_validate(config_data)

    @property
    def config(self) -> DownloadConfig:
        """Get loaded configuration (load if not already loaded)."""
        if self._config is None:
            return self.load()
        return self._config


def load_config(config_path: str | Path | None = None) -> DownloadConfig:
    """
    Convenience function to load configuration.

    Args:
        config_path: Path to configuration file

    Returns:
        Validated DownloadConfig
    """
    loader = ConfigLoader(config_path)
    return loader.load()
