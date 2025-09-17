#!/bin/bash

# 批量下載多個交易對的數據
# 用法: ./batch_download.sh [開始日期] [結束日期]

set -e

# 預設日期範圍
START_DATE=${1:-"2023-01-01"}
END_DATE=${2:-"2023-01-02"}

# Deribit 主要永續合約
SYMBOLS="BTC-PERPETUAL,ETH-PERPETUAL"

# 要下載的數據類型
DATA_TYPES="trades,incremental_book_L2,book_snapshot_25"

echo "批量下載 Deribit 數據..."
echo "交易對: $SYMBOLS"
echo "數據類型: $DATA_TYPES"
echo "日期範圍: $START_DATE 到 $END_DATE"
echo

# 創建下載目錄
DOWNLOAD_DIR="./batch_data"
mkdir -p "$DOWNLOAD_DIR"

echo "開始下載..."

# 下載所有數據
td-fire download 'deribit' "$DATA_TYPES" "$SYMBOLS" "$START_DATE" "$END_DATE" \
  --download_dir "$DOWNLOAD_DIR" \
  --concurrency 3

echo
echo "批量下載完成！"
echo "數據保存在: $DOWNLOAD_DIR"

# 顯示下載的文件
echo
echo "下載的文件列表:"
find "$DOWNLOAD_DIR" -name "*.gz" | head -10
