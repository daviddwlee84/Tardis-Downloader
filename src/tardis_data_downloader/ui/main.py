import streamlit as st

st.set_page_config(page_title="Tardis Data Downloader", page_icon="📊", layout="wide")

st.title("📊 Tardis Data Downloader")
st.markdown(
    "A tool for downloading and managing cryptocurrency market data from Tardis."
)

st.markdown(
    """
## Features

- 📥 **Download Data**: Download historical market data from various exchanges
- 📊 **View Raw Data**: Explore and analyze downloaded data
- 🔧 **Data Management**: Organize and manage your data collections

## Getting Started

Select a page from the sidebar to get started with downloading or viewing your data.
"""
)

# Show some basic info
st.info(
    "💡 Tip: Use the sidebar to navigate between different features of the application."
)

if __name__ == "__main__":
    pass
