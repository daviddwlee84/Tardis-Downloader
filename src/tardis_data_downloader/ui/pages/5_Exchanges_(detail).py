import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from collections import Counter
import os

st.title("📊 All Exchanges Overview Analysis")
st.set_page_config(layout="wide", page_icon="🌍")

# Import the data manager
from tardis_data_downloader.data.data_manager import TardisApi

# Optional parameters in expander
with st.expander("Advanced Options"):
    http_proxy = st.text_input(
        "HTTP Proxy", help="HTTP proxy URL (leave empty if not required)"
    )


# Cache function to get exchanges data
@st.cache_data
def get_exchanges_data(http_proxy: str | None = None) -> list:
    api = TardisApi(http_proxy=http_proxy)
    return api.get_exchanges()


# Use session state to track fetched data
if "exchanges_data" not in st.session_state:
    st.session_state.exchanges_data = None

# Load data
if st.session_state.exchanges_data is None:
    with st.spinner("Loading exchanges data..."):
        try:
            exchanges_data = get_exchanges_data(http_proxy)
            st.session_state.exchanges_data = exchanges_data
        except Exception as e:
            st.error(f"❌ Error loading data: {e}")
            st.stop()
else:
    exchanges_data = st.session_state.exchanges_data

# Refresh button
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.session_state.exchanges_data = None
    st.rerun()

if not exchanges_data:
    st.error("❌ No exchanges data available!")
    st.stop()

# Create DataFrame for analysis
df_exchanges = pd.DataFrame(exchanges_data)

# Convert dates to datetime
df_exchanges["availableSince"] = pd.to_datetime(df_exchanges["availableSince"])
df_exchanges["availableTo"] = pd.to_datetime(
    df_exchanges["availableTo"], errors="coerce"
)
df_exchanges["year"] = df_exchanges["availableSince"].dt.year
df_exchanges["month"] = df_exchanges["availableSince"].dt.month

# Add status column
df_exchanges["status"] = df_exchanges["availableTo"].apply(
    lambda x: "Delisted" if pd.notna(x) else "Active"
)

# Sidebar filters
st.sidebar.title("🎛️ Filters")

# Status filter
status_options = sorted(df_exchanges["status"].unique())
selected_status = st.sidebar.multiselect(
    "Exchange Status",
    options=status_options,
    default=status_options,
    help="Filter by exchange status",
)

# Dataset support filter
dataset_options = ["Supports Datasets", "No Dataset Support"]
selected_datasets = st.sidebar.multiselect(
    "Dataset Support",
    options=dataset_options,
    default=dataset_options,
    help="Filter by dataset support",
)

# Year filter
years = sorted(df_exchanges["year"].unique())
selected_years = st.sidebar.multiselect(
    "Available Years",
    options=years,
    default=years,
    help="Filter by year when exchange became available",
)

# Apply filters
dataset_filter = []
if "Supports Datasets" in selected_datasets:
    dataset_filter.append(True)
if "No Dataset Support" in selected_datasets:
    dataset_filter.append(False)

filtered_df = df_exchanges[
    (df_exchanges["status"].isin(selected_status))
    & (df_exchanges["supportsDatasets"].isin(dataset_filter))
    & (df_exchanges["year"].isin(selected_years))
]

# Show current filter summary
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Current Filters")
st.sidebar.write(
    f"**Status:** {', '.join(selected_status) if selected_status else 'None'}"
)
st.sidebar.write(
    f"**Dataset Support:** {', '.join(selected_datasets) if selected_datasets else 'None'}"
)
st.sidebar.write(
    f"**Years:** {', '.join(map(str, selected_years)) if selected_years else 'None'}"
)
st.sidebar.write(f"**Filtered Results:** {len(filtered_df)} exchanges")

# Main content - Overview Metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🏢 Total Exchanges", f"{len(df_exchanges):,}")

with col2:
    st.metric(
        "✅ Active Exchanges",
        f"{len(df_exchanges[df_exchanges['status'] == 'Active']):,}",
    )

