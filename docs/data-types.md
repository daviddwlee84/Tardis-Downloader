# Data Type

https://docs.tardis.dev/faq/data#what-data-types-do-you-support
https://docs.tardis.dev/downloadable-csv-files#data-types

## What data types do you support?

We provide the most comprehensive and granular market data on the market [sourced from real-time WebSocket APIs](https://docs.tardis.dev/faq/data#why-data-source-matters-and-why-we-use-real-time-websocket-feeds-as-data-source-vs-periodically-calling-rest-endpoints) with complete [control and transparency](https://docs.tardis.dev/historical-data-details#market-data-collection-overview) how the data is being recorded.

Via [downloadable CSV data files](https://docs.tardis.dev/downloadable-csv-files) following normalized **tick-level** data types are available:

- [trades](https://docs.tardis.dev/downloadable-csv-files#trades)
- [incremental order book L2 updates](https://docs.tardis.dev/downloadable-csv-files#incremental_book_l2)
- [order book snapshots](https://docs.tardis.dev/downloadable-csv-files#book_snapshot_25) (top 25 and top 5 levels)
- [options_chain](https://docs.tardis.dev/downloadable-csv-files#options_chain)
- [quotes](https://docs.tardis.dev/downloadable-csv-files#quotes)
- [derivative tick info](https://docs.tardis.dev/downloadable-csv-files#derivative_ticker) (open interest, funding rate, mark price, index price)
- [liquidations](https://docs.tardis.dev/downloadable-csv-files#liquidations)

---

[Raw data API](https://docs.tardis.dev/api/getting-started) that is **available for** [**pro and business**](https://docs.tardis.dev/faq/billing-and-subscriptions#what-are-the-differences-between-subscriptions-types) **subscriptions** provides data in [exchange-native data format](https://docs.tardis.dev/faq/data#what-is-a-difference-between-exchange-native-and-normalized-data-format). See [historical data details](https://docs.tardis.dev/historical-data-details) to learn about [real-time channels](https://docs.tardis.dev/faq/data#what-is-the-channel-field-used-in-the-http-api-and-client-libs-replay-functions) captured for each exchange. Each captured channel can be considered a different exchange specific data type (for example [Binance bookTicker channel](https://docs.tardis.dev/historical-data-details/binance#captured-real-time-channels), or [BitMEX liquidation channel](https://docs.tardis.dev/historical-data-details/bitmex#captured-real-time-channels)).

We also provide following [normalized data types](https://docs.tardis.dev/faq/data#what-is-a-difference-between-exchange-native-and-normalized-data-format) via our [client libs](https://docs.tardis.dev/api/getting-started) (normalization is done client-side, using [raw data API](https://docs.tardis.dev/api/getting-started) as a data source):

- trades
- order book L2 updates
- order book snapshots (tick-by-tick, 10ms, 100ms, 1s, 10s etc)
- quotes
- derivative tick info (open interest, funding rate, mark price, index price)
- liquidations
- options summary
- OHLCV
- volume/tick based trade bars
