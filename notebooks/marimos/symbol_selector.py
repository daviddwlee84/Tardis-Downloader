# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx",
#     "marimo",
#     "polars",
#     "altair",
#     "pyyaml",
# ]
# ///

import marimo

__generated_with = "0.19.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import polars as pl
    import altair as alt
    import yaml
    from datetime import datetime, timedelta
    from pathlib import Path
    return datetime, mo, timedelta, yaml


@app.cell
def _(mo):
    mo.md("""
    # ML/HFT Symbol Selector & Config Generator

    Select optimal symbols for machine learning training and high-frequency trading,
    then generate a download configuration file.

    ---
    """)
    return


@app.cell
def _(datetime, mo, timedelta, yaml):
    cli_args = mo.cli_args()
    is_script_mode = mo.app_meta().mode == "script"

    # CLI mode: generate default config and print
    if is_script_mode:
        _preset = cli_args.get("preset", "core")
        _start = cli_args.get("start", str((datetime.now() - timedelta(days=30)).date()))
        _end = cli_args.get("end", str((datetime.now() - timedelta(days=1)).date()))

        _presets = {
            "core": {
                "description": "Core BTC/ETH perpetuals from top exchanges",
                "exchanges": ["binance-futures", "bybit", "deribit"],
                "data_types": ["trades", "quotes", "derivative_ticker"],
                "symbols": {
                    "binance-futures": ["BTCUSDT", "ETHUSDT"],
                    "bybit": ["BTCUSDT", "ETHUSDT"],
                    "deribit": ["BTC-PERPETUAL", "ETH-PERPETUAL"],
                }
            },
            "ml": {
                "description": "ML training data with full orderbook",
                "exchanges": ["binance-futures", "bybit", "deribit"],
                "data_types": ["trades", "quotes", "incremental_book_L2", "derivative_ticker"],
                "symbols": {
                    "binance-futures": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT"],
                    "bybit": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
                    "deribit": ["BTC-PERPETUAL", "ETH-PERPETUAL"],
                }
            },
            "hft": {
                "description": "HFT research - trades and quotes only",
                "exchanges": ["binance-futures", "bybit"],
                "data_types": ["trades", "quotes"],
                "symbols": {
                    "binance-futures": ["BTCUSDT", "ETHUSDT"],
                    "bybit": ["BTCUSDT", "ETHUSDT"],
                }
            },
        }

        if "list-presets" in cli_args:
            print("\n=== Available Presets ===\n")
            for _name, _info in _presets.items():
                print(f"  {_name:12s} - {_info['description']}")
            print("\nUsage: python symbol_selector.py -- --preset ml --start 2024-01-01 --end 2024-12-31\n")
        elif "generate" in cli_args or _preset:
            _selected = _presets.get(_preset, _presets["core"])
            _config = {
                "version": "1.0",
                "storage": {"root_dir": "./datasets", "format": "csv"},
                "profiles": {
                    f"{_preset}_profile": {
                        "description": _selected["description"],
                        "exchanges": _selected["exchanges"],
                        "data_types": _selected["data_types"],
                        "symbols": _selected["symbols"],
                        "date_range": {"start": _start, "end": _end}
                    }
                },
                "incremental": {"enabled": True, "state_file": ".tardis_download_state.json", "auto_continue": True},
                "download": {"concurrency": 5, "skip_existing": True, "retry_attempts": 3, "timeout_seconds": 300}
            }
            print(f"\n=== Generated Config (preset: {_preset}) ===\n")
            print(yaml.dump(_config, default_flow_style=False, sort_keys=False))
            print("# Save to: configs/download.yaml")
            print(f"# Run: td-fire config-download --config configs/download.yaml --profile {_preset}_profile\n")

    return cli_args, is_script_mode


@app.cell
def _(mo):
    mo.md("""
    ## Recommended Symbols for ML/HFT

    Based on liquidity, data availability, and trading volume, here are the recommended symbols:

    ### Tier 1: Core Assets (Must Have)
    - **BTC** - Highest liquidity, longest history
    - **ETH** - Second highest liquidity

    ### Tier 2: Major Alts (High Volume)
    - **SOL** - High volatility, good for momentum strategies
    - **XRP** - High volume, good spread
    - **DOGE** - Retail-driven, unique dynamics
    - **BNB** - Exchange token, correlated with Binance volume

    ### Tier 3: DeFi/Infrastructure
    - **AVAX**, **LINK**, **MATIC** - Solid liquidity

    ### Recommended Exchanges
    1. **binance-futures** - Highest volume, most symbols, longest history
    2. **bybit** - Second largest, good API
    3. **deribit** - Best for BTC/ETH, institutional grade
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Configure Your Download
    """)
    return


