import importlib
import logging
from datetime import date, datetime, time
from logging import Logger
from math import floor

from rich.terminal_theme import TerminalTheme
from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Grid, VerticalScroll
from textual.logging import TextualHandler
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    TabbedContent,
    TabPane,
)
from textual.widgets.data_table import ColumnKey
from textual.worker import get_current_worker
from textual_plotext import PlotextPlot

from luz_metronomo.configuration import Configuration, DevelopmentServer
from luz_metronomo.default import Default
from luz_metronomo.entity.price_list import PriceList
from luz_metronomo.util.api import find_price_point_by_datetime, get_price_lists
from luz_metronomo.util.itertools import first
from luz_metronomo.util.textual import textual_theme_enum_to_object
from luz_metronomo.util.timezone import GMT_PLUS_2

logger = logging.getLogger(Default.PROGRAM_NAME)


class PriceListGraph(PlotextPlot):
    def __init__(
        self,
        price_list: PriceList,
        plot_marker: str,
        line_colour: tuple[int, int, int],
        light_plot_theme: str | None,
        dark_plot_theme: str | None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._price_list: PriceList = price_list
        self._plot_marker: str = plot_marker
        self._line_colour: tuple[int, int, int] = line_colour
        if light_plot_theme is not None:
            self.light_mode_theme = light_plot_theme
        if dark_plot_theme is not None:
            self.dark_mode_theme = dark_plot_theme

    def _redraw_with_rulers(self, now: datetime):
        self._redraw()
        time_str: str = now.strftime("%H:%M")
        if (price_point_now := find_price_point_by_datetime(self._price_list, now)) is None:
            logger.warning("Unable to find price point for date: %s", now)
        else:
            self.plt.hline(floor(price_point_now.value), self._line_colour)
            # FIXME: Draw an additional line that indicates the lower time range
            self.plt.vline(time_str, self._line_colour)
            self.refresh()

    def _redraw(self):
        self.plt.date_form("H:M")
        last_update: str = self._price_list.last_update.strftime("%c")
        self.plt.title(f"Rates as of: {last_update}")
        self.plt.clear_data()
        times: list[str] = [
            price_point.datetime.strftime("%H:%M") for price_point in self._price_list.price_points
        ]
        price_points: list[float] = [
            price_point.value for price_point in self._price_list.price_points
        ]
        self.plt.plot(times, price_points, marker=self._plot_marker)
        self.plt.xticks(times)
        self.plt.yticks(set(floor(price_point) for price_point in price_points))

    def on_mount(self):
        now: datetime = datetime.now(GMT_PLUS_2)
        now_date: date = now.date()
        if (
            first(
                True
                for price_point in self._price_list.price_points
                if price_point.datetime.date() == now_date
            )
            is not None
        ):
            self._redraw_with_rulers(now)
            # FIXME: This should be moved to the PriceListPane as a general `highlight_current_time`
            self.set_interval(
                60.0,
                callback=lambda: self._redraw_with_rulers(datetime.now(GMT_PLUS_2)),
                name="redraw_with_rulers",
            )
        else:
            self._redraw()
        self.refresh()


class PriceListPane(Widget):
    BINDINGS = [
        ("p", "sort_rates_by('period')", "Sort rates by period"),
        ("P", "sort_rates_by('period', True)", "Sort (reverse) rates by period"),
        ("t", "sort_rates_by('time')", "Sort rates by time"),
        ("T", "sort_rates_by('time', True)", "Sort (reverse) rates by time"),
        ("r", "sort_rates_by('rate')", "Sort rates by value"),
        ("R", "sort_rates_by('rate', True)", "Sort (reverse) rates by value"),
    ]

    @classmethod
    def datetime_to_peak_hour_text(cls, datetime: datetime) -> Text:
        # NOTE: The API only uses hours for time ranges, and assume the range
        # begins at the full hour
        # E.g. 08:00 matches the documented low and mid ranges, but assume the
        # low range ends at 07:59 and the mid range starts at 08:00
        hora_valle: tuple[Text, list[tuple[time, time]]] = (
            Text("valle", "green"),
            [
                # 00:00 to 08:00
                (time(hour=0), time(hour=7, minute=59)),
            ],
        )
        hora_llano: tuple[Text, list[tuple[time, time]]] = (
            Text("llano", "white"),
            [
                # 08:00 to 10:00
                (time(hour=8), time(hour=9, minute=59)),
                # 14:00 to 18:00
                (time(hour=14), time(hour=17, minute=59)),
                # 22:00 to 00:00
                (time(hour=22), time(hour=23, minute=59)),
            ],
        )
        hora_punta: tuple[Text, list[tuple[time, time]]] = (
            Text("punta", "red"),
            [
                # 10:00 to 14:00
                (time(hour=10), time(hour=13, minute=59)),
                # 18:00 to 22:00
                (time(hour=18), time(hour=21, minute=59)),
            ],
        )

        # NOTE: On the weekend, it’s always “valle”.
        if datetime.weekday() in (5, 6):
            return hora_valle[0]

        for text, horas in (hora_valle, hora_llano, hora_punta):
            for hora in horas:
                if hora[0] <= datetime.time() <= hora[1]:
                    return text

        return Text()

    def __init__(
        self,
        configuration: Configuration,
        terminal_theme: TerminalTheme,
        price_list: PriceList,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._configuration: Configuration = configuration
        self._terminal_theme = terminal_theme
        self._price_list = price_list
        self._column_keys = {}

    def on_mount(self):
        table: DataTable = self.query_one(DataTable)
        table.add_columns("period", "time", "rate")
        # FIXME: Highlight row of current time period, update every minute
        table.add_rows(
            (
                PriceListPane.datetime_to_peak_hour_text(price_point.datetime),
                price_point.datetime.strftime("%H:%M"),
                price_point.value,
            )
            for price_point in self._price_list.price_points
        )

    def compose(self) -> ComposeResult:
        yield PriceListGraph(
            price_list=self._price_list,
            plot_marker=self._configuration.user_interface.plot_marker,
            line_colour=(
                self._terminal_theme.foreground_color.red,
                self._terminal_theme.foreground_color.green,
                self._terminal_theme.foreground_color.blue,
            ),
            light_plot_theme=self._configuration.user_interface.light_plot_theme,
            dark_plot_theme=self._configuration.user_interface.dark_plot_theme,
        )
        yield DataTable(cell_padding=2, cursor_type="row", zebra_stripes=True)

    def action_sort_rates_by(self, column_predicate: str, reverse: bool = False):
        table: DataTable = self.query_one(DataTable)
        column_key: ColumnKey | None = first(
            column.key
            for column in table.columns.values()
            if column.label.plain == column_predicate
        )
        if column_key is not None:
            # NOTE: The table doesn’t know how to sort `Text` instances
            table.sort(
                column_key,
                reverse=reverse,
                key=lambda value: value.plain if isinstance(value, Text) else value,
            )
        else:
            logger.warning("Unable to get key for column labelled: %s", column_predicate)


# FIXME: Move?
def datetime_now_as_ymd() -> datetime:
    return datetime.now(GMT_PLUS_2).replace(hour=0, minute=0, second=0, tzinfo=None)


class LuzMetronomoApp(App):
    TITLE = "Luz Metronomo"

    BINDINGS = [
        ("q", "exit", "Exit the programme"),
    ]

    price_lists: reactive[list[PriceList]] = reactive([], layout=True, recompose=True)
    date_from: reactive[datetime] = reactive(datetime_now_as_ymd)

    def __init__(self, configuration: Configuration, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.CSS = (
            importlib.resources.files("luz_metronomo")
            .joinpath("luz_metronomo_app.tcss")
            .read_text()
        )
        self._configuration: Configuration = configuration

        console_config: DevelopmentServer = self._configuration.luz_metronomo.development_server
        if console_config.enable:
            logger.info(
                "Connecting to development server: %s:%s", console_config.host, console_config.port
            )
            try:
                from textual_dev.client import DevtoolsClient
                from textual_dev.redirect_output import StdoutRedirector
            except ImportError:
                logger.warning("Development dependencies are not installed")
            else:
                self.devtools = DevtoolsClient(host=console_config.host, port=console_config.port)
                self._devtools_redirector = StdoutRedirector(self.devtools)
                textual_handler = TextualHandler()
                logger.addHandler(textual_handler)
                # NOTE: Removing the default handler must be done after at least one alternative handler was set
                default_logger: Logger = logger.handlers[0]
                if isinstance(default_logger, logging.StreamHandler):
                    logger.removeHandler(default_logger)
                logger.info("Installed Textual handler for logging")

        if self._configuration.user_interface.dark_theme is not None:
            self.ansi_theme_dark = textual_theme_enum_to_object(
                self._configuration.user_interface.dark_theme
            )
        if self._configuration.user_interface.light_theme is not None:
            self.ansi_theme_light = textual_theme_enum_to_object(
                self._configuration.user_interface.light_theme
            )
        if self._configuration.user_interface.use_dark_theme is not None:
            self.dark = self._configuration.user_interface.use_dark_theme

    # TODO: A checkbox/option to update to the following day at midnight
    def compose(self) -> ComposeResult:
        header_widget = Header(show_clock=True)
        header_widget.icon = "≡"
        yield header_widget
        yield Grid(
            Label("Date:", id="date-picker-label"),
            # FIXME: Validator, suggestor
            Input(
                placeholder=self.date_from.strftime("%Y-%m-%d"),
                restrict=r"[0-9-]*",
                id="date-picker-input",
            ),
            Button("today", id="date-picker-today"),
            Button("ok", variant="primary", id="date-picker-submit"),
            id="date-picker-container",
        )
        with VerticalScroll(id="price-lists-container"):
            with TabbedContent():
                for price_list in self.price_lists:
                    with TabPane(price_list.title):
                        yield PriceListPane(
                            configuration=self._configuration,
                            terminal_theme=self.ansi_theme,
                            price_list=price_list,
                        )
        yield Footer()

    async def watch_date_from(self, date_from: datetime | None):
        if date_from is not None:
            self.get_price_lists(date_from)

    def update_price_lists(self, price_lists: list[PriceList]):
        self.price_lists = price_lists

    def set_price_lists_loading(self, loading: bool):
        self.query_one("#price-lists-container").loading = loading

    @work(exclusive=True, thread=True)
    def get_price_lists(self, date_from: datetime):
        worker = get_current_worker()
        date_to = date_from.replace(hour=23, minute=59, second=0, tzinfo=None)
        self.call_from_thread(self.set_price_lists_loading, True)
        price_lists = list(get_price_lists(self._configuration.api, date_from, date_to))
        if not worker.is_cancelled:
            self.call_from_thread(lambda value: setattr(self, "price_lists", value), price_lists)
        else:
            logger.warning("Worker was cancelled, the price lists will not be updated")
        self.call_from_thread(self.set_price_lists_loading, False)

    @on(Input.Submitted, "#date-picker-input")
    @on(Button.Pressed, "#date-picker-submit")
    def update_date_from_value(self):
        input: Input = self.query_one("#date-picker-input", Input)
        date_now: datetime = datetime.strptime(input.value, "%Y-%m-%d")
        self.date_from = date_now.replace(hour=0, minute=0, second=0, tzinfo=None)

    @on(Button.Pressed, "#date-picker-today")
    def update_date_from_input(self):
        input: Input = self.query_one("#date-picker-input", Input)
        input.value = datetime_now_as_ymd().strftime("%Y-%m-%d")

    def action_exit(self):
        self.exit()
