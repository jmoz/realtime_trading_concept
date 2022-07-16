from dataclasses import dataclass, field


@dataclass
class Context:
    markets: list = field(default_factory=list)