@app.cell
def _(mo):
    profile_name = mo.ui.text(
        value="ml_hft_training",
        label="Profile Name"
    )

    profile_description = mo.ui.text(
        value="ML training and HFT research data",
        label="Description"
    )

    mo.hstack([profile_name, profile_description])
    return profile_description, profile_name


@app.cell
def _(mo):
    mo.md("""
    ### Select Exchanges
    """)
    return


@app.cell
def _(mo):
    AVAILABLE_EXCHANGES = {
        "binance-futures": {"name": "Binance USDT-M", "since": "2019-11-17", "tier": 1},
        "bybit": {"name": "Bybit Derivatives", "since": "2019-11-07", "tier": 1},
        "deribit": {"name": "Deribit", "since": "2019-03-30", "tier": 1},
        "okex-swap": {"name": "OKX Swap", "since": "2019-03-30", "tier": 2},
        "huobi-dm-linear-swap": {"name": "Huobi USDT Swap", "since": "2020-10-30", "tier": 2},
        "gate-io-futures": {"name": "Gate.io Futures", "since": "2020-07-01", "tier": 2},
        "hyperliquid": {"name": "Hyperliquid", "since": "2024-10-29", "tier": 2},
        "bitget-futures": {"name": "Bitget Futures", "since": "2024-11-08", "tier": 3},
    }

    exchange_checkboxes = {
        ex_id: mo.ui.checkbox(
            label=f"{info['name']} (since {info['since']})",
            value=info["tier"] == 1
        )
        for ex_id, info in AVAILABLE_EXCHANGES.items()
    }

    mo.vstack([
        mo.md("**Tier 1 (Recommended)**"),
        mo.hstack([exchange_checkboxes["binance-futures"], exchange_checkboxes["bybit"], exchange_checkboxes["deribit"]]),
        mo.md("**Tier 2**"),
        mo.hstack([exchange_checkboxes["okex-swap"], exchange_checkboxes["huobi-dm-linear-swap"], exchange_checkboxes["gate-io-futures"]]),
        mo.md("**Tier 3 (Newer)**"),
        mo.hstack([exchange_checkboxes["hyperliquid"], exchange_checkboxes["bitget-futures"]]),
    ])
    return (exchange_checkboxes,)


@app.cell
def _(exchange_checkboxes):
    selected_exchanges = [ex_id for ex_id, cb in exchange_checkboxes.items() if cb.value]
    return (selected_exchanges,)


@app.cell
def _(mo):
    mo.md("""
    ### Select Data Types
    """)
    return


@app.cell
def _(mo):
    DATA_TYPES = {
        "trades": {"desc": "Trade executions (essential)", "size": "Small", "ml": True, "hft": True},
        "quotes": {"desc": "Best bid/ask (essential)", "size": "Small", "ml": True, "hft": True},
        "incremental_book_L2": {"desc": "Full L2 orderbook", "size": "Large", "ml": True, "hft": True},
        "book_snapshot_25": {"desc": "Top 25 levels snapshot", "size": "Medium", "ml": True, "hft": False},
        "derivative_ticker": {"desc": "Funding, mark price, OI", "size": "Small", "ml": True, "hft": True},
        "liquidations": {"desc": "Forced liquidations", "size": "Small", "ml": True, "hft": False},
    }

    use_case = mo.ui.radio(
        options=["ML Training (Full Data)", "HFT Research (Essential Only)", "Custom"],
        value="ML Training (Full Data)",
        label="Use Case"
    )
    use_case
    return DATA_TYPES, use_case


@app.cell
def _(DATA_TYPES, mo, use_case):
    if use_case.value == "ML Training (Full Data)":
        default_types = [dt for dt, info in DATA_TYPES.items() if info["ml"]]
    elif use_case.value == "HFT Research (Essential Only)":
        default_types = [dt for dt, info in DATA_TYPES.items() if info["hft"]]
    else:
        default_types = ["trades", "quotes"]

    data_type_checkboxes = {
        dt: mo.ui.checkbox(
            label=f"{dt} - {info['desc']} [{info['size']}]",
            value=dt in default_types
        )
        for dt, info in DATA_TYPES.items()
    }

    mo.vstack(list(data_type_checkboxes.values()))
    return (data_type_checkboxes,)


