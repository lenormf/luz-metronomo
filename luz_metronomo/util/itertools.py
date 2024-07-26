from typing import Any, Iterable


def first(haystack: Iterable, default: Any | None = None) -> Any:
    return next(iter(haystack), default)