with col3:
    st.metric(
        "⏸️ Delisted Exchanges",
        f"{len(df_exchanges[df_exchanges['status'] == 'Delisted']):,}",
    )

with col4:
    st.metric(
        "📊 Dataset Support", f"{len(df_exchanges[df_exchanges['supportsDatasets']])}"
    )

# Overview Section
st.header("📋 Exchange Overview")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📊 Status Distribution")

    # Status distribution
    status_counts = filtered_df["status"].value_counts()

    # Pie chart for status
    fig_status = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        title="Exchange Status Distribution",
        color_discrete_sequence=["#00ff00", "#ff6b6b"],
    )
    fig_status.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig_status, width="stretch")

with col2:
    st.subheader("📈 Dataset Support")

    # Dataset support distribution
    dataset_counts = filtered_df["supportsDatasets"].value_counts()

    # Bar chart for dataset support
    fig_dataset = px.bar(
        x=[
            "Supports Datasets" if k else "No Dataset Support"
            for k in dataset_counts.index
        ],
        y=dataset_counts.values,
        title="Dataset Support Distribution",
        color=["#00ff00" if k else "#ff6b6b" for k in dataset_counts.index],
        color_discrete_sequence=["#00ff00", "#ff6b6b"],
    )
    fig_dataset.update_layout(showlegend=False)
    st.plotly_chart(fig_dataset, width="stretch")

# Timeline Analysis
st.header("⏰ Timeline Analysis")

# Yearly distribution
st.subheader("📅 Exchanges by Year")

yearly_counts = filtered_df.groupby(["year", "status"]).size().reset_index(name="count")

fig_yearly = px.bar(
    yearly_counts,
    x="year",
    y="count",
    color="status",
    title="Exchanges Available by Year and Status",
    labels={"year": "Year", "count": "Number of Exchanges", "status": "Status"},
    barmode="stack",
    color_discrete_sequence=["#00ff00", "#ff6b6b"],
)
st.plotly_chart(fig_yearly, width="stretch")

# Monthly distribution for recent years
st.subheader("📆 Monthly Distribution (Recent Years)")

recent_years = (
    sorted(filtered_df["year"].unique())[-3:]
    if len(filtered_df["year"].unique()) >= 3
    else sorted(filtered_df["year"].unique())
)
recent_df = filtered_df[filtered_df["year"].isin(recent_years)]

monthly_counts = (
    recent_df.groupby(["year", "month", "status"]).size().reset_index(name="count")
)
monthly_counts["year_month"] = (
    monthly_counts["year"].astype(str)
    + "-"
    + monthly_counts["month"].astype(str).str.zfill(2)
)

fig_monthly = px.line(
    monthly_counts,
    x="year_month",
    y="count",
    color="status",
    title="Monthly Exchange Availability (Recent Years)",
    labels={
        "year_month": "Year-Month",
        "count": "Number of Exchanges",
        "status": "Status",
    },
    markers=True,
    color_discrete_sequence=["#00ff00", "#ff6b6b"],
)
fig_monthly.update_xaxes(tickangle=45)
st.plotly_chart(fig_monthly, width="stretch")

# Channel Analysis
st.header("📡 Channel Analysis")

# Flatten channels for analysis
all_channels = []
for _, row in filtered_df.iterrows():
    if row["availableChannels"]:
        for channel in row["availableChannels"]:
            all_channels.append(
                {"exchange": row["name"], "channel": channel, "status": row["status"]}
            )

