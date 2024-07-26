from dataclasses import dataclass
from logging import Logger
from typing import Any, Callable, Protocol

from textual.app import ALABASTER, MONOKAI
from textual.notifications import Notification, SeverityLevel
from textual.widget import Widget

from luz_metronomo.textual_theme import TextualTheme


class Notifier(Protocol):
    def notify(
        self,
        message: str | list[str],
        title: str = "",
        severity: SeverityLevel = Notification.severity,
        timeout: int = Notification.timeout,
    ): ...

    def information(
        self, message: str | list[str], title: str = "", timeout: int = Notification.timeout
    ): ...

    def warning(
        self, message: str | list[str], title: str = "", timeout: int = Notification.timeout
    ): ...

    def error(
        self, message: str | list[str], title: str = "", timeout: int = Notification.timeout
    ): ...


# FIXME: Configurable timeouts per severity
@dataclass
class TextualNotifier:
    widget: Widget

    def notify(
        self,
        message: str | list[str],
        title: str = "",
        severity: SeverityLevel = Notification.severity,
        timeout: int = Notification.timeout,
    ):
        the_message: str = message
        if isinstance(message, list):
            the_message = "\n".join(message)
        self.widget.notify(the_message, title=title, severity=severity, timeout=timeout)

    def information(
        self, message: str | list[str], title: str = "", timeout: int = Notification.timeout
    ):
        return self.notify(message, title, "information", timeout)

    def warning(
        self, message: str | list[str], title: str = "", timeout: int = Notification.timeout
    ):
        return self.notify(message, title, "warning", timeout)

    def error(self, message: str | list[str], title: str = "", timeout: int = Notification.timeout):
        return self.notify(message, title, "error", timeout)


class TextualLoggerNotifier(TextualNotifier):
    logger: Logger

    def __init__(self, widget: Widget, logger: Logger):
        super().__init__(widget)
        self.logger = logger

    def _log(
        self,
        message: str | list[str],
        title: str = "",
        severity: SeverityLevel = Notification.severity,
    ):
        the_message: list[str] = []
        if title:
            the_message.append(title)
        if isinstance(message, str):
            the_message.append(message)
        else:
            the_message.extend(message)

        logger_fn: Callable[[str, ...]]
        match severity:
            case "information":
                logger_fn = self.logger.info
            case "warning":
                logger_fn = self.logger.warning
            case "error":
                logger_fn = self.logger.error
            case _:
                raise ValueError(f"Unsupported severity level: {severity}")

        return logger_fn("%s", "\n".join(the_message))

    def notify(
        self,
        message: str | list[str],
        title: str = "",
        severity: SeverityLevel = Notification.severity,
        timeout: int = Notification.timeout,
    ):
        self._log(message, title, severity)
        return super().notify(message, title, severity, timeout)

    def information(
        self, message: str | list[str], title: str = "", timeout: int = Notification.timeout
    ):
        return self.notify(message, title, "information", timeout)

    def warning(
        self, message: str | list[str], title: str = "", timeout: int = Notification.timeout
    ):
        return self.notify(message, title, "warning", timeout)

    def error(self, message: str | list[str], title: str = "", timeout: int = Notification.timeout):
        return self.notify(message, title, "error", timeout)


def textual_theme_enum_to_object(theme: TextualTheme) -> Any:
    match theme:
        case TextualTheme.Monokai:
            return MONOKAI

        case TextualTheme.Alabaster:
            return ALABASTER

    raise ValueError(f"Unsupported theme: {theme.value}")
