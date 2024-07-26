from pydantic import (
    AnyHttpUrl,
    BaseModel,
    Field,
    NonNegativeFloat,
    NonNegativeInt,
    PositiveInt,
    StrictBool,
    StrictStr,
    field_validator,
)
from textual.constants import DEVTOOLS_HOST, DEVTOOLS_PORT
from urllib3.util import Retry as UrllibRetry

from luz_metronomo.default import Default
from luz_metronomo.entity.datetime_format import DatetimeFormat
from luz_metronomo.entity.textual_theme import TextualTheme
from luz_metronomo.util.enum import name_to_enum


class DevelopmentServer(BaseModel):
    enable: StrictBool = Field(
        default=False,
        description="""
        Whether to enable connecting Textual to the development server (i.e. “console”).
        The development server may be provided by a different package, which must be installed prior to enabling this option.
    """,
    )
    host: StrictStr = Field(
        default=DEVTOOLS_HOST,
        description="""
        Hostname on which the development server is running.
    """,
    )
    port: PositiveInt = Field(
        default=DEVTOOLS_PORT,
        description="""
        Port on which the development server is running.
    """,
    )


# FIXME: Document.
class LuzMetronomo(BaseModel):
    development_server: DevelopmentServer = Field(
        default_factory=DevelopmentServer, alias="development-server"
    )


# FIXME: Document.
class UserInterface(BaseModel):
    dark_theme: StrictStr | None = Field(
        default=None,
        alias="dark-theme",
        description="""
        Theme to apply when dark mode is enabled.
    """,
    )
    light_theme: StrictStr | None = Field(
        default=None,
        alias="light-theme",
        description="""
        Theme to apply when dark mode is disabled.
    """,
    )
    use_dark_theme: StrictBool | None = Field(
        default=None,
        alias="use-dark-theme",
        description="""
        Whether to enable the dark theme.
    """,
    )

    # FIXME: Validator.
    plot_marker: StrictStr | None = Field(
        default="braille",
        alias="plot-marker",
    )

    # FIXME: Validator.
    # https://github.com/Textualize/textual-plotext/commit/be2d422f3494f0e88a9c725f9ec831031e97d6f0#diff-874f33563125619a7a5cb567ebe523c59258662d69858d78d24d947b275f9c6c
    light_plot_theme: StrictStr | None = Field(
        default=None,
        alias="light-plot-theme",
    )

    # FIXME: Validator.
    # https://github.com/Textualize/textual-plotext/commit/be2d422f3494f0e88a9c725f9ec831031e97d6f0#diff-874f33563125619a7a5cb567ebe523c59258662d69858d78d24d947b275f9c6c
    dark_plot_theme: StrictStr | None = Field(
        default=None,
        alias="dark-plot-theme",
    )

    @field_validator("dark_theme", "light_theme")
    @classmethod
    def validate_theme(cls, value: str | TextualTheme) -> TextualTheme:
        if isinstance(value, str):
            return name_to_enum(value, TextualTheme, case_insensitive=True)
        return value


class Backoff(BaseModel):
    factor: NonNegativeFloat = Field(
        default=1.0,
        description="""
        A backoff factor to apply between attempts after the second try.
        Formula: {backoff factor} * (2 ** ({number of previous retries})).
        Disable with a value of `0.0`.
    """,
    )
    max: NonNegativeFloat = Field(
        default=0.0,
        description="""
        Amount of seconds not to exceed when waiting between retries (with backoff).
        Disable with a value of `0.0`.
    """,
    )
    jitter: NonNegativeFloat = Field(
        default=1.0,
        description="""
        Amount of seconds that will be the upper range for random jitter applied to pauses between retries (with backoff).
        Formula: random.uniform(0, {backoff jitter})
        Disable with a value of `0.0`.
    """,
    )


class Retry(BaseModel):
    backoff: Backoff = Backoff()
    redirect: NonNegativeInt = Field(
        default=3,
        description="""
        Maximum amount of HTTP redirections to follow, if any.
        A redirection is a HTTP (server) response with status code 301, 302, 303, 307 or 308.
        Set to `0` to avoid following any redirection, and fail instantly.
    """,
    )
    total: NonNegativeInt | None = Field(
        default=3,
        description="""
        Total amount of retries to allow, regardless of their type.
        Takes precedence over the other counts.
        Set to `0` to fail instantly.
        Set to `None` (or remove from configuration completely) to take into account the other, more granular, retry counts.
    """,
    )
    connect: NonNegativeInt = Field(
        default=0,
        description="""
        Amount of connection failures to retry on.
        Ignored if the `total` count is set.
        Set to `0` to fail instantly.
    """,
    )
    read: NonNegativeInt = Field(
        default=0,
        description="""
        Amount of read failures to retry on.
        Ignored if the `total` count is set.
        Set to `0` to fail instantly.
    """,
    )
    status: NonNegativeInt = Field(
        default=3,
        description="""
        Amount of status failures (in `status-forcelist`) to retry on.
        Ignored if the `total` count is set.
        Set to `0` to fail instantly.
    """,
    )
    other: NonNegativeInt = Field(
        default=0,
        description="""
        Amount of other types of failures to retry on.
        Ignored if the `total` count is set.
        Set to `0` to fail instantly.
    """,
    )
    # TODO: Determine behaviour on empty list.
    allowed_methods: list[str] | None = Field(
        default=UrllibRetry.DEFAULT_ALLOWED_METHODS,
        alias="allowed-methods",
        description="""
        List of HTTP method names that are considered idempotent (i.e. may be retried safely).
        Set to `None` to retry any HTTP request.
    """,
    )
    status_forcelist: list[int] = Field(
        default_factory=list,
        alias="status-forcelist",
        description="""
        Force retrying upon failure if the method matches `allowed-methods` and the status is in this list.
        Set to the empty list to ignore the status.
    """,
    )


class Timeout(BaseModel):
    total: NonNegativeFloat | None = Field(
        default=3.0,
        description="""
        Maximum amount of time (in seconds) after which a request that has been initiated will be considered timed out.
        Takes precedence over the other durations.
        Set to `None` (or remove from configuration completely) to take into account the other, more granular, retry counts.
    """,
    )
    connect: NonNegativeFloat = Field(
        default=0.0,
        description="""
        Maximum amount of time (in seconds) to wait for a connection attempt to a server to succeed.
        Set to `0.0` to prevent a connection attempt from being considered timed out.
    """,
    )
    read: NonNegativeFloat = Field(
        default=0.0,
        description="""
        Maximum amount of time (in seconds) to wait for a response from a server connected to.
        Set to `0.0` to prevent an established connection without response from being considered timed out.
    """,
    )


# FIXME: Document.
class Api(BaseModel):
    # TODO: Customise request methods, parameters, formats…
    url: AnyHttpUrl = Field(
        default=AnyHttpUrl(Default.URL_API),
    )
    retry: Retry = Retry()
    timeout: Timeout = Timeout()
    datetime_format: DatetimeFormat = Field(
        default=DatetimeFormat.Iso,
    )

    # FIXME: field_validator for `datetime_format`


class Configuration(BaseModel):
    luz_metronomo: LuzMetronomo = Field(default_factory=LuzMetronomo, alias="luz-metronomo")
    user_interface: UserInterface = Field(default_factory=UserInterface, alias="user-interface")
    api: Api = Field(default_factory=Api)
