import json
from decimal import Decimal

from cryptofeed.exchanges import FTX


class MyFTX(FTX):
    async def fetch_markets(self, retry_count=1, retry_delay=60):
        data = await self.http_conn.read(f"{self.api}/markets", retry_count=retry_count, retry_delay=retry_delay)
        return json.loads(data, parse_float=Decimal)['result']
