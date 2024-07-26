import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import urllib3
from urllib3.exceptions import (
    HTTPError,
    LocationValueError,
    NewConnectionError,
    ProtocolError,
    RequestError,
    TimeoutError,
)
from urllib3.response import BaseHTTPResponse
from urllib3.util import Retry, Timeout

from luz_metronomo.default import Default
from luz_metronomo.util.timezone import GMT_PLUS_2

logger = logging.getLogger(Default.PROGRAM_NAME)


def normalise_datetime_field(datetime: datetime) -> str:
    """
    Set the given datetime into the Spanish timezone, and remove microsecond, timezone
    information.
    """
    return datetime.astimezone(GMT_PLUS_2).replace(microsecond=0, tzinfo=None).isoformat()


class ApiError(Exception): ...


# TODO: Document.
@dataclass
class Api:
    url: str
    retry: Retry | None = None
    timeout: Timeout | None = None

    def __post_init__(self):
        if self.retry is None:
            self.retry = Retry()
        if self.timeout is None:
            self.timeout = Timeout()

    def get(self, date_from: datetime, date_to: datetime) -> dict[str, Any]:
        try:
            # NOTE: The endpoint only supports YYYY-MM-DDT00:00:00, GMT+2 without
            # timezone information in the string
            start_date_spain: str = normalise_datetime_field(date_from)
            end_date_spain: str = normalise_datetime_field(date_to)
            fields: dict[str, Any] = {
                "start_date": start_date_spain,
                "end_date": end_date_spain,
                "time_trunc": "hour",
            }
            logger.debug("Api request: %s (fields: %s)", self.url, fields)
            http_response: BaseHTTPResponse = urllib3.request(
                "GET", self.url, retries=self.retry, timeout=self.timeout, fields=fields
            )
        except (
            HTTPError,
            TimeoutError,
            LocationValueError,
            RequestError,
            NewConnectionError,
            ProtocolError,
        ) as e:
            raise ApiError from e

        text_response: str = http_response.data.decode("utf-8")

        logger.debug("Response from the API: %s", text_response)

        try:
            json_response: dict[str, Any] = json.loads(text_response)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ApiError from e

        # TODO: Use a validation schema
        if not json_response:
            raise ApiError("Invalid JSON response")

        return json_response
