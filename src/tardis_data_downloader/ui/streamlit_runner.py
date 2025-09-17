#!/usr/bin/env python3
"""
Streamlit runner for Tardis Data Downloader UI
"""
import subprocess
import sys
import os
import argparse
from pathlib import Path


def run_streamlit(
    run_on_save=False,
    file_watcher_type="auto",
    server_port=None,
    headless=False,
    dry_run=False,
):
    """Run streamlit with Overview.py

    Args:
        run_on_save (bool): 是否在文件修改时自动重新运行
        file_watcher_type (str): 文件监视器类型 ("auto", "watchdog", "poll", "none")
        server_port (int): 服务器端口
        headless (bool): 是否以无头模式运行
        dry_run (bool): 仅显示命令而不执行
    """
    # Get the path to Overview.py
    current_dir = Path(__file__).parent
    overview_path = current_dir / "Overview.py"

    # Build streamlit command using Python module to ensure it works in any environment
    cmd = [sys.executable, "-m", "streamlit", "run", str(overview_path)]

    # Add file change detection options
    if run_on_save:
        cmd.extend(["--server.runOnSave", "true"])
        print("✓ 启用文件变更自动重载")

    if file_watcher_type != "auto":
        cmd.extend(["--server.fileWatcherType", file_watcher_type])
        print(f"✓ 文件监视器类型: {file_watcher_type}")

    if server_port:
        cmd.extend(["--server.port", str(server_port)])
        print(f"✓ 服务器端口: {server_port}")

    if headless:
        cmd.extend(["--server.headless", "true"])
        print("✓ 无头模式")

    print(f"运行命令: {' '.join(cmd)}")

    if dry_run:
        print("🔍 仅显示模式 - 不执行命令")
        return

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
    # TODO: use better argument parser (and make it English)
    parser = argparse.ArgumentParser(
        description="Tardis Data Downloader Streamlit UI Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python streamlit_runner.py                           # 基本运行
  python streamlit_runner.py --auto-reload             # 启用自动重载
  python streamlit_runner.py --auto-reload --watcher poll # 使用轮询监视器
  python streamlit_runner.py --port 8502               # 指定端口
  python streamlit_runner.py --headless                # 无头模式
  python streamlit_runner.py --dry-run --auto-reload   # 测试命令(不执行)

文件变更检测选项:
  --auto-reload    启用文件变更时自动重载应用 (--server.runOnSave)
  --watcher        文件监视器类型: auto, watchdog, poll, none (默认: auto)
  --port           指定服务器端口 (默认: 8501)
  --headless       无头模式运行，不打开浏览器
  --dry-run        仅显示命令而不执行 (用于测试)
        """,
    )

    parser.add_argument(
        "--auto-reload",
        action="store_true",
        help="启用文件变更时自动重载应用 (--server.runOnSave)",
    )

    parser.add_argument(
        "--watcher",
        choices=["auto", "watchdog", "poll", "none"],
        default="auto",
        help="文件监视器类型 (默认: auto)",
    )

    parser.add_argument("--port", type=int, help="服务器端口 (默认: 8501)")

    parser.add_argument(
        "--headless", action="store_true", help="无头模式运行，不打开浏览器"
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="仅显示命令而不执行 (用于测试)"
    )

    args = parser.parse_args()

    # Run streamlit with options
    run_streamlit(
        run_on_save=args.auto_reload,
        file_watcher_type=args.watcher,
        server_port=args.port,
        headless=args.headless,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
