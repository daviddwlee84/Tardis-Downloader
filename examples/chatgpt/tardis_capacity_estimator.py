#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import csv
import dataclasses as dc
import json
import math
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Dict, Tuple, Optional
from urllib.parse import urlencode, quote

import aiohttp

API_BASE = "https://api.tardis.dev/v1"
DATASETS_BASE = "https://datasets.tardis.dev/v1"

# Unauthorized. Please set the 'Authorization' header with the following format: 'Bearer YOUR_API_KEY' and if you provided one already, please double check if you pasted the API key in full and without any typos. Instruments metadata API is available only for active "pro" and "business" subscriptions.

# ---- Helpers -----------------------------------------------------------------


def daterange(d1: str, d2: str, step_days: int = 1) -> List[date]:
    start = datetime.fromisoformat(d1).date()
    end = datetime.fromisoformat(d2).date()
    days = []
    d = start
    while d <= end:
        days.append(d)
        d += timedelta(days=step_days)
    return days


def human_bytes(n: int) -> str:
    if n is None:
        return "-"
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    x = float(n)
    while x >= 1024 and i < len(units) - 1:
        x /= 1024.0
        i += 1
    return f"{x:.2f} {units[i]}"


# ---- CLI config ---------------------------------------------------------------


@dc.dataclass
class Args:
    # 交易所：預設是最常用的四家 + Deribit
    exchanges: List[str] = dc.field(
        default_factory=lambda: [
            "binance-futures",
            "binance-delivery",
            "okex-swap",
            "bybit",
            "deribit",
        ]
    )
    # 資料型別：預設不含 L2（高性價比）
    data_types: List[str] = dc.field(
        default_factory=lambda: [
            "trades",
            "quotes",
            "derivative_ticker",
            "liquidations",
        ]
    )
    # 也可以加上 L2 與 snapshots（體積大）
    include_l2: bool = False  # 若 True 會附加 incremental_book_L2
    include_snapshots_25: bool = False  # 若 True 會附加 book_snapshot_25

    # 日期區間（含端點）
    from_date: str = "2023-01-01"
    to_date: str = "2023-01-07"

    # 只取活躍 perpetuals
    active_only: bool = True

    # 只抽樣每 N 日（如 7 表示每 7 天抽 1 天）; 1 表示全檢 (精準)
    sample_step: int = 1

    # 只估前 K 個最活躍符號（0=不限）。可先設 0；或設 20 做快速估算。
    top_k_symbols: int = 0

    # 併發度
    concurrency: int = 64
    timeout_sec: int = 30

    # 輸出
    out_dir: str = "tardis_capacity_out"  # 內含 manifest.csv 與 report.json


# ---- Core --------------------------------------------------------------------


async def fetch_perp_symbols(
    session: aiohttp.ClientSession, exchange: str, api_key: str, active_only: bool
) -> List[str]:
    """Call instruments API to get perpetual symbols for an exchange."""
    flt = {"type": "perpetual"}
    if active_only:
        flt["active"] = True
    query = urlencode({"filter": json.dumps(flt)})
    url = f"{API_BASE}/instruments/{exchange}?{query}"
    headers = {"Authorization": f"Bearer {api_key}"}
    async with session.get(url, headers=headers) as r:
        r.raise_for_status()
        data = await r.json()
    # response items contain 'symbol' field in Tardis canonical form
    symbols = [it["symbol"] for it in data]
    return symbols


def build_dataset_url(exchange: str, data_type: str, day: date, symbol: str) -> str:
    yyyy = f"{day.year:04d}"
    mm = f"{day.month:02d}"
    dd = f"{day.day:02d}"
    # symbol 需原樣（已是 Tardis 格式）；URL 需轉義
    sym = quote(symbol, safe="")
    return f"{DATASETS_BASE}/{exchange}/{data_type}/{yyyy}/{mm}/{dd}/{sym}.csv.gz"


async def head_content_length(
    session: aiohttp.ClientSession, url: str
) -> Tuple[bool, Optional[int]]:
    """HEAD to get Content-Length; fall back to GET Range for servers not supporting HEAD."""
    try:
        async with session.head(url) as r:
            if r.status == 200:
                cl = r.headers.get("Content-Length")
                return True, int(cl) if cl is not None else None
            elif r.status == 404:
                return False, None
            else:
                # Some servers may not support HEAD well; fall back
                pass
    except Exception:
        pass

    # Fallback: GET first byte to read headers (still cheap)
    try:
        async with session.get(url, headers={"Range": "bytes=0-0"}) as r:
            if r.status in (200, 206):
                cl = r.headers.get("Content-Length")
                return True, int(cl) if cl is not None else None
            elif r.status == 404:
                return False, None
            else:
                return False, None
    except Exception:
        return False, None