@app.cell
def _(data_type_checkboxes):
    selected_data_types = [dt for dt, cb in data_type_checkboxes.items() if cb.value]
    return (selected_data_types,)


@app.cell
def _(mo):
    mo.md("""
    ### Select Symbols
    """)
    return


@app.cell
def _(mo):
    SYMBOL_PRESETS = {
        "Core BTC/ETH Only": {
            "binance-futures": ["BTCUSDT", "ETHUSDT"],
            "bybit": ["BTCUSDT", "ETHUSDT"],
            "deribit": ["BTC-PERPETUAL", "ETH-PERPETUAL"],
        },
        "Top 5 Assets": {
            "binance-futures": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT"],
            "bybit": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"],
            "deribit": ["BTC-PERPETUAL", "ETH-PERPETUAL"],
        },
        "Top 10 Assets": {
            "binance-futures": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT", 
                               "DOGEUSDT", "AVAXUSDT", "LINKUSDT", "MATICUSDT", "ADAUSDT"],
            "bybit": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", 
                     "AVAXUSDT", "LINKUSDT", "MATICUSDT"],
            "deribit": ["BTC-PERPETUAL", "ETH-PERPETUAL"],
        },
        "BTC Only (Multi-Exchange)": {
            "binance-futures": ["BTCUSDT"],
            "bybit": ["BTCUSDT"],
            "deribit": ["BTC-PERPETUAL"],
            "okex-swap": ["BTC-USDT-SWAP"],
            "huobi-dm-linear-swap": ["BTC-USDT"],
        },
    }

    symbol_preset = mo.ui.dropdown(
        options=list(SYMBOL_PRESETS.keys()),
        value="Core BTC/ETH Only",
        label="Symbol Preset"
    )
    symbol_preset
    return SYMBOL_PRESETS, symbol_preset


@app.cell
def _(SYMBOL_PRESETS, selected_exchanges, symbol_preset):
    preset_symbols = SYMBOL_PRESETS.get(symbol_preset.value, {})

    symbols_config = {}
    for ex in selected_exchanges:
        if ex in preset_symbols:
            symbols_config[ex] = preset_symbols[ex]
        elif ex == "okex-swap":
            symbols_config[ex] = ["BTC-USDT-SWAP", "ETH-USDT-SWAP"]
        elif ex == "huobi-dm-linear-swap":
            symbols_config[ex] = ["BTC-USDT", "ETH-USDT"]
        elif ex == "gate-io-futures":
            symbols_config[ex] = ["BTC_USDT", "ETH_USDT"]
        elif ex == "hyperliquid":
            symbols_config[ex] = ["BTC", "ETH"]
        elif ex == "bitget-futures":
            symbols_config[ex] = ["BTCUSDT", "ETHUSDT"]
        else:
            symbols_config[ex] = ["BTCUSDT", "ETHUSDT"]
    return (symbols_config,)


@app.cell
def _(mo, symbols_config):
    mo.md(f"""
    **Selected Symbols:**

    {chr(10).join(f"- **{ex}**: {', '.join(syms)}" for ex, syms in symbols_config.items())}
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ### Date Range
    """)
    return


@app.cell
def _(datetime, mo, timedelta):
    today = datetime.now().date()
    default_start = today - timedelta(days=365)
    default_end = today - timedelta(days=1)

    start_date = mo.ui.date(
        value=default_start,
        label="Start Date"
    )

    end_date = mo.ui.date(
        value=default_end,
        label="End Date"
    )

    mo.hstack([start_date, end_date])
    return end_date, start_date


@app.cell
def _(end_date, mo, start_date):
    days_count = (end_date.value - start_date.value).days + 1
    mo.md(f"📅 **{days_count} days** of data selected")
    return (days_count,)


@app.cell
def _(mo):
    mo.md("""
    ### Download Settings
    """)
    return


