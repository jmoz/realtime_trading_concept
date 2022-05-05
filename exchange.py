import json
from decimal import Decimal


async def fetch_markets(api, retry_count=1, retry_delay=60):
    data = await api.http_conn.read(f"{api.api}/markets", retry_count=retry_count, retry_delay=retry_delay)
    data = json.loads(data, parse_float=Decimal)['result']
    return data


async def fetch_candles(api, symbol, interval='1m', retry_count=1, retry_delay=60):
    candles = [c async for c in api.candles(symbol, interval=interval, retry_count=retry_count, retry_delay=retry_delay)][0]  # uses a generator to request more candles
    return candles
