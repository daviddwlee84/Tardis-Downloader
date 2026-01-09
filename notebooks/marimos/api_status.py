# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx",
#     "marimo",
#     "polars",
#     "altair",
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
    import os
    from datetime import datetime
    return alt, datetime, httpx, mo, os, pl


@app.cell
def _(mo):
    mo.md("""
    # Tardis API Status

    This notebook queries and displays your Tardis API key information, showing access types,
    date ranges, and data plans for each exchange.

    ---
    """)
    return


@app.cell
def _(mo):
    cli_args = mo.cli_args()
    is_script_mode = mo.app_meta().mode == "script"
    return


@app.cell
def _(httpx, mo, os):
    def fetch_api_key_info():
        api_key = os.environ.get("TARDIS_API_KEY")
        if not api_key:
            return None, "TARDIS_API_KEY environment variable not set"

        try:
            response = httpx.get(
                "https://api.tardis.dev/v1/api-key-info",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json(), None
        except httpx.HTTPError as e:
            return None, f"HTTP error: {e}"
        except Exception as e:
            return None, f"Error: {e}"

    refresh_button = mo.ui.run_button(label="🔄 Refresh API Status")
    refresh_button
    return fetch_api_key_info, refresh_button


@app.cell
def _(fetch_api_key_info, mo, refresh_button):
    _ = refresh_button.value
    api_data, error = fetch_api_key_info()

    if error:
        mo.output.replace(mo.md(f"**Error:** {error}"))
    return api_data, error


@app.cell
def _(api_data, datetime, error, mo, pl):
    mo.stop(error is not None or api_data is None, mo.md("⚠️ No API data available. Check your TARDIS_API_KEY."))

    records = []
    for _item in api_data:
        from_date = datetime.fromisoformat(_item["from"].replace("Z", "+00:00"))
        to_date = datetime.fromisoformat(_item["to"].replace("Z", "+00:00"))
        records.append({
            "Exchange": _item["exchange"],
            "Access Type": _item["accessType"],
            "Data Plan": _item["dataPlan"],
            "From": from_date.strftime("%Y-%m-%d"),
            "To": to_date.strftime("%Y-%m-%d"),
            "Days Available": (to_date - from_date).days,
            "Symbols Filter": ", ".join(_item.get("symbols", [])) if _item.get("symbols") else "All"
        })

    df = pl.DataFrame(records)
    return (df,)


@app.cell
def _(df, mo):
    mo.md(f"""
    ## Summary

    - **Total Exchanges:** {len(df)}
    - **Access Types:** {", ".join(df["Access Type"].unique().to_list())}
    - **Data Plans:** {", ".join(df["Data Plan"].unique().to_list())}
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Exchange Access Details
    """)
    return


@app.cell
def _(df, mo):
    mo.ui.table(df, selection=None)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Data Availability Timeline
    """)
    return


@app.cell
def _(alt, api_data, datetime, pl):
    timeline_data = []
    for _item in api_data:
        from_dt = datetime.fromisoformat(_item["from"].replace("Z", "+00:00"))
        to_dt = datetime.fromisoformat(_item["to"].replace("Z", "+00:00"))
        timeline_data.append({
            "Exchange": _item["exchange"],
            "Start": from_dt,
            "End": to_dt,
            "Data Plan": _item["dataPlan"]
        })

    timeline_df = pl.DataFrame(timeline_data)

    chart = alt.Chart(timeline_df).mark_bar().encode(
        y=alt.Y("Exchange:N", sort="-x", title="Exchange"),
        x=alt.X("Start:T", title="Date"),
        x2=alt.X2("End:T"),
        color=alt.Color("Data Plan:N", scale=alt.Scale(scheme="category10")),
        tooltip=["Exchange", "Start", "End", "Data Plan"]
    ).properties(
        title="Historical Data Availability by Exchange",
        width=700,
        height=max(400, len(timeline_data) * 20)
    )

    chart
    return


@app.cell
def _(api_data, mo):
    perpetuals_exchanges = [x["exchange"] for x in api_data if x.get("dataPlan") == "perpetuals"]

    mo.md(f"""
    ## Perpetuals Plan Exchanges

    Your API key has access to perpetuals data from the following **{len(perpetuals_exchanges)}** exchanges:

    {chr(10).join(f"- `{ex}`" for ex in sorted(perpetuals_exchanges))}
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ---

    ## CLI Usage

    Run this notebook from command line:

    ```bash
    # Interactive mode
    marimo run notebooks/marimos/api_status.py

    # Or using uv
    uv run marimo run notebooks/marimos/api_status.py
    ```
    """)
    return


if __name__ == "__main__":
    app.run()
