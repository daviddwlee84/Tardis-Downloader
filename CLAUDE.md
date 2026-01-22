# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tardis Data Downloader is a Python CLI tool and library for downloading cryptocurrency market data from Tardis.dev. It supports both direct downloads and config-file based batch downloads with incremental sync capabilities.

## Development Commands

```bash
# Install dependencies (requires uv package manager)
uv sync --all-groups

# Run CLI
td-fire --help
td-fire list-exchanges
td-fire download 'deribit' 'trades' 'BTC-PERPETUAL' '2023-01-01' '2023-01-02'
td-fire config-download --config configs/download.yaml --profile hft_core

# Run Streamlit UI
td-ui

# Run marimo notebooks
marimo edit notebooks/api_status.py
marimo edit notebooks/data_explorer.py

# Format code
black src/
```

## Architecture

### Source Structure (`src/tardis_data_downloader/`)

- **cli/** - Python Fire-based CLI with two entry points:
  - `fire_download_wrapper.py` → `td-fire` command (main CLI)
  - `tardis_data_downloader.py` → legacy entry point

- **config/** - YAML/TOML configuration with Pydantic validation:
  - `loader.py` - Config loading with `${ENV_VAR}` substitution
  - `models.py` - Pydantic models for config validation
  - Supports profiles for different download scenarios

- **download/** - Download orchestration:
  - `orchestrator.py` - Batch and incremental download coordination
  - `state.py` - State tracking via `.tardis_download_state.json`

- **data/** - Data models and management:
  - `models.py` - Pydantic models (SymbolInfo, exchange enums)
  - `data_manager.py` - TardisDataManager for file operations

- **ui/** - Streamlit multi-page application:
  - `Overview.py` - Main dashboard
  - `pages/` - Feature-specific pages
  - `shared_components.py` - Reusable UI components

- **utils/** - Utility functions (date parsing, validation)

### Key Patterns

- **Configuration**: YAML/TOML files with environment variable substitution (`${API_KEY}`)
- **CLI Design**: Python Fire auto-generates CLI from class methods
- **Data Format**: Downloads to CSV.GZ format by default
- **Incremental Downloads**: State tracked in `.tardis_download_state.json`

### Marimo Notebooks

Located in `notebooks/`. When editing marimo notebooks:
- Only edit code inside `@app.cell` decorators
- Cells execute reactively based on dependency graph
- Use polars for data manipulation, altair for visualization
- Access UI element values with `.value` in a separate cell
- Run `marimo check --fix` after editing
