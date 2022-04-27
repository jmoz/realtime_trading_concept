import logging
from datetime import datetime

from cryptofeed.backends.aggregate import AggregateCallback

from models import Candle

logger = logging.getLogger(__name__)


class OnBarOpen(AggregateCallback):
    """Custom callback to execute on tick of bar open"""

    def __init__(self, *args, timeframe='1m', **kwargs):
        self.context = kwargs.pop('context')
        super().__init__(*args, **kwargs)
        self.current_open = None
        self.data = {}
        self.timeframe = timeframe

    def _agg(self, trade):
        # New symbol, create the structure with some price data, highs and lows don't matter
        if trade.symbol not in self.data:
            self.data[trade.symbol] = {self.current_open: Candle(
                self.current_open,
                trade.price,
                trade.price,
                trade.price,
                trade.price,
            )}

        # New open timestamp, create the same as above
        if self.current_open not in self.data[trade.symbol]:
            self.data[trade.symbol][self.current_open] = Candle(
                self.current_open,
                trade.price,
                trade.price,
                trade.price,
                trade.price,
            )

        # The core code to constantly update a candle
        self.data[trade.symbol][self.current_open] = Candle(
            self.current_open,
            self.data[trade.symbol][self.current_open].open,
            max(trade.price, self.data[trade.symbol][self.current_open].high),
            min(trade.price, self.data[trade.symbol][self.current_open].low),
            trade.price,
        )

    async def __call__(self, trade, receipt_timestamp: float):
        latency = receipt_timestamp - trade.timestamp
        logger.debug(f'Latency {latency * 1000:.0f}ms')

        trade_dt = datetime.fromtimestamp(trade.timestamp)
        receipt_dt = datetime.fromtimestamp(receipt_timestamp)
        this_open = trade_dt.replace(second=0, microsecond=0).timestamp()

        if self.current_open is None:
            self.current_open = this_open

        # on new bar open
        if this_open > self.current_open:
            for symbol in self.data:
                try:
                    self.context.candles[symbol].append(self.data[symbol][self.current_open])
                except KeyError:
                    # no candle for time period
                    pass

            self.current_open = this_open

            # call handler with candles, symbol, timestamp
            await self.handler(self.context.candles, trade_dt, receipt_dt)

        self._agg(trade)


class Context:
    def __init__(self, handler, context):
        self.handler = handler
        self.context = context

    async def __call__(self, data, receipt_timestamp):
        await self.handler(data, receipt_timestamp, self.context)
