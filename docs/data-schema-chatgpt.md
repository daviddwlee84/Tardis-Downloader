# Data Schema (of each [data types](data-types.md))

https://r.jina.ai/https://docs.tardis.dev/downloadable-csv-files#data-types
https://chatgpt.com/share/68ca4fc3-07a4-8012-a8e6-04912cf96e3b

下面把 **Tardis 可下載 CSV** 的各資料型別欄位，整理成容易對照的表格（含通用欄位與各型別專屬欄位）。欄位型別以文件語意推斷為主（時間戳皆為微秒 epoch）。

# 全域檔案屬性（所有資料集通用）

| 屬性             | 值 / 說明                                               |
| ---------------- | ------------------------------------------------------- |
| 壓縮             | gzip（`.csv.gz`）                                       |
| 切割             | 依「天」分檔（以 `local_timestamp` 做日界）             |
| 排序             | 以 `local_timestamp` 升序                               |
| 分隔符           | 逗號 `,`                                                |
| 換行             | `\n` (LF)                                               |
| 小數點           | `.`                                                     |
| 時區             | UTC（所有 `timestamp`/`local_timestamp` 皆以 UTC 微秒） |
| 無資料日         | 仍回傳空的 gzip 檔                                      |
| 時戳補值         | 若交易所未提供 `timestamp`，則以 `local_timestamp` 回填 |
| 取樣可免 API Key | 每月 **1 號** 歷史資料可免 API key 下載                 |

# 通用欄位（多數型別都會出現）

| 欄位              | 型別          | 說明                                                          |
| ----------------- | ------------- | ------------------------------------------------------------- |
| `exchange`        | string        | 交易所 ID（小寫，如 `deribit`）                               |
| `symbol`          | string(UPPER) | 交易所原生商品代碼；CSV API 要求**全大寫**                    |
| `timestamp`       | int64 (µs)    | 交易所訊息時間（微秒 epoch）；缺失時以 `local_timestamp` 代替 |
| `local_timestamp` | int64 (µs)    | **訊息到達時間**（微秒 epoch）                                |

---

# incremental\_book\_L2（逐筆 L2 訂單簿增量）

| 欄位          | 型別              | 說明                                                                                    |
| ------------- | ----------------- | --------------------------------------------------------------------------------------- |
| （通用 4 欄） |                   | 見上                                                                                    |
| `is_snapshot` | boolean           | `true`=屬於「初始快照」的一部分；若上一筆非快照、此筆為快照，**需捨棄既有簿狀態並重建** |
| `side`        | enum(`bid`,`ask`) | 更新屬於買/賣方                                                                         |
| `price`       | decimal           | 被更新的價位                                                                            |
| `amount`      | decimal           | **該價位的絕對量**（非 delta）；`0` 代表該價位應移除                                    |

> 備註：同一訊息可能含多個價階更新，可用 `local_timestamp` 分組以還原同包訊息。

---

# book\_snapshot\_25（Top 25 逐變化快照）

| 欄位                 | 型別       | 說明                       |
| -------------------- | ---------- | -------------------------- |
| （通用 4 欄）        |            |                            |
| `asks[0..24].price`  | decimal\[] | 賣 25 檔 **遞增** 價       |
| `asks[0..24].amount` | decimal\[] | 對應數量；若深度不足則留空 |
| `bids[0..24].price`  | decimal\[] | 買 25 檔 **遞減** 價       |
| `bids[0..24].amount` | decimal\[] | 對應數量；若深度不足則留空 |

> 於 **任一** 前 25 檔改變時記錄一列。

---

# book\_snapshot\_5（Top 5 逐變化快照）

| 欄位                | 型別       | 說明                |
| ------------------- | ---------- | ------------------- |
| （通用 4 欄）       |            |                     |
| `asks[0..4].price`  | decimal\[] | 賣 5 檔 **遞增** 價 |
| `asks[0..4].amount` | decimal\[] |                     |
| `bids[0..4].price`  | decimal\[] | 買 5 檔 **遞減** 價 |
| `bids[0..4].amount` | decimal\[] |                     |

---

# trades（逐筆成交）

| 欄位          | 型別                         | 說明                                  |
| ------------- | ---------------------------- | ------------------------------------- |
| （通用 4 欄） |                              |                                       |
| `id`          | string                       | 交易所提供的成交 ID（數值/GUID/或無） |
| `side`        | enum(`buy`,`sell`,`unknown`) | **主動方**（taker）方向               |
| `price`       | decimal                      | 成交價                                |
| `amount`      | decimal                      | 成交量                                |

---

# options\_chain（選擇權鏈概況）

