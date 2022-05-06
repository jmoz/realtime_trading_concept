import json
from decimal import Decimal

from cryptofeed.exchanges import FTX


class MyFTX(FTX):
    async def fetch_markets(self, retry_count=1, retry_delay=60):
        data = await self.http_conn.read(f"{self.api}/markets", retry_count=retry_count, retry_delay=retry_delay)
        return json.loads(data, parse_float=Decimal)['result']

    async def fetch_candles(self, symbol, interval='1m', retry_count=1, retry_delay=60):
        # uses a generator to request more candles but we want one call/result
        return [c async for c in self.candles(symbol,
                                              interval=interval,
                                              retry_count=retry_count,
                                              retry_delay=retry_delay)][0]
