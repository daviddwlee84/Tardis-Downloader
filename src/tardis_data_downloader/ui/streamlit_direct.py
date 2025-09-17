#!/usr/bin/env python3
"""
Direct Streamlit runner for Tardis Data Downloader UI
"""
import sys
import os
from pathlib import Path


def main():
    """Direct entry point for streamlit"""
    # Get the path to Overview.py
    current_dir = Path(__file__).parent
    overview_path = current_dir / "Overview.py"

    # Import streamlit and run directly
    try:
        import streamlit.web.cli as st_cli

        # Simulate command line arguments for streamlit run
        sys.argv = ["streamlit", "run", str(overview_path)]
        st_cli.main()
    except ImportError as e:
        print(f"Error importing streamlit: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error running streamlit: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
