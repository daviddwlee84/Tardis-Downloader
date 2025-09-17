#!/bin/bash

# 下載 Deribit BTC 永續合約數據
# 用法: ./download_deribit_btc.sh [開始日期] [結束日期]

set -e

# 預設日期範圍（如果沒有提供參數）
START_DATE=${1:-"2023-01-01"}
END_DATE=${2:-"2023-01-02"}

echo "下載 Deribit BTC 永續合約數據..."
echo "日期範圍: $START_DATE 到 $END_DATE"

# 下載交易數據
echo "下載交易數據..."
td-fire download 'deribit' 'trades' 'BTC-PERPETUAL' "$START_DATE" "$END_DATE"

# 下載 L2 增量訂單簿數據
echo "下載 L2 增量訂單簿數據..."
td-fire download 'deribit' 'incremental_book_L2' 'BTC-PERPETUAL' "$START_DATE" "$END_DATE"

# 下載訂單簿快照
echo "下載 25 層訂單簿快照..."
td-fire download 'deribit' 'book_snapshot_25' 'BTC-PERPETUAL' "$START_DATE" "$END_DATE"

echo "所有數據下載完成！"
