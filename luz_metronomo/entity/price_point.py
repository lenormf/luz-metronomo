from dataclasses import dataclass
from datetime import datetime


@dataclass
class PricePoint:
    value: float
    datetime: datetime
