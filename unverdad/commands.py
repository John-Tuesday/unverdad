import argparse
import logging
import subprocess
import sys
from typing import override

from unverdad import config
from unverdad.config import user_config

logger = logging.getLogger(__name__)

from unverdad import subcommands
from unverdad.subcommands import subcommand


class ClearLogSubCmd(subcommand.SubCommand):
    """Clear log file."""

    @override
    def attach(self, subparsers) -> argparse.ArgumentParser:
        p = subparsers.add_parser("clear-log", help="clear log and exit")
        p.set_defaults(log_mode="w", hook=lambda _: logger.info("log cleared"))
        return p


def parse_args(
    root_logger: logging.Logger = logging.getLogger(),
    subcommands: list[subcommand.SubCommand] = [
        ClearLogSubCmd(),
        *subcommands.as_list(),
    ],
):
    """Parse args to configure and perform user chosen actions.

    Creates, configures, and runs an argparse.ArgumentParser.
    According to the parsed arguments, configure logging and run associated
    hook functions.
    """
    parser = argparse.ArgumentParser(
        prog=config.APP_NAME,
        description="manage mods for Guilty Gear Strive",
    )
    parser.set_defaults(log_mode="a", out_lvl=logging.INFO)
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        "-v",
        "--verbose",
        help="detailed output",
        action="store_const",
        const=logging.DEBUG,
        dest="out_lvl",
    )
    verbosity_group.add_argument(
        "-q",
        "--quiet",
        help="silent output",
        action="store_const",
        const=logging.ERROR,
        dest="out_lvl",
    )
    subparsers = parser.add_subparsers(
        title="subcommands",
        description="control mod installation",
        required=True,
    )
    for subcmd in subcommands:
        p = subcmd.attach(subparsers)
        p.set_defaults(hook=subcmd.hook)
    args = parser.parse_args()

    # init logger handles
    console_h = logging.StreamHandler(sys.stdout)
    console_h.setLevel(args.out_lvl)
    console_h.setFormatter(logging.Formatter())
    root_logger.addHandler(console_h)
    file_h = logging.FileHandler(filename=config.LOG_FILE, mode=args.log_mode)
    file_h.setLevel(logging.DEBUG)
    file_h.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
    root_logger.addHandler(file_h)

    args.config = user_config.load_config()
    args.hook(args)
