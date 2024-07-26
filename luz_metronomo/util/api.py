import logging
from collections.abc import Iterator
from datetime import datetime
from typing import Any

from urllib3.util import Retry as UrllibRetry
from urllib3.util import Timeout as UrllibTimeout

from luz_metronomo.api import Api, ApiError
from luz_metronomo.configuration import Api as ApiConfig
from luz_metronomo.default import Default
from luz_metronomo.entity.price_list import PriceList
from luz_metronomo.entity.price_point import PricePoint
from luz_metronomo.util.configuration import retry_object, timeout_object

logger = logging.getLogger(Default.PROGRAM_NAME)


# FIXME: Document.
def get_price_lists(
    api_config: ApiConfig, date_from: datetime, date_to: datetime
) -> Iterator[PriceList]:
    retry: UrllibRetry = retry_object(api_config.retry)
    timeout: UrllibTimeout = timeout_object(api_config.timeout)
    try:
        api = Api(url=str(api_config.url), retry=retry, timeout=timeout)
        data: dict[str, Any] = api.get(date_from, date_to)
    except ApiError:
        logger.exception("Could not fetch data", extra={"url": str(api_config.url)})
    else:
        for price_list in data["included"]:
            title: str = price_list["attributes"]["title"]
            last_update: datetime = datetime.fromisoformat(price_list["attributes"]["last-update"])
            the_list = PriceList(
                title=title,
                last_update=last_update,
                price_points=[
                    PricePoint(
                        value=the_value["value"],
                        datetime=datetime.fromisoformat(the_value["datetime"]),
                    )
                    for the_value in sorted(
                        price_list["attributes"]["values"],
                        key=lambda the_value: datetime.fromisoformat(
                            the_value["datetime"]
                        ).timestamp(),
                    )
                ],
            )
            # NOTE: The last item has `00:00` set as a date, like the first one,
            # so we remove it to avoid rendering issues.
            # Ideally, the pruning should be smarter and remove all trailing entries
            # that match earlier HH:MM entries.
            if the_list.price_points and all(
                (
                    the_list.price_points[-1].datetime.hour
                    == the_list.price_points[0].datetime.hour,
                    the_list.price_points[-1].datetime.minute
                    == the_list.price_points[0].datetime.minute,
                )
            ):
                the_list.price_points.pop()
            yield the_list


# FIXME: Document.
def find_price_point_by_datetime(price_list: PriceList, datetime: datetime) -> PricePoint | None:
    datetime_predicate: datetime = datetime.replace(minute=0, second=0, microsecond=0)
    for idx_price_point, price_point in enumerate(price_list.price_points):
        price_point_datetime_predicate: datetime = price_point.datetime.replace(
            minute=0, second=0, microsecond=0
        )
        # NOTE: This function assumes the current interval stops at minute 59,
        # despite the API returning overlapping ranges.
        if price_point_datetime_predicate == datetime_predicate:
            logger.debug(
                "Found price point for dates: %s %s %s",
                price_point,
                datetime_predicate,
                price_point_datetime_predicate,
            )
            return price_point

    return None
