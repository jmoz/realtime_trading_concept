import logging
import re
from datetime import datetime, timezone

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
        # Initialise the bar with opening timestamp and open which is last close. Other fields are updated constantly.
        if trade.symbol not in self.data:
            self.data[trade.symbol] = Candle(
                self.current_open,
                self.context.candles[trade.symbol][-1].close,  # open of new bar is previous close
                trade.price,
                trade.price,
                trade.price,
                0,
            )

        # The core code to constantly update a candle
        self.data[trade.symbol].high = max(trade.price, self.data[trade.symbol].high)
        self.data[trade.symbol].low = min(trade.price, self.data[trade.symbol].low)
        self.data[trade.symbol].close = trade.price
        self.data[trade.symbol].volume = sum([trade.amount, self.data[trade.symbol].volume])

    async def __call__(self, trade, receipt_timestamp: float):
        latency = receipt_timestamp - trade.timestamp
        logger.debug(f'Latency {latency * 1000:.0f}ms')

        trade_dt = datetime.fromtimestamp(trade.timestamp, timezone.utc)
        receipt_dt = datetime.fromtimestamp(receipt_timestamp, timezone.utc)
        this_open = get_open_dt(self.timeframe, trade_dt)

        if self.current_open is None:
            self.current_open = this_open

        # on new bar open
        if this_open > self.current_open:
            for symbol in self.data.keys():
                try:
                    self.context.candles[symbol].append(self.data[symbol])
                except KeyError:
                    # no candle for time period
                    pass

            self.current_open = this_open
            self.data = {}

            # call handler with candles, symbol, timestamp
            await self.handler(self.context.candles, trade_dt, receipt_dt)

        self._agg(trade)


def get_open_dt(timeframe, trade_dt):
    m = re.match('(\d+)([mhd])', timeframe)
    if m:
        num = int(m.group(1))
        base = m.group(2)
    else:
        raise ValueError(f"Invalid timeframe {timeframe}, use 1m, 2h, 3d etc")

    replace_params = {'second': 0, 'microsecond': 0}

    if timeframe == '1m':
        pass
    elif base == 'm':
        replace_params.update({'minute': trade_dt.minute // num * num})
    elif timeframe == '1h':
        replace_params.update({'minute': 0})
    elif base == 'h':
        replace_params.update({'hour': trade_dt.hour // num * num, 'minute': 0})
    elif timeframe == '1d':
        replace_params.update({'hour': 0, 'minute': 0})

    this_open = trade_dt.replace(**replace_params).timestamp()

    return this_open


class Context:
    def __init__(self, handler, context):
        self.handler = handler
        self.context = context

    async def __call__(self, data, receipt_timestamp):
        await self.handler(data, receipt_timestamp, self.context)