| 欄位                                  | 型別               | 說明                 |
| ------------------------------------- | ------------------ | -------------------- |
| （通用 4 欄）                         |                    |                      |
| `type`                                | enum(`put`,`call`) | 權種                 |
| `strike_price`                        | decimal            | 履約價               |
| `expiration`                          | int64 (µs)         | 到期日（微秒 epoch） |
| `open_interest`                       | decimal?           | 未平倉量（可能缺）   |
| `last_price`                          | decimal?           | 近一筆成交價         |
| `bid_price` / `bid_amount` / `bid_iv` | decimal?           | 最優買價/量/隱波     |
| `ask_price` / `ask_amount` / `ask_iv` | decimal?           | 最優賣價/量/隱波     |
| `mark_price` / `mark_iv`              | decimal?           | 標記價與其隱波       |
| `underlying_index`                    | string             | 標的指數名稱         |
| `underlying_price`                    | decimal?           | 標的價格             |
| `delta` `gamma` `vega` `theta` `rho`  | decimal?           | 希臘值（可能缺）     |

> 僅對 `OPTIONS` 群組符號提供（單日彙整所有個別權證）。

---

# quotes（Top-of-Book 最優報價，源自 L2 重建）

| 欄位          | 型別     | 說明     |
| ------------- | -------- | -------- |
| （通用 4 欄） |          |          |
| `ask_amount`  | decimal? | 最優賣量 |
| `ask_price`   | decimal? | 最優賣價 |
| `bid_price`   | decimal? | 最優買價 |
| `bid_amount`  | decimal? | 最優買量 |

> 每當最優一檔變動就記錄一次；刻意不直接用各所原生 quote 串流，以維持跨所一致性與即時性。

---

# derivative\_ticker（永續/衍生品 Ticker 統計）

| 欄位                     | 型別        | 說明                     |
| ------------------------ | ----------- | ------------------------ |
| （通用 4 欄）            |             |                          |
| `funding_timestamp`      | int64 (µs)? | **下一次資金費**時間     |
| `funding_rate`           | decimal?    | 將在下一次生效的資金費率 |
| `predicted_funding_rate` | decimal?    | 再下一次的預估資金費率   |
| `open_interest`          | decimal?    | OI                       |
| `last_price`             | decimal?    | 最新價                   |
| `index_price`            | decimal?    | 指數價                   |
| `mark_price`             | decimal?    | 標記價                   |

---

# liquidations（強平）

| 欄位          | 型別               | 說明                                                        |
| ------------- | ------------------ | ----------------------------------------------------------- |
| （通用 4 欄） |                    |                                                             |
| `id`          | string             | 交易所提供的強平 ID（可能缺）                               |
| `side`        | enum(`buy`,`sell`) | `buy`=**空單被強平**（short 被買回）、`sell`=**多單被強平** |
| `price`       | decimal            | 強平價                                                      |
| `amount`      | decimal            | 強平量                                                      |

---

# 群組化符號（便捷下載）

| 群組         | 適用市場 | 適用資料型別                                  |
| ------------ | -------- | --------------------------------------------- |
| `SPOT`       | 現貨     | `trades`                                      |
| `FUTURES`    | 期貨     | `trades`, `liquidations`                      |
| `PERPETUALS` | 永續     | `trades`, `liquidations`, `derivative_ticker` |
| `OPTIONS`    | 選擇權   | `trades`, `quotes`, `options_chain`           |

> 使用群組符號時，單日檔會包含該市場**所有**商品的資料（特別適合 `OPTIONS`）。

---

# Datasets API（路徑參數一覽）

| 參數          | 值 / 範例                                                                                                                   | 說明                                                         |
| ------------- | --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `exchange`    | `deribit`                                                                                                                   | 必須是 `/v1/exchanges` 中 `supportsDatasets:true` 的 `id`    |
| `dataType`    | `incremental_book_L2` / `trades` / `quotes` / `derivative_ticker` / `book_snapshot_25` / `book_snapshot_5` / `liquidations` | 端點支援的資料型別                                           |
| `year`        | `YYYY`                                                                                                                      | 年（四位）                                                   |
| `month`       | `MM`                                                                                                                        | 月（兩位）                                                   |
| `day`         | `DD`                                                                                                                        | 日（兩位）                                                   |
| `symbol`      | 例：`BTC-PERPETUAL`、`BTCUSDT`、`OPTIONS`                                                                                   | **CSV API 要求**：全大寫，且把 `/`、`:` 改為 `-` 以 URL 安全 |
| Authorization | `Bearer YOUR_API_KEY`                                                                                                       | 無 API key 僅能抓每月 1 號樣本日                             |

---

## 小抄（實務備忘）

* **重建簿**：使用 `incremental_book_L2`，遇到 `is_snapshot=true` 先清盤再套入後續增量。
* **只要 Top-N**：直接用 `book_snapshot_25` 或 `book_snapshot_5`（變動即錄）。
* **最佳一檔曲線**：用 `quotes`（由 L2 重建而非各所原生 quote）。
* **資金費/標記價/OI**：看 `derivative_ticker`。
* **逐筆成交**：`trades`。
* **強平事件**：`liquidations`（注意 `side` 的語義）。
* **選擇權全表**：`options_chain`（單日全品種）。
