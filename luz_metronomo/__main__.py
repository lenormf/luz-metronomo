import logging
import sys
from typing import Any

import confight
from pydantic_core import ValidationError
from textual.app import App

from luz_metronomo.cli_options import CliOptions
from luz_metronomo.configuration import Configuration
from luz_metronomo.default import Default
from luz_metronomo.logger import Logger
from luz_metronomo.textual import LuzMetronomoApp

logger = logging.getLogger(Default.PROGRAM_NAME)


def main(av: list[str]) -> int:
    cli_options = CliOptions(av[1:])

    logging_level = logging.WARN
    if cli_options.debug_output or cli_options.debug:
        logging_level = logging.DEBUG
    elif cli_options.verbose:
        logging_level = logging.INFO
    # FIXME: The log file can only be set from CLI
    logger = Logger(Default.PROGRAM_NAME, logging_level, cli_options.debug_output)

    logger.debug("Debug messages enabled")
    logger.debug("Options namespace: %s", cli_options)

    configuration_data: dict[str, Any] | None = None
    try:
        if cli_options.configuration is not None:
            configuration_data = confight.load([cli_options.configuration])
        else:
            configuration_data = confight.load_user_app(
                Default.PROGRAM_NAME, dir_path=Default.PATH_DIR_USER_CONFIG
            )
    except Exception:
        logger.exception(
            "Unable to load the configuration data", extra={"path": cli_options.configuration}
        )
        return 1
    logger.debug("Raw configuration data: %s", configuration_data)

    try:
        configuration = Configuration.validate(configuration_data)
    except ValidationError:
        logger.exception(
            "Unable to load the configuration object", extra={"data": configuration_data}
        )
        return 1
    logger.debug("Configuration: %s", configuration)

    app: App = None
    try:
        app = LuzMetronomoApp(configuration)
        return app.run()
    except KeyboardInterrupt:
        logger.info("Interrupt caught, quitting")
    except Exception:
        logger.exception("An unknown error occurred")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
