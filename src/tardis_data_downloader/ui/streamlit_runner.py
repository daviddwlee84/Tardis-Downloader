#!/usr/bin/env python3
"""
Streamlit runner for Tardis Data Downloader UI
"""
import subprocess
import sys
import os
from pathlib import Path


def run_streamlit():
    """Run streamlit with Overview.py"""
    # Get the path to Overview.py
    current_dir = Path(__file__).parent
    overview_path = current_dir / "Overview.py"

    # Run streamlit
    cmd = ["streamlit", "run", str(overview_path)]
    print(f"Running: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Streamlit stopped by user")
        sys.exit(0)


def main():
    """Main entry point"""
    run_streamlit()


if __name__ == "__main__":
    main()
