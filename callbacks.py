import logging
import os
from datetime import datetime, timezone

import psycopg

logger = logging.getLogger(__name__)


class TimescaleDb:
    def __init__(self):
        self.aconn = None
        self.counter = 0
        self.ts = 0

    def log_stats(self, trade):
        if logger.getEffectiveLevel() > logging.INFO:
            return

        self.counter += 1
        x, y = divmod(int(trade.timestamp), 60)
        if x != self.ts and y == 0:
            logger.info(f'Processing {self.counter}/m, {self.counter / 60:.0f}/s')
            self.counter = 0
            self.ts = x

    async def __call__(self, trade, receipt_timestamp: float):
        if not self.aconn:
            self.aconn = await psycopg.AsyncConnection.connect(
                f"dbname={os.getenv('DB_NAME')} "
                f"host={os.getenv('DB_HOST')} "
                f"user={os.getenv('DB_USER')} "
                f"password={os.getenv('DB_PASS')}", autocommit=True)
            logger.info('Async connected to postgres')

        async with self.aconn.cursor() as acur:
            await acur.execute(
                "INSERT INTO trades (timestamp, symbol, price, amount) VALUES (%s, %s, %s, %s)",
                (datetime.fromtimestamp(trade.timestamp, timezone.utc),
                 trade.symbol.replace('USD-PERP', 'PERP'),
                 trade.price,
                 trade.amount if trade.side == 'buy' else -trade.amount))

            logger.debug(trade)

        self.log_stats(trade)
