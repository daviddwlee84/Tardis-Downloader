import streamlit as st
from tardis_data_downloader.data.data_manager import (
    EXCHANGE,
    TardisDataManager,
)
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from collections import Counter
import os

st.title("🔍 Deribit Exchange Detail Analysis")
st.set_page_config(layout="wide", page_icon="📊")

# Import the data manager
from tardis_data_downloader.data.data_manager import EXCHANGE, TardisDataManager

# Exchange selection
EXCHANGE_LIST = [e.value for e in EXCHANGE]
exchange = st.selectbox(
    "Exchange",
    options=EXCHANGE_LIST,
    index=EXCHANGE_LIST.index("deribit") if "deribit" in EXCHANGE_LIST else 0,
    key="exchange_selector",
)

# Optional parameters in expander
with st.expander("Advanced Options"):
    http_proxy = st.text_input(
        "HTTP Proxy", help="HTTP proxy URL (leave empty if not required)"
    )


# Cache function to get exchange detail data
@st.cache_data
def get_exchange_detail(exchange: str, _http_proxy: str | None = None) -> dict:
    manager = TardisDataManager(exchange=exchange)
    return manager.get_exchange_details(http_proxy)


# Use session state to track fetched data and current exchange
if "exchange_detail" not in st.session_state:
    st.session_state.exchange_detail = None
    st.session_state.current_exchange = None

# Check if exchange changed, clear cache if so
if st.session_state.current_exchange != exchange:
    st.session_state.exchange_detail = None
    st.session_state.current_exchange = exchange

# Load data
if st.session_state.exchange_detail is None:
    with st.spinner("Loading exchange data..."):
        try:
            deribit_data = get_exchange_detail(exchange, http_proxy)
            st.session_state.exchange_detail = deribit_data
        except Exception as e:
            st.error(f"❌ Error loading data: {e}")
            st.stop()
else:
    deribit_data = st.session_state.exchange_detail

# Refresh button
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.session_state.exchange_detail = None
    st.rerun()

# Extract symbols data
symbols = deribit_data.get("availableSymbols", [])

# Create DataFrame for analysis
df_symbols = pd.DataFrame(symbols)

# Convert dates to datetime
df_symbols["availableSince"] = pd.to_datetime(df_symbols["availableSince"])
df_symbols["year_month"] = df_symbols["availableSince"].dt.to_period("M")
df_symbols["year"] = df_symbols["availableSince"].dt.year

# Handle availableTo field
df_symbols["availableTo"] = pd.to_datetime(df_symbols["availableTo"], errors="coerce")
df_symbols["is_active"] = df_symbols["availableTo"].isna()
df_symbols["availableTo_year"] = df_symbols["availableTo"].dt.year

# Sidebar for filters
st.sidebar.title("📊 Filters")

# Active/Inactive filter
active_options = ["Active", "Inactive"]
selected_status = st.sidebar.multiselect(
    "Symbol Status",
    options=active_options,
    default=active_options,
    help="Filter by active or inactive symbols",
)

# Symbol type filter
symbol_types = sorted(df_symbols["type"].unique())
selected_types = st.sidebar.multiselect(
    "Symbol Types",
    options=symbol_types,
    default=symbol_types,
    help="Filter symbols by type",
)

# Year filter
years = sorted(df_symbols["year"].unique())
selected_years = st.sidebar.multiselect(
    "Available Years",
    options=years,
    default=years,
    help="Filter by year when symbols became available",
)

# Apply filters
# Status filter logic
if "Active" in selected_status and "Inactive" in selected_status:
    # Show both active and inactive
    status_condition = True
elif "Active" in selected_status:
    # Show only active
    status_condition = df_symbols["is_active"]
elif "Inactive" in selected_status:
    # Show only inactive
    status_condition = ~df_symbols["is_active"]
else:
    # No status selected, show nothing
    status_condition = False

# Apply all filters
filtered_df = df_symbols[
    status_condition
    & (df_symbols["type"].isin(selected_types))
    & (df_symbols["year"].isin(selected_years))
]

