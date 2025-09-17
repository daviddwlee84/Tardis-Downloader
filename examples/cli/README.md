# Tardis CLI 範例

這個目錄包含使用 `td-fire` 命令行工具的範例。

## 安裝

確保你已經安裝了 tardis-data-downloader：

```bash
pip install -e .
```

## 基本使用

### 1. 顯示幫助信息

```bash
td-fire --help
```

### 2. 獲取交易所詳情

```bash
# 獲取 Deribit 交易所的可用數據類型和交易對
td-fire get-exchange-details 'deribit'

# 獲取 Binance 交易所詳情
td-fire get-exchange-details 'binance'
```

### 3. 列出支持的交易所

```bash
td-fire list-exchanges
```

### 4. 下載數據

基本的數據下載命令格式：

```bash
td-fire download EXCHANGE DATA_TYPES SYMBOLS FROM_DATE TO_DATE [選項]
```

#### 範例：下載 Deribit BTC 永續合約數據

```bash
# 下載交易和 L2 增量訂單簿數據
td-fire download 'deribit' 'trades,incremental_book_L2' 'BTC-PERPETUAL' '2023-01-01' '2023-01-02'
```

#### 範例：下載多個交易對

```bash
# 下載 BTC 和 ETH 永續合約
td-fire download 'deribit' 'trades' 'BTC-PERPETUAL,ETH-PERPETUAL' '2023-01-01' '2023-01-02'
```

#### 範例：下載更長時間範圍的數據

```bash
# 下載一個月的數據
td-fire download 'binance-futures' 'trades,book_snapshot_5' 'BTCUSDT' '2023-01-01' '2023-02-01'
```

#### 範例：使用自定義選項

```bash
# 指定下載目錄和並發數量
td-fire download 'deribit' 'trades' 'BTC-PERPETUAL' '2023-01-01' '2023-01-02' \
  --download_dir './my_data' \
  --concurrency 10 \
  --format 'csv'
```

## 錯誤排除

### 常見錯誤

1. **缺少必需參數**
   ```
   ERROR: The function received no value for the required argument: data_types
   ```
   解決方案：確保提供所有必需參數（exchange, data_types, symbols, from_date, to_date）

2. **無效的交易所名稱**
   ```
   獲取交易所詳情失敗: 404 Client Error
   ```
   解決方案：使用 `td-fire list-exchanges` 查看支持的交易所

3. **日期格式錯誤**
   確保使用 ISO 格式：`YYYY-MM-DD`

### 數據類型說明

常見的數據類型：
- `trades` - 交易數據
- `incremental_book_L2` - L2 增量訂單簿
- `quotes` - 報價數據
- `book_snapshot_25` - 25 層訂單簿快照
- `derivative_ticker` - 衍生品行情
- `liquidations` - 清算數據

### API 金鑰

如果需要更高級的功能，可以設置 TARDIS API 金鑰：

```bash
export TARDIS_API_KEY="your_api_key_here"
```

或者在命令中直接指定：

```bash
td-fire download 'deribit' 'trades' 'BTC-PERPETUAL' '2023-01-01' '2023-01-02' --api_key 'your_api_key'
```

## 腳本範例

查看 `scripts/` 目錄中的自動化腳本範例。
