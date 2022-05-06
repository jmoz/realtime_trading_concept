import asyncio
from datetime import datetime

from cryptofeed import FeedHandler
from cryptofeed.defines import TRADES

from callbacks import OnBarOpen
from exchange import MyFTX
from models import Candle, Context


async def initialise(context, timeframe='1m'):
    print('init start')
    ftx = MyFTX(config='config.yaml')

    markets = await ftx.fetch_markets()
    markets = [m for m in markets if m['name'].endswith('PERP')]
    for m in markets:
        # lib confusingly changes symbol names ETH-PERP to ETH-USD-PERP and for spot ETH/USD to ETH-USD
        std_market = f"{m['name'].split('-')[0]}-USD-PERP"
        context.markets[std_market] = m

    candles = await asyncio.gather(*[ftx.fetch_candles(m, timeframe) for m in context.markets])
    for c in candles:
        # map candles by standardised symbol ETH-USD-PERP
        context.candles[c[0].symbol] = list(
            map(lambda x: Candle(x.timestamp, x.open, x.high, x.low, x.close, x.volume), c))
    print('init end')

    print(datetime.utcnow())
    for c in context.candles['ETH-USD-PERP'][-5:]:
        print(f'{c.dt()} {c}')


async def open_callback(candles, trade_dt, receipt_dt):
    last = candles['ETH-USD-PERP'][-1]
    print(f'{last.dt()} o {last.open} h {last.high} l {last.low} c {last.close} v {last.volume}')


async def main():
    context = Context()

    timeframe = '15m'

    await initialise(context, timeframe)  # load all the markets and 1m candles into context var

    f = FeedHandler(config="config.yaml")
    # subscribe to all markets on bar open callback
    f.add_feed(MyFTX(config="config.yaml", symbols=[m for m in context.markets], channels=[TRADES],
                     callbacks={TRADES: OnBarOpen(open_callback, timeframe=timeframe, context=context)}))
    f.run(start_loop=False)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
