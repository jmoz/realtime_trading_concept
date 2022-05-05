from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Context:
    markets: dict = field(default_factory=dict)
    candles: dict = field(default_factory=dict)


@dataclass
class Candle:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

    def dt(self):
        return datetime.fromtimestamp(self.timestamp, timezone.utc)
