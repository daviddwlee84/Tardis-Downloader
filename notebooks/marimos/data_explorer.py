# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx",
#     "marimo",
#     "polars",
#     "altair",
#     "tardis-dev",
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
    import httpx
    import json
    import os
    from pathlib import Path
    from datetime import datetime
    return Path, httpx, json, mo, pl


@app.cell
def _(mo):
    mo.md("""
    # Tardis Data Explorer

    Explore available exchanges, data types, and symbols from Tardis.dev.

    ---
    """)
    return


@app.cell
def _(mo):
    cli_args = mo.cli_args()
    is_script_mode = mo.app_meta().mode == "script"
    return cli_args, is_script_mode


@app.cell
def _(Path, json, mo):
    exchanges_file = Path("files/exchanges_2025-09-17.json")
    if not exchanges_file.exists():
        exchanges_file = Path("../../files/exchanges_2025-09-17.json")

    if exchanges_file.exists():
        with open(exchanges_file) as f:
            exchanges_data = json.load(f)
        mo.output.replace(
            mo.md(f"✅ Loaded {len(exchanges_data)} exchanges from local cache")
        )
    else:
        exchanges_data = []
        mo.output.replace(
            mo.md("⚠️ Local exchanges file not found. Use the fetch button below.")
        )
    return (exchanges_data,)


@app.cell
def _(cli_args, exchanges_data, httpx, is_script_mode, mo, pl):
    mo.stop(not exchanges_data, mo.md("No exchange data available"))

    # Handle CLI --list-exchanges
    if is_script_mode and "list-exchanges" in cli_args:
        print("\n=== Available Exchanges ===\n")
        for ex in exchanges_data:
            if not ex.get("delisted", False):
                print(f"  {ex['id']:30s} {ex['name']}")
        print()

    # Handle CLI --exchange with --fetch
    if is_script_mode and cli_args.get("exchange") and "fetch" in cli_args:
        _exchange_id = cli_args.get("exchange")
        print(f"\n=== Fetching symbols for {_exchange_id} ===\n")
        try:
            _response = httpx.get(
                f"https://api.tardis.dev/v1/exchanges/{_exchange_id}", timeout=30.0
            )
            _response.raise_for_status()
            _details = _response.json()
            _symbols = _details.get("availableSymbols", [])
            _data_types = _details.get("availableDataTypes", [])

            print(f"Exchange: {_details.get('name', _exchange_id)}")
            print(f"Available Since: {_details.get('availableSince', 'N/A')[:10]}")
            print(f"Data Types: {', '.join(_data_types)}")
            print(f"\nTotal Symbols: {len(_symbols)}")

            # Group by type
            _type_counts = {}
            for _s in _symbols:
                if isinstance(_s, dict):
                    _t = _s.get("type", "unknown")
                    _type_counts[_t] = _type_counts.get(_t, 0) + 1
            print("\nSymbols by Type:")
            for _t, _count in sorted(_type_counts.items()):
                print(f"  {_t}: {_count}")

            # Show perpetuals
            _perpetuals = [
                _s.get("id")
                for _s in _symbols
                if isinstance(_s, dict) and _s.get("type") == "perpetual"
            ]
            if _perpetuals:
                print(f"\nPerpetuals ({len(_perpetuals)}):")
                for _p in _perpetuals[:20]:
                    print(f"  - {_p}")
                if len(_perpetuals) > 20:
                    print(f"  ... and {len(_perpetuals) - 20} more")
            print()
        except Exception as _e:
            print(f"Error: {_e}")

    exchange_records = []
    for ex in exchanges_data:
        available_since = ex.get("availableSince", "")
        available_to = ex.get("availableTo", "")

        exchange_records.append(
            {
                "ID": ex["id"],
                "Name": ex["name"],
                "Enabled": "✅" if ex.get("enabled", False) else "❌",
                "Delisted": "⚠️" if ex.get("delisted", False) else "",
                "Available Since": available_since[:10] if available_since else "N/A",
                "Available To": available_to[:10] if available_to else "Present",
                "Channels": len(ex.get("availableChannels", [])),
            }
        )

    exchanges_df = pl.DataFrame(exchange_records)
    return (exchanges_df,)