# Show current filter summary
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Current Filters")
st.sidebar.write(
    f"**Status:** {', '.join(selected_status) if selected_status else 'None'}"
)
st.sidebar.write(
    f"**Types:** {', '.join(selected_types) if selected_types else 'None'}"
)
st.sidebar.write(
    f"**Years:** {', '.join(map(str, selected_years)) if selected_years else 'None'}"
)
st.sidebar.write(f"**Filtered Results:** {len(filtered_df)} symbols")

# Main content
col1, col2, col3, col4 = st.columns(4)

active_count = df_symbols["is_active"].sum()
inactive_count = len(df_symbols) - active_count

with col1:
    st.metric("📈 Total Symbols", f"{len(df_symbols):,}")

with col2:
    st.metric("✅ Active Symbols", f"{active_count:,}")

with col3:
    st.metric("⏸️ Inactive Symbols", f"{inactive_count:,}")

with col4:
    st.metric("🎯 Types", len(df_symbols["type"].unique()))

# Overview Section
st.header("📋 Exchange Overview")
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Basic Information")
    info_data = {
        "Exchange ID": deribit_data.get("id", "N/A"),
        "Name": deribit_data.get("name", "N/A"),
        "Enabled": "✅ Yes" if deribit_data.get("enabled", False) else "❌ No",
        "Available Since": deribit_data.get("availableSince", "N/A"),
    }

    for key, value in info_data.items():
        st.write(f"**{key}:** {value}")

with col2:
    st.subheader("Available Channels")
    channels = deribit_data.get("availableChannels", [])
    if channels:
        # Create a nice grid layout for channels
        cols = st.columns(3)
        for i, channel in enumerate(channels):
            cols[i % 3].write(f"• {channel}")
    else:
        st.write("No channels available")

# Statistics Section
st.header("📊 Symbol Statistics")

# Symbol Type Distribution
st.subheader("🎯 Symbol Type Distribution")

col1, col2 = st.columns([1, 1])

# Use filtered data for statistics
type_counts = (
    filtered_df["type"].value_counts()
    if not filtered_df.empty
    else df_symbols["type"].value_counts()
)