async def estimate_sizes(args: Args) -> None:
    api_key = os.environ.get("TARDIS_API_KEY")
    if not api_key:
        raise SystemExit("ERROR: Please export TARDIS_API_KEY.")

    # expand data types
    data_types = list(args.data_types)
    if args.include_l2 and "incremental_book_L2" not in data_types:
        data_types.append("incremental_book_L2")
    if args.include_snapshots_25 and "book_snapshot_25" not in data_types:
        data_types.append("book_snapshot_25")

    days_all = daterange(args.from_date, args.to_date)
    days = (
        days_all
        if args.sample_step <= 1
        else daterange(args.from_date, args.to_date, args.sample_step)
    )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.csv"
    report_path = out_dir / "report.json"

    timeout = aiohttp.ClientTimeout(total=args.timeout_sec)
    connector = aiohttp.TCPConnector(limit=args.concurrency)

    auth_header = {"Authorization": f"Bearer {api_key}"}

    summary: Dict[str, Dict[str, int]] = {}  # exchange -> data_type -> bytes
    total_checked = 0
    total_exists = 0

    # Prepare CSV
    with manifest_path.open("w", newline="") as fcsv:
        w = csv.writer(fcsv)
        w.writerow(
            ["exchange", "data_type", "symbol", "date", "url", "exists", "size_bytes"]
        )

        async with aiohttp.ClientSession(
            timeout=timeout, connector=connector
        ) as session:
            # 1) get perpetural symbols per exchange
            exch2symbols: Dict[str, List[str]] = {}
            for exch in args.exchanges:
                try:
                    syms = await fetch_perp_symbols(
                        session, exch, api_key, args.active_only
                    )
                    syms.sort()
                    if args.top_k_symbols and len(syms) > args.top_k_symbols:
                        syms = syms[: args.top_k_symbols]
                    exch2symbols[exch] = syms
                    print(f"[{exch}] symbols: {len(syms)}")
                except Exception as e:
                    print(f"[WARN] fail get symbols for {exch}: {e}")
                    exch2symbols[exch] = []

            # 2) schedule HEAD tasks
            sem = asyncio.Semaphore(args.concurrency)

            async def probe(exch: str, dt: str, sym: str, d: date):
                nonlocal total_checked, total_exists
                url = build_dataset_url(exch, dt, d, sym)
                async with sem:
                    exists, size = await head_content_length(session, url)
                total_checked += 1
                if exists:
                    total_exists += 1
                    summary.setdefault(exch, {}).setdefault(dt, 0)
                    summary[exch][dt] += size or 0
                w.writerow([exch, dt, sym, d.isoformat(), url, int(exists), size or ""])
                return exists, size

            tasks = []
            for exch, syms in exch2symbols.items():
                for dt in data_types:
                    for sym in syms:
                        for d in days:
                            tasks.append(asyncio.create_task(probe(exch, dt, sym, d)))

            batch = 0
            for fut in asyncio.as_completed(tasks):
                await fut
                batch += 1
                if batch % 500 == 0:
                    print(f"Probed {batch}/{len(tasks)} files...")

    # 3) if sampling: scale to full range
    scale = 1.0
    if args.sample_step > 1:
        full_days = len(days_all)
        sampled_days = len(days)
        scale = full_days / sampled_days
        for exch in summary:
            for dt in summary[exch]:
                summary[exch][dt] = int(summary[exch][dt] * scale)

    # 4) write report
    grand_total = sum(v for exch in summary.values() for v in exch.values())
    report = {
        "from_date": args.from_date,
        "to_date": args.to_date,
        "exchanges": args.exchanges,
        "data_types": data_types,
        "active_only": args.active_only,
        "top_k_symbols": args.top_k_symbols,
        "sample_step": args.sample_step,
        "scale_applied": scale,
        "files_checked": total_checked,
        "files_existing_count": total_exists,
        "totals_bytes_by_exchange_dataType": summary,
        "grand_total_bytes": grand_total,
        "grand_total_human": human_bytes(grand_total),
    }
    report_path.write_text(json.dumps(report, indent=2))
    print("\n=== Capacity Estimation (compressed .csv.gz) ===")
    for exch, mp in summary.items():
        line = " + ".join([f"{dt}:{human_bytes(sz)}" for dt, sz in mp.items()])
        print(f"{exch:18s} -> {line}  | subtotal={human_bytes(sum(mp.values()))}")
    print(
        f"\nGrand Total ≈ {human_bytes(grand_total)} "
        f"(sample_step={args.sample_step}, scaled x{scale:.2f})"
    )
    print(f"\nManifest: {manifest_path}")
    print(f"Report:   {report_path}")


# ---- Entrypoint --------------------------------------------------------------


def parse_args() -> Args:
    # 無第三方 CLI 依賴；用環境變數或直接改預設值即可。
    import argparse, ast

    p = argparse.ArgumentParser(
        description="Estimate Tardis CSV storage & emit manifest."
    )
    p.add_argument(
        "--exchanges",
        type=str,
        default=",".join(Args().exchanges),
        help="Comma-separated exchanges (e.g. binance-futures,okex-swap,bybit,deribit)",
    )
    p.add_argument(
        "--data-types",
        type=str,
        default=",".join(Args().data_types),
        help="Comma-separated data types",
    )
    p.add_argument("--include-l2", action="store_true")
    p.add_argument("--include-snapshots-25", action="store_true")
    p.add_argument("--from-date", type=str, default=Args().from_date)
    p.add_argument("--to-date", type=str, default=Args().to_date)
    p.add_argument("--active-only", type=lambda s: s.lower() != "false", default=True)
    p.add_argument("--sample-step", type=int, default=1)
    p.add_argument("--top-k-symbols", type=int, default=0)
    p.add_argument("--concurrency", type=int, default=64)
    p.add_argument("--timeout-sec", type=int, default=30)
    p.add_argument("--out-dir", type=str, default=Args().out_dir)
    a = p.parse_args()

    return Args(
        exchanges=[s for s in a.exchanges.split(",") if s],
        data_types=[s for s in a.data_types.split(",") if s],
        include_l2=a.include_l2,
        include_snapshots_25=a.include_snapshots_25,
        from_date=a.from_date,
        to_date=a.to_date,
        active_only=a.active_only,
        sample_step=a.sample_step,
        top_k_symbols=a.top_k_symbols,
        concurrency=a.concurrency,
        timeout_sec=a.timeout_sec,
        out_dir=a.out_dir,
    )


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(estimate_sizes(args))
