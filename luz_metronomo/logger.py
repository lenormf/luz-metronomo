import logging
from logging import FileHandler, Formatter, Handler, StreamHandler
from pathlib import Path
from typing import Optional


# NOTE: Mypy doesn’t support this inheritance construct
class Logger(logging.getLoggerClass()):  # type: ignore
    def __init__(self, name: str, level: int, path_log_file: Optional[Path] = None):
        super().__init__(name, level)

        self.path_log_file = path_log_file
        logging_handler: Optional[Handler] = None
        if self.path_log_file:
            logging_handler = FileHandler(self.path_log_file)
        else:
            logging_handler = StreamHandler()
        logging_formatter = Formatter("[%(asctime)s][%(levelname)s]: %(message)s")
        logging_handler.setFormatter(logging_formatter)
        self.addHandler(logging_handler)

        # NOTE: Register the logger into the `logging` internal queue
        global_logger = logging.getLogger(name)
        global_logger.setLevel(level)
        global_logger.addHandler(logging_handler)
