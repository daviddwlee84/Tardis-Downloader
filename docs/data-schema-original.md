# Data Schema

https://docs.tardis.dev/downloadable-csv-files#data-types

## incremental_book_L2

| Column Name     | Description                                                                                                                                       |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| exchange        | exchange id, one of https://api.tardis.dev/v1/exchanges (`[].id` field)                                                                           |
| symbol          | instrument symbol as provided by exchange (always uppercase)                                                                                      |
| timestamp       | timestamp provided by exchange in microseconds since epoch - if exchange does not provide one `local_timestamp` value is used as a fallback       |
| local_timestamp | message arrival timestamp in microseconds since epoch                                                                                             |
| is_snapshot     | possible values: `true` - if update was a part of initial order book snapshot, `false` - if update was not a part of initial order book snapshot  |
| side            | determines to which side of the order book update belongs to: `bid` - bid side of the book, buy orders; `ask` - ask side of the book, sell orders |
| price           | price identifying book level being updated                                                                                                        |
| amount          | updated price level amount as provided by exchange, not a delta - an amount of `0` indicates that the price level can be removed                  |

## book_snapshot_25

| Column Name     | Description                                                                                                                                 |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| exchange        | exchange id, one of https://api.tardis.dev/v1/exchanges (`[].id` field)                                                                     |
| symbol          | instrument symbol as provided by exchange (always uppercase)                                                                                |
| timestamp       | timestamp provided by exchange in microseconds since epoch - if exchange does not provide one `local_timestamp` value is used as a fallback |
| local_timestamp | message arrival timestamp in microseconds since epoch                                                                                       |
| asks            | JSON array of ask price levels, each level is an array of `[price, amount]`                                                                 |
| bids            | JSON array of bid price levels, each level is an array of `[price, amount]`                                                                 |

## book_snapshot_5

| Column Name     | Description                                                                                                                                 |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| exchange        | exchange id, one of https://api.tardis.dev/v1/exchanges (`[].id` field)                                                                     |
| symbol          | instrument symbol as provided by exchange (always uppercase)                                                                                |
| timestamp       | timestamp provided by exchange in microseconds since epoch - if exchange does not provide one `local_timestamp` value is used as a fallback |
| local_timestamp | message arrival timestamp in microseconds since epoch                                                                                       |
| asks            | JSON array of ask price levels, each level is an array of `[price, amount]`                                                                 |
| bids            | JSON array of bid price levels, each level is an array of `[price, amount]`                                                                 |

## trades

| Column Name     | Description                                                                                                                                 |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| exchange        | exchange id, one of https://api.tardis.dev/v1/exchanges (`[].id` field)                                                                     |
| symbol          | instrument symbol as provided by exchange (always uppercase)                                                                                |
| timestamp       | timestamp provided by exchange in microseconds since epoch - if exchange does not provide one `local_timestamp` value is used as a fallback |
| local_timestamp | message arrival timestamp in microseconds since epoch                                                                                       |
| id              | unique trade identifier as provided by exchange                                                                                             |
| side            | trade side: `buy` or `sell`                                                                                                                 |
| price           | trade price                                                                                                                                 |
| amount          | trade amount                                                                                                                                |

## options_chain

| Column Name      | Description                                                                                                                                 |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| exchange         | exchange id, one of https://api.tardis.dev/v1/exchanges (`[].id` field)                                                                     |
| symbol           | instrument symbol as provided by exchange (always uppercase)                                                                                |
| timestamp        | timestamp provided by exchange in microseconds since epoch - if exchange does not provide one `local_timestamp` value is used as a fallback |
| local_timestamp  | message arrival timestamp in microseconds since epoch                                                                                       |
| option_symbol    | option contract symbol                                                                                                                      |
| option_type      | option type: `call` or `put`                                                                                                                |
| strike_price     | option strike price                                                                                                                         |
| expiration_date  | option expiration date in YYYY-MM-DD format                                                                                                 |
| underlying_price | underlying asset price at the time of snapshot                                                                                              |
| bid_price        | best bid price for the option                                                                                                               |
| bid_amount       | best bid amount for the option                                                                                                              |
| ask_price        | best ask price for the option                                                                                                               |
| ask_amount       | best ask amount for the option                                                                                                              |

## quotes

| Column Name     | Description                                                                                                                                 |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| exchange        | exchange id, one of https://api.tardis.dev/v1/exchanges (`[].id` field)                                                                     |
| symbol          | instrument symbol as provided by exchange (always uppercase)                                                                                |
| timestamp       | timestamp provided by exchange in microseconds since epoch - if exchange does not provide one `local_timestamp` value is used as a fallback |
| local_timestamp | message arrival timestamp in microseconds since epoch                                                                                       |
| bid_price       | best bid price                                                                                                                              |
| bid_amount      | best bid amount                                                                                                                             |
| ask_price       | best ask price                                                                                                                              |
| ask_amount      | best ask amount                                                                                                                             |

## derivative_ticker

| Column Name            | Description                                                                                                                                 |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| exchange               | exchange id, one of https://api.tardis.dev/v1/exchanges (`[].id` field)                                                                     |
| symbol                 | instrument symbol as provided by exchange (always uppercase)                                                                                |
| timestamp              | timestamp provided by exchange in microseconds since epoch - if exchange does not provide one `local_timestamp` value is used as a fallback |
| local_timestamp        | message arrival timestamp in microseconds since epoch                                                                                       |
| open                   | opening price                                                                                                                               |
| high                   | highest price                                                                                                                               |
| low                    | lowest price                                                                                                                                |
| close                  | closing price                                                                                                                               |
| volume                 | trading volume                                                                                                                              |
| funding_rate           | current funding rate (for perpetual contracts)                                                                                              |
| predicted_funding_rate | predicted funding rate (for perpetual contracts)                                                                                            |

## liquidations

| Column Name     | Description                                                                                                                                 |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| exchange        | exchange id, one of https://api.tardis.dev/v1/exchanges (`[].id` field)                                                                     |
| symbol          | instrument symbol as provided by exchange (always uppercase)                                                                                |
| timestamp       | timestamp provided by exchange in microseconds since epoch - if exchange does not provide one `local_timestamp` value is used as a fallback |
| local_timestamp | message arrival timestamp in microseconds since epoch                                                                                       |
| side            | liquidation side: `buy` (long position liquidated) or `sell` (short position liquidated)                                                    |
| price           | liquidation price                                                                                                                           |
| amount          | liquidated position amount                                                                                                                  |
