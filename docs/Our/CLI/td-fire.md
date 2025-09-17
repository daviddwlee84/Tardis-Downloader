# td-fire

- [src/tardis_data_downloader/cli/fire_download_wrapper.py](../../../src/tardis_data_downloader/cli/fire_download_wrapper.py)

```bash
$ td-fire list-exchanges
常見支持的交易所:
  - deribit
  - binance
  - binance-futures
  - binance-delivery
  - bitmex
  - bybit
  - okex
  - huobi
  - kraken
  - ftx
```

```bash
$ td-fire get-exchange-details deribit
獲取 deribit 交易所詳情...

交易所詳情:
名稱: Deribit
ID: deribit
可用數據類型: 
可用交易對數量: 271932

前 10 個可用交易對:
  - {'id': 'BTC-PERPETUAL', 'type': 'perpetual', 'availableSince': '2019-03-30T00:00:00.000Z'}
  - {'id': 'BTC_USDC-PERPETUAL', 'type': 'perpetual', 'availableSince': '2022-03-09T00:00:00.000Z'}
  - {'id': 'ETH-PERPETUAL', 'type': 'perpetual', 'availableSince': '2019-03-30T00:00:00.000Z'}
  - {'id': 'ETH_USDC-PERPETUAL', 'type': 'perpetual', 'availableSince': '2022-03-14T00:00:00.000Z'}
  - {'id': 'BNB_USDC-PERPETUAL', 'type': 'perpetual', 'availableSince': '2024-09-17T00:00:00.000Z'}
  - {'id': 'LTC_USDC-PERPETUAL', 'type': 'perpetual', 'availableSince': '2022-04-28T00:00:00.000Z'}
  - {'id': 'SOL_USDC-PERPETUAL', 'type': 'perpetual', 'availableSince': '2022-03-15T00:00:00.000Z'}
  - {'id': 'BCH_USDC-PERPETUAL', 'type': 'perpetual', 'availableSince': '2022-04-28T00:00:00.000Z'}
  - {'id': 'XRP_USDC-PERPETUAL', 'type': 'perpetual', 'availableSince': '2022-03-16T00:00:00.000Z'}
  - {'id': 'AVAX_USDC-PERPETUAL', 'type': 'perpetual', 'availableSince': '2022-03-17T00:00:00.000Z'}
```


```bash
$ td-fire download 'deribit' 'trades' 'BTC-PERPETUAL' '2023-01-01' '2023-01-01' --concurrency 1
開始下載數據...
交易所: deribit
數據類型: trades
交易對: BTC-PERPETUAL
日期範圍: 2023-01-01 到 2023-01-01
格式: csv
下載目錄: ./datasets

下載完成！

$ ipython
In [1]: import pandas as pd

In [2]: pd.read_csv("datasets/deribit_trades_2023-01-01_BTC-PERPETUAL.csv.gz")
Out[2]: 
     exchange         symbol         timestamp   local_timestamp         id  side    price  amount
0     deribit  BTC-PERPETUAL  1672531205853000  1672531205861103  238463900   buy  16532.0      50
1     deribit  BTC-PERPETUAL  1672531205949000  1672531205969686  238463901  sell  16531.5      50
2     deribit  BTC-PERPETUAL  1672531325378000  1672531325389000  238463936  sell  16531.5    1680
3     deribit  BTC-PERPETUAL  1672531325378000  1672531325389000  238463937  sell  16531.5    1610
4     deribit  BTC-PERPETUAL  1672531326565000  1672531326574550  238463938   buy  16532.0   29610
...       ...            ...               ...               ...        ...   ...      ...     ...
8446  deribit  BTC-PERPETUAL  1672617486492000  1672617486501833  238477552  sell  16616.5     450
8447  deribit  BTC-PERPETUAL  1672617486492000  1672617486501833  238477553  sell  16616.5    4100
8448  deribit  BTC-PERPETUAL  1672617486493000  1672617486501853  238477554  sell  16616.5    7830
8449  deribit  BTC-PERPETUAL  1672617486493000  1672617486501853  238477555  sell  16616.5      10
8450  deribit  BTC-PERPETUAL  1672617486493000  1672617486501853  238477556  sell  16616.5      10

[8451 rows x 8 columns]
```

- [google/python-fire: Python Fire is a library for automatically generating command line interfaces (CLIs) from absolutely any Python object.](https://github.com/google/python-fire)
