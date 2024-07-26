from dataclasses import dataclass
from datetime import datetime

from luz_metronomo.entity.price_point import PricePoint


@dataclass
class PriceList:
    title: str
    last_update: datetime
    price_points: list[PricePoint]
