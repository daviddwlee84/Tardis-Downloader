# https://docs.tardis.dev/downloadable-csv-files#quick-start
# pip install tardis-dev
# requires Python >=3.6
from tardis_dev import datasets
from dotenv import load_dotenv, find_dotenv
import os

_ = load_dotenv(find_dotenv())

datasets.download(
    exchange="deribit",
    data_types=[
        "incremental_book_L2",
        "trades",
        "quotes",
        "derivative_ticker",
        "book_snapshot_25",
        "liquidations",
    ],
    from_date="2019-11-01",
    to_date="2019-11-02",
    symbols=["BTC-PERPETUAL", "ETH-PERPETUAL"],
    api_key=os.getenv("TARDIS_API_KEY"),
)
