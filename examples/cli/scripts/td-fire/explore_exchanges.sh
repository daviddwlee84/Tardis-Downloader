#!/bin/bash

# 探索交易所詳情
# 用法: ./explore_exchanges.sh

set -e

echo "探索支持的交易所..."

# 列出所有交易所
echo "支持的交易所列表："
td-fire list-exchanges
echo

# 探索幾個主要交易所
exchanges=("deribit" "binance" "binance-futures" "bitmex")

for exchange in "${exchanges[@]}"; do
    echo "========================================"
    echo "探索 $exchange 交易所"
    echo "========================================"

    if td-fire get-exchange-details "$exchange" 2>/dev/null; then
        echo "✓ $exchange 詳情獲取成功"
    else
        echo "✗ $exchange 詳情獲取失敗"
    fi

    echo
    sleep 1  # 避免請求過於頻繁
done

echo "探索完成！"
