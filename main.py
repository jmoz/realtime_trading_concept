import asyncio
import json
from decimal import Decimal

from cryptofeed import FeedHandler
from cryptofeed.defines import TRADES
from cryptofeed.exchanges import FTX

from callbacks import OnBarOpen
from models import Candle, Context


async def fetch_markets(api, retry_count=1, retry_delay=60):
    data = await api.http_conn.read(f"{api.api}/markets", retry_count=retry_count, retry_delay=retry_delay)
    data = json.loads(data, parse_float=Decimal)['result']
    return data


async def fetch_candles(api, symbol):
    candles = [c async for c in api.candles(symbol)][0]  # uses a generator to request more candles
    return candles


async def init(context):
    print('init start')
    ftx = FTX(config='config.yaml')

    markets = await fetch_markets(ftx)
    markets = [m for m in markets if m['name'].endswith('PERP')]
    for m in markets:
        # lib confusingly changes symbol names ETH-PERP to ETH-USD-PERP and for spot ETH/USD to ETH-USD
        std_market = f"{m['name'].split('-')[0]}-USD-PERP"
        context.markets[std_market] = m

    candles = await asyncio.gather(*[fetch_candles(ftx, m) for m in context.markets])
    for c in candles:
        # map candles by standardised symbol ETH-USD-PERP
        context.candles[c[0].symbol] = list(map(lambda x: Candle(x.timestamp, x.open, x.high, x.low, x.close), c))

    # print(context.markets.keys())
    # print(context.candles.keys())
    print('init end')


async def trade_callback(t, ts, context):
    last = context.candles[t.symbol][-1]
    pc_change = t.price / last.close * 100 - 100
    if pc_change > 1:
        print(f'{t.symbol} {t.price / last.close * 100 - 100:.2f} last {last.close} current {t.price}')


async def open_callback(candles, trade_dt, receipt_dt):
    last = candles['ETH-USD-PERP'][-1]
    print(f'{last.dt()} {last.close}')


async def main():
    # prepare context structure for easy later use
    context = Context()

    await init(context)  # load all the markets and 1m candles into context var

    f = FeedHandler(config="config.yaml")
    # subscribe to all markets on bar open callback
    f.add_feed(FTX(config="config.yaml", symbols=[m for m in context.markets], channels=[TRADES],
                   callbacks={TRADES: OnBarOpen(open_callback, timeframe='1m', context=context)}))
    f.run(start_loop=False)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