@app.cell
def _(exchanges_df, mo, pl):
    mo.md(f"""
    ## Available Exchanges

    Total: **{len(exchanges_df)}** exchanges  
    Active: **{len(exchanges_df.filter(pl.col("Enabled") == "✅"))}**  
    Delisted: **{len(exchanges_df.filter(pl.col("Delisted") == "⚠️"))}**
    """)
    return


@app.cell
def _(mo):
    show_delisted = mo.ui.checkbox(label="Show delisted exchanges", value=False)
    show_delisted
    return (show_delisted,)


@app.cell
def _(exchanges_df, mo, pl, show_delisted):
    filtered_exchanges = exchanges_df
    if not show_delisted.value:
        filtered_exchanges = exchanges_df.filter(pl.col("Delisted") == "")

    mo.ui.table(filtered_exchanges, selection=None)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Exchange Details
    """)
    return


@app.cell
def _(exchanges_data, mo, show_delisted):
    exchange_options = sorted(
        [
            ex["id"]
            for ex in exchanges_data
            if show_delisted.value or not ex.get("delisted", False)
        ]
    )

    exchange_selector = mo.ui.dropdown(
        options=exchange_options,
        value=(
            "binance-futures"
            if "binance-futures" in exchange_options
            else exchange_options[0] if exchange_options else None
        ),
        label="Select Exchange",
    )
    exchange_selector
    return (exchange_selector,)


@app.cell
def _(exchange_selector, exchanges_data, mo):
    mo.stop(not exchange_selector.value, mo.md("Select an exchange to view details"))

    selected_exchange = next(
        (ex for ex in exchanges_data if ex["id"] == exchange_selector.value), None
    )
    return (selected_exchange,)


@app.cell
def _(mo, selected_exchange):
    mo.stop(not selected_exchange, mo.md("Exchange not found"))

    channels = selected_exchange.get("availableChannels", [])

    mo.md(
        f"""
    ### {selected_exchange['name']} (`{selected_exchange['id']}`)

    - **Available Since:** {selected_exchange.get('availableSince', 'N/A')[:10]}
    - **Available To:** {selected_exchange.get('availableTo', 'Present')[:10] if selected_exchange.get('availableTo') else 'Present'}
    - **Status:** {'⚠️ Delisted' if selected_exchange.get('delisted') else '✅ Active'}
    - **Supports Datasets:** {'Yes' if selected_exchange.get('supportsDatasets') else 'No'}

    #### Available Channels ({len(channels)})

    {', '.join(f'`{ch}`' for ch in channels)}
    """
    )
    return


@app.cell
def _(mo):
    mo.md("""
    ## Fetch Live Symbol Data
    """)
    return


@app.cell
def _(exchange_selector, mo):
    fetch_symbols_btn = mo.ui.run_button(
        label=f"🔍 Fetch Symbols for {exchange_selector.value}"
    )
    fetch_symbols_btn
    return (fetch_symbols_btn,)


@app.cell
def _(exchange_selector, fetch_symbols_btn, httpx, mo):
    mo.stop(
        not fetch_symbols_btn.value,
        mo.md("Click the button above to fetch live symbol data"),
    )

    try:
        response = httpx.get(
            f"https://api.tardis.dev/v1/exchanges/{exchange_selector.value}",
            timeout=30.0,
        )
        response.raise_for_status()
        details = response.json()
        symbols_list = details.get("availableSymbols", [])
        available_data_types = details.get("availableDataTypes", [])
        mo.output.replace(mo.md(f"✅ Fetched {len(symbols_list)} symbols"))
    except Exception as e:
        symbols_list = []
        available_data_types = []
        mo.output.replace(mo.md(f"❌ Error: {e}"))
    return available_data_types, symbols_list


@app.cell
def _(available_data_types, mo, symbols_list):
    mo.stop(not symbols_list, mo.md("No symbols loaded. Click fetch button above."))

    mo.md(
        f"""
    ### Available Data Types

    {', '.join(f'`{dt}`' for dt in available_data_types) if available_data_types else 'Not available'}

    ### Symbols ({len(symbols_list)} total)
    """
    )
    return


@app.cell
def _(mo, symbols_list):
    mo.stop(not symbols_list, None)

    symbol_types = list(
        set(s.get("type", "unknown") for s in symbols_list if isinstance(s, dict))
    )

    type_filter = mo.ui.dropdown(
        options=["All"] + sorted(symbol_types), value="All", label="Filter by Type"
    )

    symbol_search = mo.ui.text(
        value="", label="Search Symbol", placeholder="e.g., BTC, ETH"
    )

    mo.hstack([type_filter, symbol_search])
    return symbol_search, type_filter


@app.cell
def _(mo, pl, symbol_search, symbols_list, type_filter):
    mo.stop(not symbols_list, None)

    symbol_records = []
    for sym in symbols_list:
        if isinstance(sym, dict):
            symbol_records.append(
                {
                    "Symbol": sym.get("id", "N/A"),
                    "Type": sym.get("type", "unknown"),
                    "Available Since": (
                        sym.get("availableSince", "N/A")[:10]
                        if sym.get("availableSince")
                        else "N/A"
                    ),
                    "Available To": (
                        sym.get("availableTo", "Present")[:10]
                        if sym.get("availableTo")
                        else "Present"
                    ),
                }
            )
        else:
            symbol_records.append(
                {
                    "Symbol": str(sym),
                    "Type": "unknown",
                    "Available Since": "N/A",
                    "Available To": "Present",
                }
            )

    symbols_df = pl.DataFrame(symbol_records)

    filtered_symbols = symbols_df
    if type_filter.value != "All":
        filtered_symbols = filtered_symbols.filter(pl.col("Type") == type_filter.value)

    if symbol_search.value:
        search_term = symbol_search.value.upper()
        filtered_symbols = filtered_symbols.filter(
            pl.col("Symbol").str.to_uppercase().str.contains(search_term)
        )
    return (filtered_symbols,)


@app.cell
def _(filtered_symbols, mo):
    mo.stop(filtered_symbols is None, None)

    mo.md(f"Showing **{len(filtered_symbols)}** symbols")
    return


@app.cell
def _(filtered_symbols, mo):
    mo.stop(
        filtered_symbols is None or len(filtered_symbols) == 0,
        mo.md("No symbols match the filter"),
    )

    mo.ui.table(filtered_symbols, selection=None)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Common Data Types Reference

    | Data Type | Description | Size |
    |-----------|-------------|------|
    | `trades` | Individual trade executions | Small |
    | `quotes` | Top-of-book best bid/ask | Small |
    | `incremental_book_L2` | Full L2 orderbook updates | **Large** |
    | `book_snapshot_25` | Top 25 levels snapshot | Medium |
    | `book_snapshot_5` | Top 5 levels snapshot | Small |
    | `derivative_ticker` | Funding rate, mark price, OI | Small |
    | `liquidations` | Forced liquidation orders | Small |

    ---

    ## CLI Usage

    ```bash
    # Interactive mode (opens browser UI)
    marimo run notebooks/marimos/data_explorer.py

    # CLI mode - list all exchanges
    marimo run notebooks/marimos/data_explorer.py -- --list-exchanges

    # CLI mode - fetch symbols for an exchange
    marimo run notebooks/marimos/data_explorer.py -- --exchange binance-futures --fetch

    # Using uv
    uv run marimo run notebooks/marimos/data_explorer.py -- --list-exchanges
    ```
    """)
    return


if __name__ == "__main__":
    app.run()
