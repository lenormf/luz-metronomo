from enum import Enum
from typing import Any


def name_to_enum(
    the_name: str,
    enum_class: type[Enum],
    default: Any | None = None,
    case_insensitive: bool = False,
) -> Any:
    """
    Convert a string used as an enum name in an enumeration into the associated typed
    enum.

    Example: name_to_enum("One", Numbers) == Numbers.One
    """

    def name_predicate(the_name: str, name: str, case_insensitive: bool) -> Any:
        if case_insensitive:
            return the_name.lower() == name.lower()
        return the_name == name

    return next(
        (
            value
            for name, value in enum_class.__members__.items()
            if name_predicate(the_name, name, case_insensitive)
        ),
        default,
    )
