from argparse import ArgumentParser, Namespace

from luz_metronomo.default import Default


class CliOptions(Namespace):
    def __init__(self, args: list[str]):
        parser = ArgumentParser(
            prog=Default.PROGRAM_NAME,
            description=Default.PROGRAM_DESCRIPTION,
        )

        parser.add_argument("-d", "--debug", action="store_true", help="Display debug messages")
        parser.add_argument(
            "-D", "--debug-output", help="Write debug messages to the given file (implies -d)"
        )
        parser.add_argument(
            "-v", "--verbose", action="store_true", help="Display informational messages"
        )
        parser.add_argument("-c", "--configuration", help="Path to the configuration file to load")

        parser.parse_args(args, self)
