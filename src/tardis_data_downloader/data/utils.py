from datetime import datetime


def default_file_name(
    exchange: str, data_type: str, date: datetime, symbol: str, format: str
):
    return f"{exchange}_{data_type}_{date.strftime('%Y-%m-%d')}_{symbol}.{format}.gz"
