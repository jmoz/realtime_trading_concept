import json
from decimal import Decimal


async def fetch_markets(api, retry_count=1, retry_delay=60):
    data = await api.http_conn.read(f"{api.api}/markets", retry_count=retry_count, retry_delay=retry_delay)
    data = json.loads(data, parse_float=Decimal)['result']
    return data


async def fetch_candles(api, symbol):
    candles = [c async for c in api.candles(symbol)][0]  # uses a generator to request more candles
    return candles
