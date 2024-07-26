from typing import Any

from urllib3.util import Retry as UrllibRetry
from urllib3.util import Timeout as UrllibTimeout

from luz_metronomo.configuration import Retry, Timeout


def retry_object(retry: Retry) -> UrllibRetry:
    parameters: dict[str, Any] = {}

    if retry.backoff.factor > 0.0:
        parameters["backoff_factor"] = retry.backoff.factor
        if retry.backoff.max > 0.0:
            parameters["backoff_max"] = retry.backoff.max
        if retry.backoff.jitter > 0.0:
            parameters["backoff_jitter"] = retry.backoff.jitter

    parameters["redirect"] = retry.redirect

    if retry.total is not None:
        parameters["total"] = retry.total
    else:
        parameters["connect"] = retry.connect
        parameters["read"] = retry.read
        parameters["status"] = retry.status
        parameters["other"] = retry.other
        parameters["allowed_methods"] = retry.allowed_methods
        if retry.status_forcelist:
            parameters["status_forcelist"] = retry.status_forcelist

    return UrllibRetry(**parameters)


def timeout_object(timeout: Timeout) -> UrllibTimeout:
    parameters: dict[str, Any] = {}

    if timeout.total is not None:
        parameters["total"] = timeout.total
    else:
        parameters["connect"] = timeout.connect
        parameters["read"] = timeout.read
    return UrllibTimeout(**parameters)
