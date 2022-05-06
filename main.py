import asyncio
import logging
from datetime import datetime

from cryptofeed import FeedHandler
from cryptofeed.defines import TRADES

from callbacks import OnBarOpen
from exchange import MyFTX
from models import Candle, Context

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def initialise(context, timeframe='1m'):
    logger.debug('Initialise start')
    ex = MyFTX(config='config.yaml')

    markets = await ex.fetch_markets()
    perps = [m for m in markets if m['name'].endswith('PERP')]
    # lib confusingly changes symbol names ETH-PERP to ETH-USD-PERP and for spot ETH/USD to ETH-USD
    context.markets = [f"{p['name'].split('-')[0]}-USD-PERP" for p in perps]
    logger.info(f'Loaded markets: {context.markets}')

    candles = await asyncio.gather(*[ex.fetch_candles(m, timeframe) for m in context.markets])
    for c in candles:
        # map candles by standardised symbol ETH-USD-PERP
        context.candles[c[0].symbol] = list(
            map(lambda x: Candle(x.timestamp, x.open, x.high, x.low, x.close, x.volume), c))
    logger.info(f'Loaded candles: {sum(map(len, context.candles.values()))}')
    logger.debug('Initialise end')

    print(datetime.utcnow())
    for c in context.candles['ETH-USD-PERP'][-5:]:
        print(f'{c.dt()} {c}')


async def open_callback(candles, trade_dt, receipt_dt):
    last = candles['ETH-USD-PERP'][-1]
    print(f'{last.dt()} o {last.open} h {last.high} l {last.low} c {last.close} v {last.volume}')


async def main():
    context = Context()
    timeframe = '15m'

    await initialise(context, timeframe)  # load all the markets and candles into context var

    f = FeedHandler(config="config.yaml")
    # subscribe to all markets on bar open callback
    f.add_feed(MyFTX(config="config.yaml", symbols=context.markets, channels=[TRADES],
                     callbacks={TRADES: OnBarOpen(open_callback, timeframe=timeframe, context=context)}))
    f.run(start_loop=False)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