with col1:
    # Pie Chart
    fig_pie = px.pie(
        values=type_counts.values,
        names=type_counts.index,
        title="Symbol Types Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    fig_pie.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig_pie, width="stretch")

with col2:
    # Bar Chart
    fig_bar = px.bar(
        x=type_counts.index,
        y=type_counts.values,
        title="Symbol Count by Type",
        labels={"x": "Type", "y": "Count"},
        color=type_counts.index,
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    fig_bar.update_layout(showlegend=False)
    st.plotly_chart(fig_bar, width="stretch")

# Statistics Table
st.subheader("📈 Detailed Statistics")

# Calculate percentages and active status using filtered data
total_symbols = len(filtered_df) if not filtered_df.empty else len(df_symbols)
stats_data = []
for symbol_type, count in type_counts.items():
    percentage = (count / total_symbols) * 100
    # Use filtered data for active/inactive counts
    type_df = (
        filtered_df[filtered_df["type"] == symbol_type]
        if not filtered_df.empty
        else df_symbols[df_symbols["type"] == symbol_type]
    )
    type_active = type_df["is_active"].sum()
    type_inactive = len(type_df) - type_active
    stats_data.append(
        {
            "Type": symbol_type,
            "Total": count,
            "Active": type_active,
            "Inactive": type_inactive,
            "Percentage": ".2f",
        }
    )

stats_df = pd.DataFrame(stats_data)
st.dataframe(stats_df, width="stretch")

# Active vs Inactive Analysis
st.subheader("📊 Active vs Inactive Symbols")

col1, col2 = st.columns([1, 1])

# Use filtered data for active/inactive analysis
filtered_active_count = (
    filtered_df["is_active"].sum() if not filtered_df.empty else active_count
)
filtered_inactive_count = (
    len(filtered_df) - filtered_active_count
    if not filtered_df.empty
    else inactive_count
)

with col1:
    # Active/Inactive Pie Chart
    if not filtered_df.empty and (
        filtered_active_count > 0 or filtered_inactive_count > 0
    ):
        fig_active_pie = px.pie(
            values=[filtered_active_count, filtered_inactive_count],
            names=["Active", "Inactive"],
            title="Active vs Inactive Symbols (Filtered)",
            color_discrete_sequence=["#00ff00", "#ff6b6b"],
        )
        fig_active_pie.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_active_pie, width="stretch")
    else:
        st.info("No data to display for the current filters")

with col2:
    # Active/Inactive by Type
    if not filtered_df.empty:
        active_by_type = filtered_df[filtered_df["is_active"]].groupby("type").size()
        inactive_by_type = filtered_df[~filtered_df["is_active"]].groupby("type").size()

        # Combine for plotting
        combined_data = []
        for symbol_type in filtered_df["type"].unique():
            combined_data.append(
                {
                    "Type": symbol_type,
                    "Active": active_by_type.get(symbol_type, 0),
                    "Inactive": inactive_by_type.get(symbol_type, 0),
                }
            )
    else:
        combined_data = []

    combined_df = pd.DataFrame(combined_data)

    fig_active_bar = px.bar(
        combined_df,
        x="Type",
        y=["Active", "Inactive"],
        title="Active/Inactive by Symbol Type",
        barmode="stack",
        color_discrete_sequence=["#00ff00", "#ff6b6b"],
    )
    st.plotly_chart(fig_active_bar, width="stretch")

# Timeline Analysis
st.header("⏰ Timeline Analysis")

# Yearly distribution
st.subheader("📅 Symbols Available by Year")

# Use filtered data for timeline analysis
timeline_df = filtered_df if not filtered_df.empty else df_symbols
yearly_counts = timeline_df.groupby(["year", "type"]).size().reset_index(name="count")

fig_yearly = px.bar(
    yearly_counts,
    x="year",
    y="count",
    color="type",
    title="Symbol Availability by Year and Type",
    labels={"year": "Year", "count": "Number of Symbols", "type": "Symbol Type"},
    barmode="stack",
    color_discrete_sequence=px.colors.qualitative.Set3,
)
st.plotly_chart(fig_yearly, width="stretch")

# Monthly distribution for recent years
st.subheader("📆 Monthly Distribution (Last 3 Years)")

# Use filtered data for monthly analysis
monthly_analysis_df = timeline_df
recent_years = (
    sorted(monthly_analysis_df["year"].unique())[-3:]
    if len(monthly_analysis_df["year"].unique()) >= 3
    else sorted(monthly_analysis_df["year"].unique())
)
recent_df = monthly_analysis_df[monthly_analysis_df["year"].isin(recent_years)]

monthly_counts = (
    recent_df.groupby(["year_month", "type"]).size().reset_index(name="count")
)
monthly_counts["year_month"] = monthly_counts["year_month"].astype(str)

fig_monthly = px.line(
    monthly_counts,
    x="year_month",
    y="count",
    color="type",
    title="Monthly Symbol Availability (Recent Years)",
    labels={
        "year_month": "Year-Month",
        "count": "Number of Symbols",
        "type": "Symbol Type",
    },
    markers=True,
    color_discrete_sequence=px.colors.qualitative.Set3,
)
fig_monthly.update_xaxes(tickangle=45)
st.plotly_chart(fig_monthly, width="stretch")

# Inactive Symbols Timeline
st.subheader("⏸️ Symbol Deactivation Timeline")

# Use filtered data for deactivation analysis
inactive_symbols = timeline_df[~timeline_df["is_active"]].copy()
if not inactive_symbols.empty:
    inactive_yearly = (
        inactive_symbols.groupby(["availableTo_year", "type"])
        .size()
        .reset_index(name="count")
    )

    fig_inactive = px.bar(
        inactive_yearly,
        x="availableTo_year",
        y="count",
        color="type",
        title="Symbols Deactivated by Year and Type (Filtered)",
        labels={
            "availableTo_year": "Year Deactivated",
            "count": "Number of Symbols",
            "type": "Symbol Type",
        },
        barmode="stack",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    st.plotly_chart(fig_inactive, width="stretch")

    # Top deactivation years
    deactivation_years = inactive_symbols["availableTo_year"].value_counts().head(10)
    st.subheader("📅 Top Years with Most Deactivations")
    st.bar_chart(deactivation_years)
else:
    st.info("No inactive symbols found in the current filters!")

# Sample Data Section
st.header("🔍 Sample Data")

col1, col2 = st.columns([1, 2])

with col1:
    # Show sample of symbols
    st.subheader("📋 Sample Symbols")
    if not filtered_df.empty:
        sample_size = st.slider(
            "Sample Size",
            min_value=5,
            max_value=min(50, len(filtered_df)),
            value=min(10, len(filtered_df)),
        )

        sample_df = filtered_df.sample(min(sample_size, len(filtered_df)))
        display_columns = ["id", "type", "is_active", "availableSince"]
        if not sample_df["availableTo"].isna().all():
            display_columns.append("availableTo")

        st.dataframe(
            sample_df[display_columns],
            width="stretch",
            column_config={
                "id": st.column_config.TextColumn("Symbol ID", width="medium"),
                "type": st.column_config.TextColumn("Type", width="small"),
                "is_active": st.column_config.TextColumn("Active", width="small"),
                "availableSince": st.column_config.DatetimeColumn(
                    "Available Since", width="medium"
                ),
                "availableTo": st.column_config.DatetimeColumn(
                    "Available To", width="medium"
                ),
            },
        )
        st.info(
            f"Showing {len(sample_df)} sample symbols out of {len(filtered_df)} total filtered results"
        )
    else:
        st.warning(
            "No data matches the selected filters. Try adjusting your filter criteria."
        )

with col2:
    # Search functionality
    st.subheader("🔎 Search Symbols")
    search_term = st.text_input("Search by Symbol ID", placeholder="Enter symbol ID...")

    if search_term:
        # Use filtered data for search
        search_base = filtered_df if not filtered_df.empty else df_symbols
        search_results = search_base[
            search_base["id"].str.contains(search_term, case=False, na=False)
        ]
        if not search_results.empty:
            display_columns = ["id", "type", "is_active", "availableSince"]
            if not search_results["availableTo"].isna().all():
                display_columns.append("availableTo")

            st.dataframe(
                search_results[display_columns],
                width="stretch",
                column_config={
                    "id": st.column_config.TextColumn("Symbol ID", width="large"),
                    "type": st.column_config.TextColumn("Type", width="small"),
                    "is_active": st.column_config.TextColumn("Active", width="small"),
                    "availableSince": st.column_config.DatetimeColumn(
                        "Available Since", width="medium"
                    ),
                    "availableTo": st.column_config.DatetimeColumn(
                        "Available To", width="medium"
                    ),
                },
            )
            st.success(f"Found {len(search_results)} matching symbols")
        else:
            st.info("No symbols found matching the search term")

# Export Section
st.header("💾 Export & Raw Data")

col1, col2, col3 = st.columns(3)

with col1:
    # Export filtered data
    if st.button("📥 Export Filtered Data (CSV)"):
        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name="deribit_filtered_symbols.csv",
            mime="text/csv",
            type="primary",
        )

with col2:
    # Export statistics
    if st.button("📊 Export Statistics (JSON)"):
        stats_dict = {
            "total_symbols": len(df_symbols),
            "type_distribution": type_counts.to_dict(),
            "yearly_distribution": yearly_counts.to_dict("records"),
            "exchange_info": {
                "id": deribit_data.get("id"),
                "name": deribit_data.get("name"),
                "enabled": deribit_data.get("enabled"),
                "available_since": deribit_data.get("availableSince"),
                "channels": deribit_data.get("availableChannels", []),
            },
        }

        st.download_button(
            label="Download Statistics JSON",
            data=json.dumps(stats_dict, indent=2, default=str),
            file_name="deribit_statistics.json",
            mime="application/json",
            type="primary",
        )

with col3:
    # Show raw JSON structure
    with st.expander("🔧 Raw JSON Structure"):
        st.json(deribit_data, expanded=False)

# Footer
st.markdown("---")
st.markdown("*Data last updated: Based on deribit_exchange_detail.json*")
st.markdown("*Built with Streamlit & Plotly*")
