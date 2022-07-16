# Installation
- timescaledb/postgres


    pip3 install -r requirements.txt

# Design

The purpose of this proof of concept is to check the capabilities and performance of timescaledb TS as a source of truth.

We use the cryptofeed CF library as it has already built the websockets backend and multiple exchange implementations. We add some code for all FTX markets.

CF subscribes to all markets websocket trades on FTX.

Trade ticks are then fed into TS trades hypertable.

TS uses a continuous aggregate to create bucketed candles, 1m, 1h etc.

We have a scheduled service using APScheduler which runs hourly that fetches the aggregated candles from TS and then we would implement our algorithm and api calls after.

# Usage

`python3 main.py`

    INFO:callbacks:Async connected to postgres
    INFO:callbacks:Processing 1185/m, 20/s
    INFO:callbacks:Processing 1706/m, 28/s
    INFO:callbacks:Processing 1786/m, 30/s
    INFO:callbacks:Processing 1758/m, 29/s
    INFO:callbacks:Processing 1992/m, 33/s
    INFO:callbacks:Processing 1761/m, 29/s

`python3 task.py`

    INFO:apscheduler.executors.default:Running job "min_run (trigger: cron[minute='*/5'], next run at: 2022-07-16 07:55:00 UTC)" (scheduled at 2022-07-16 07:50:00+00:00)
    INFO:__main__:Task start 2022-07-16 15:50:00.020036
    INFO:__main__:Task async connected 2022-07-16 15:50:00.105972
    INFO:__main__:Task query executed 2022-07-16 15:50:00.280459
    INFO:__main__:Task results fetched 2022-07-16 15:50:00.371177
    [(datetime.datetime(2022, 7, 16, 7, 49, tzinfo=datetime.timezone.utc), 'CRV-PERP', 1.0961, 1.09705, 1.09605, 1.0965, Decimal('7464.0')), (datetime.datetime(2022, 7, 16, 7, 49, tzinfo=datetime.timezone.utc), 'CRO-PERP', 0.11695, 0.11695, 0.116925, 0.116925, Decimal('3340.0')), (datetime.datetime(2022, 7, 16, 7, 49, tzinfo=datetime.timezone.utc), 'CREAM-PERP', 17.25, 17.25, 17.25, 17.25, Decimal('0.01')), (datetime.datetime(2022, 7, 16, 7, 49, tzinfo=datetime.timezone.utc), 'COMP-PERP', 53.53, 53.57, 53.49, 53.49, Decimal('13.3806')), (datetime.datetime(2022, 7, 16, 7, 49, tzinfo=datetime.timezone.utc), 'CHZ-PERP', 0.105051, 0.105051, 0.104835, 0.104838, Decimal('79410.0')), (datetime.datetime(2022, 7, 16, 7, 49, tzinfo=datetime.timezone.utc), 'CHR-PERP', 0.17255, 0.17255, 0.17255, 0.17255, Decimal('35.0')), (datetime.datetime(2022, 7, 16, 7, 49, tzinfo=datetime.timezone.utc), 'CELO-PERP', 0.8835, 0.8835, 0.8825, 0.883, Decimal('2926.1')), (datetime.datetime(2022, 7, 16, 7, 49, tzinfo=datetime.timezone.utc), 'CEL-PERP', 0.727, 0.729, 0.7265, 0.7285, Decimal('3049.8')), (datetime.datetime(2022, 7, 16, 7, 49, tzinfo=datetime.timezone.utc), 'ZRX-PERP', 0.29225, 0.29225, 0.29225, 0.29225, Decimal('1.0')), (datetime.datetime(2022, 7, 16, 7, 49, tzinfo=datetime.timezone.utc), 'CAKE-PERP', 3.07, 3.07, 3.07, 3.07, Decimal('1.0'))]

We timestamp each step of execution to see where the time is spent.

The task is scheduled to fire every 5 minutes. We can see there is a small delay at the start of the task (.020036s).

The main delay is unsurprisingly from executing and fetching the candle data from TS. There is roughly a half second delay on average (measured by eyeballing previous runs on a M1 Air). This example shows a delay of up to .371177s until data is fetched. This does not include any algorithm logic and api calls which would be additional.

# Conclusion

For saving and aggregating trade tick data into candles TS does its job. The real-time table where some candles are already processed but then the live ticks are combined is also useful.

However the delay from fetching the candles is undesirable. For a medium frequency system running on hourly closes perhaps it is acceptable just for the ease of use it would add.

But there is a core feature missing imho, that I have not seen anyone talking about or any solutions. A trading system will always need candle history to work from. E.g. 200+ bars from the past to calculate averages etc. There is no simple solution to backfill the candle data. Yes you can backfill the trade ticks but this makes no sense as the amount of data would be huge and also difficult to acquire. So you would only have historical aggregated candles from when you started up TS. You would also have the problem of missing data when exchanges go down, which they do often.

So a solution for historical candles but also using real-time ticks is missing. One way would be to periodically in the background request 1m candles from an api and store, then build the current candle in memory, which would also reduce the delay of fetching data. But then this would make TS redundant, for a trading system at least.