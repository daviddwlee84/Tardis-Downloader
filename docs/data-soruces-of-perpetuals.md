# Data Source/Exchange (of Perpetuals)

https://docs.tardis.dev/faq/billing-and-subscriptions#what-is-included-in-perpetuals-data-plan

## **What is included in "Perpetuals" data plan?**

"Perpetuals" data plan provides access to the following perpetual swaps instruments' market data (over 500 perpetual swaps instruments across 13 exchanges):

- [BitMEX](https://docs.tardis.dev/historical-data-details/bitmex): all perpetual swaps instruments
- [Deribit](https://docs.tardis.dev/historical-data-details/deribit)**:** all perpetual swaps instruments
- [Binance USDT Futures](https://docs.tardis.dev/historical-data-details/binance-futures): all perpetual swaps instruments
- [Binance COIN Futures](https://docs.tardis.dev/historical-data-details/binance-delivery): all perpetual swaps instruments
- [FTX](https://docs.tardis.dev/historical-data-details/ftx): all perpetual swaps instruments
- [OKX Swap](https://docs.tardis.dev/historical-data-details/okex-swap): all perpetual swaps instruments
- [Huobi COIN Swaps](https://docs.tardis.dev/historical-data-details/huobi-dm-swap): all perpetual swaps instruments
- [Huobi USDT Swaps](https://docs.tardis.dev/historical-data-details/huobi-dm-linear-swap): all perpetual swaps instruments
- [bitFlyer](https://docs.tardis.dev/historical-data-details/bitflyer): FX_BTC_JPY
- [Bitfinex Derivatives](https://docs.tardis.dev/historical-data-details/bitfinex-derivatives): all perpetual swaps instruments
- [Bybit](https://docs.tardis.dev/historical-data-details/bybit): all perpetual swaps instruments
- [dYdX](https://docs.tardis.dev/historical-data-details/dydx): all perpetual swaps instruments
- [Phemex](https://docs.tardis.dev/historical-data-details/phemex): all perpetual swaps instruments
- [Delta](https://docs.tardis.dev/historical-data-details/delta): all perpetual swaps instruments
- [Gate.io Futures](https://docs.tardis.dev/historical-data-details/gate-io-futures): all perpetual swaps instruments
- [CoinFLEX](https://docs.tardis.dev/historical-data-details/coinflex): all perpetual swaps instruments
- [dYdX](https://docs.tardis.dev/historical-data-details/dydx): all perpetual swaps instruments
- [WOO X](https://docs.tardis.dev/historical-data-details/woo-x): all perpetual swaps instruments
- [Ascendex](https://docs.tardis.dev/historical-data-details/ascendex): all perpetual swaps instruments
- [Crypto.com](https://docs.tardis.dev/historical-data-details/crypto-com): all perpetual swaps instruments

"Perpetuals" data plan allows access to [**all available data types**](https://docs.tardis.dev/faq/data#what-data-types-do-you-support) (trades, orders book data, funding etc.) via [downloadable CSV files](https://docs.tardis.dev/downloadable-csv-files) and [raw data replay API](https://docs.tardis.dev/api/getting-started) (for pro and business subscriptions types). Range of historical data access for "Perpetuals" data plan depends on [chosen billing period](https://docs.tardis.dev/faq/billing-and-subscriptions#do-subscriptions-include-access-to-historical-data-as-well) (for example: access to **all existing historical data** we collected if subscription is **billed yearly**).

"Perpetuals" data plan is available both for [subscriptions](https://docs.tardis.dev/faq/billing-and-subscriptions#how-subscription-based-access-works) and [one-off purchases](https://docs.tardis.dev/faq/billing-and-subscriptions#how-one-off-purchase-based-access-works).

---

## What L2 order book data can be used for?

L2 data (market-by-price) includes bids and asks orders aggregated by price level and can be used to analyze among other things:

- order book imbalance
- average execution cost
- average liquidity away from midpoint
- average spread
- hidden interest (i.e., iceberg orders)

We do provide L2 data both in [CSV format as incremental order book L2 updates](https://docs.tardis.dev/downloadable-csv-files#incremental_book_l2), [tick level order book snapshots](https://docs.tardis.dev/downloadable-csv-files#book_snapshot_25) (top 25 and top 5 levels) as well as in [exchange-native](https://docs.tardis.dev/faq/data#what-is-a-difference-between-exchange-native-and-normalized-data-format) format via [API and client libraries that can perform full order book reconstruction](https://docs.tardis.dev/api/getting-started) client-side.

## What L3 order book data can be used for?

L3 data (market-by-order) includes every order book order addition, update, cancellation and match and can be used to analyze among other things:

- order resting time
- order fill probability
- order queue dynamics

Historical L3 data is currently available via API for [Bitfinex](https://docs.tardis.dev/historical-data-details/bitfinex), [Coinbase Pro](https://docs.tardis.dev/historical-data-details/coinbase) and [Bitstamp](https://docs.tardis.dev/historical-data-details/bitstamp) - remaining supported exchanges provide [L2 data](https://docs.tardis.dev/faq/data#what-l2-order-book-data-can-be-used-for) only.
