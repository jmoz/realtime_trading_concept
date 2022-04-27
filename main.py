import asyncio
import logging

from cryptofeed import FeedHandler
from cryptofeed.defines import TRADES

from callbacks import TimescaleDb
from exchange import MyFTX
from models import Context

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def initialise_context():
    logger.debug('Initialise start')
    ex = MyFTX(config='config.yaml')

    context = Context()
    markets = await ex.fetch_markets()
    perps = [m for m in markets if m['name'].endswith('PERP')]
    # lib confusingly changes symbol names ETH-PERP to ETH-USD-PERP and for spot ETH/USD to ETH-USD
    context.markets = [f"{p['name'].split('-')[0]}-USD-PERP" for p in perps]
    logger.info(f'Loaded markets: {context.markets}')
    return context


async def main():
    context = await initialise_context()  # load all the markets into context var

    f = FeedHandler(config="config.yaml")
    f.add_feed(
        MyFTX(config="config.yaml", symbols=context.markets, channels=[TRADES], callbacks={TRADES: TimescaleDb()}))
    f.run(start_loop=False)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