if all_channels:
    df_channels = pd.DataFrame(all_channels)

    # Top channels
    st.subheader("🔝 Most Popular Channels")
    channel_counts = df_channels["channel"].value_counts().head(20)

    fig_channels = px.bar(
        x=channel_counts.index,
        y=channel_counts.values,
        title="Top 20 Most Popular Channels",
        labels={"x": "Channel", "y": "Count"},
    )
    fig_channels.update_xaxes(tickangle=45)
    st.plotly_chart(fig_channels, width="stretch")

    # Channels by exchange status
    st.subheader("📊 Channels by Exchange Status")

    channel_status_counts = (
        df_channels.groupby(["channel", "status"]).size().reset_index(name="count")
    )

    # Get top 10 channels for better visualization
    top_channels = df_channels["channel"].value_counts().head(10).index
    top_channel_status = channel_status_counts[
        channel_status_counts["channel"].isin(top_channels)
    ]

    fig_channel_status = px.bar(
        top_channel_status,
        x="channel",
        y="count",
        color="status",
        title="Top 10 Channels by Exchange Status",
        labels={"channel": "Channel", "count": "Count", "status": "Exchange Status"},
        barmode="stack",
        color_discrete_sequence=["#00ff00", "#ff6b6b"],
    )
    fig_channel_status.update_xaxes(tickangle=45)
    st.plotly_chart(fig_channel_status, width="stretch")

# Exchange Details Table
st.header("📋 Exchange Details")

col1, col2 = st.columns([2, 1])

with col1:

    if not filtered_df.empty:

        # Display exchange details
        st.dataframe(
            filtered_df[
                ["name", "id", "status", "supportsDatasets", "availableSince"]
            ].rename(
                columns={
                    "name": "Exchange Name",
                    "id": "Exchange ID",
                    "status": "Status",
                    "supportsDatasets": "Dataset Support",
                    "availableSince": "Available Since",
                }
            ),
            width="stretch",
            column_config={
                "Exchange Name": st.column_config.TextColumn(
                    "Exchange Name", width="large"
                ),
                "Exchange ID": st.column_config.TextColumn(
                    "Exchange ID", width="medium"
                ),
                "Status": st.column_config.TextColumn("Status", width="small"),
                "Dataset Support": st.column_config.TextColumn(
                    "Dataset Support", width="small"
                ),
                "Available Since": st.column_config.DatetimeColumn(
                    "Available Since", width="medium"
                ),
            },
        )

        st.info(f"Showing {len(filtered_df)} total filtered results")

with col2:
    # Search functionality
    st.subheader("🔎 Search Exchanges")
    search_term = st.text_input(
        "Search by Exchange Name", placeholder="Enter exchange name..."
    )

    if search_term:
        search_results = filtered_df[
            filtered_df["name"].str.contains(search_term, case=False, na=False)
        ]
        if not search_results.empty:
            st.dataframe(
                search_results[["name", "id", "status", "supportsDatasets"]].rename(
                    columns={
                        "name": "Exchange Name",
                        "id": "Exchange ID",
                        "status": "Status",
                        "supportsDatasets": "Dataset Support",
                    }
                ),
                width="stretch",
            )
            st.success(f"Found {len(search_results)} matching exchanges")
        else:
            st.info("No exchanges found matching the search term")

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
            file_name="exchanges_filtered.csv",
            mime="text/csv",
            type="primary",
        )

with col2:
    # Export statistics
    if st.button("📊 Export Statistics (JSON)"):
        stats_dict = {
            "total_exchanges": len(df_exchanges),
            "active_exchanges": len(df_exchanges[df_exchanges["status"] == "Active"]),
            "delisted_exchanges": len(
                df_exchanges[df_exchanges["status"] == "Delisted"]
            ),
            "dataset_support_count": len(
                df_exchanges[df_exchanges["supportsDatasets"]]
            ),
            "yearly_distribution": filtered_df.groupby(["year", "status"])
            .size()
            .to_dict(),
            "top_channels": (
                dict(df_channels["channel"].value_counts().head(10))
                if "df_channels" in locals()
                else {}
            ),
        }

        st.download_button(
            label="Download Statistics JSON",
            data=json.dumps(stats_dict, indent=2, default=str),
            file_name="exchanges_statistics.json",
            mime="application/json",
            type="primary",
        )

with col3:
    # Show raw JSON structure
    with st.expander("🔧 Raw JSON Structure"):
        st.json(exchanges_data[:3], expanded=False)  # Show first 3 exchanges as sample

# Footer
st.markdown("---")
st.markdown("*Data sourced from: Tardis API (https://api.tardis.dev/v1/exchanges/)*")
st.markdown("*Built with Streamlit & Plotly*")
