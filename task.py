import asyncio
import logging
import os
from datetime import datetime

import psycopg
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Add 3 second wait as when ran on local machine it missed by 1 second
scheduler = AsyncIOScheduler(timezone=utc, job_defaults={'misfire_grace_time': 3})


@scheduler.scheduled_job("cron", minute='*/5')
async def min_run():
    logger.info(f'Task start {datetime.now()}')
    async with await psycopg.AsyncConnection.connect(
            f"dbname={os.getenv('DB_NAME')} "
            f"host={os.getenv('DB_HOST')} "
            f"user={os.getenv('DB_USER')} "
            f"password={os.getenv('DB_PASS')}", autocommit=True) as aconn:
        logger.info(f'Task async connected {datetime.now()}')

        async with aconn.cursor() as acur:
            await acur.execute(
                "SELECT * FROM candles_1m "
                "WHERE bucket > NOW() - INTERVAL '1 hour' AND bucket < date_trunc('second', now()) "
                "ORDER BY bucket",
            )
            logger.info(f'Task query executed {datetime.now()}')
            result = await acur.fetchall()
            logger.info(f'Task results fetched {datetime.now()}')
        print(result[-10:])


if __name__ == '__main__':
    scheduler.start()
    asyncio.get_event_loop().run_forever()