@app.cell
def _(mo):
    concurrency = mo.ui.slider(
        start=1,
        stop=20,
        value=5,
        label="Concurrency (parallel downloads)"
    )

    skip_existing = mo.ui.checkbox(
        label="Skip existing files",
        value=True
    )

    mo.hstack([concurrency, skip_existing])
    return concurrency, skip_existing


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Generated Configuration
    """)
    return


@app.cell
def _(
    concurrency,
    end_date,
    profile_description,
    profile_name,
    selected_data_types,
    selected_exchanges,
    skip_existing,
    start_date,
    symbols_config,
    yaml,
):
    config = {
        "version": "1.0",
        "storage": {
            "root_dir": "./datasets",
            "format": "csv"
        },
        "profiles": {
            profile_name.value: {
                "description": profile_description.value,
                "exchanges": selected_exchanges,
                "data_types": selected_data_types,
                "symbols": symbols_config,
                "date_range": {
                    "start": str(start_date.value),
                    "end": str(end_date.value)
                }
            }
        },
        "incremental": {
            "enabled": True,
            "state_file": ".tardis_download_state.json",
            "auto_continue": True
        },
        "download": {
            "concurrency": concurrency.value,
            "skip_existing": skip_existing.value,
            "retry_attempts": 3,
            "timeout_seconds": 300
        }
    }

    config_yaml = yaml.dump(config, default_flow_style=False, sort_keys=False, allow_unicode=True)
    return (config_yaml,)


@app.cell
def _(config_yaml, mo):
    mo.md(f"""
    ```yaml
    {config_yaml}
    ```
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Download Commands
    """)
    return


@app.cell
def _(mo, profile_name):
    config_file_name = f"configs/{profile_name.value}.yaml"

    commands = f"""
    ## Save Configuration

    First, save the YAML above to `{config_file_name}`, then run:

    ```bash
    # 1. Preview what will be downloaded (dry run)
    td-fire config-download --config {config_file_name} --profile {profile_name.value} --dry-run

    # 2. Estimate storage requirements
    td-fire estimate --config {config_file_name} --profile {profile_name.value}

    # 3. Start the download
    td-fire config-download --config {config_file_name} --profile {profile_name.value}

    # 4. For incremental updates (run daily/weekly)
    td-fire incremental --config {config_file_name} --profile {profile_name.value}

    # 5. Check download status
    td-fire status --config {config_file_name} --profile {profile_name.value}
    ```

    ## Quick Download (Without Config File)

    ```bash
    # Download directly using td-fire
    td-fire download 'binance-futures' 'trades,quotes' 'BTCUSDT,ETHUSDT' '2024-01-01' '2024-12-31'
    ```
    """
    mo.md(commands)
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Storage Estimation
    """)
    return


@app.cell
def _(days_count, mo, selected_data_types, symbols_config):
    SIZE_ESTIMATES_MB_PER_DAY = {
        "trades": 5,
        "quotes": 3,
        "incremental_book_L2": 500,
        "book_snapshot_25": 50,
        "book_snapshot_5": 10,
        "derivative_ticker": 2,
        "liquidations": 0.5,
    }

    total_symbols = sum(len(syms) for syms in symbols_config.values())

    total_mb = 0
    breakdown = []
    for dt in selected_data_types:
        size_per_day = SIZE_ESTIMATES_MB_PER_DAY.get(dt, 5)
        dt_total = size_per_day * days_count * total_symbols
        total_mb += dt_total
        breakdown.append(f"- **{dt}**: ~{dt_total:,.0f} MB ({size_per_day} MB/day × {days_count} days × {total_symbols} symbols)")

    total_gb = total_mb / 1024

    mo.md(f"""
    ### Estimated Storage Requirements

    **Total: ~{total_gb:,.1f} GB** (compressed CSV)

    #### Breakdown by Data Type:

    {chr(10).join(breakdown)}

    ⚠️ *These are rough estimates. Actual sizes vary by exchange and market activity.*

    💡 **Tip:** Start with `trades` and `quotes` only to minimize storage. Add `incremental_book_L2` only if you need full orderbook data.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ---

    ## CLI Usage

    ```bash
    # Interactive mode (opens browser UI)
    marimo run notebooks/marimos/symbol_selector.py

    # CLI mode - list available presets
    python notebooks/marimos/symbol_selector.py -- --list-presets

    # CLI mode - generate config with preset
    python notebooks/marimos/symbol_selector.py -- --preset core
    python notebooks/marimos/symbol_selector.py -- --preset ml --start 2024-01-01 --end 2024-12-31
    python notebooks/marimos/symbol_selector.py -- --preset hft

    # Using uv
    uv run python notebooks/marimos/symbol_selector.py -- --preset ml
    ```
    """)
    return


if __name__ == "__main__":
    app.run()
