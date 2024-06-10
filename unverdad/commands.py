import argparse
import logging
import pathlib
import sys
from typing import Optional

from unverdad import config, errors, subcommands


def mkdir_homes():
    """Ensure directory homes exist."""
    for dir in [config.DATA_HOME, config.CONFIG_HOME, config.STATE_HOME]:
        dir.expanduser().resolve().mkdir(parents=True, exist_ok=True)


def init_logging(
    level: int,
    root_logger: Optional[logging.Logger] = None,
    log_file: Optional[pathlib.Path] = None,
) -> None:
    """Initialize logging

    :param `level`: Level for `root_logger`.
    :param `root_logger`: Logger which will be configured; if None, use the root logger.
    :param `log_file`: Path to file in which to output logs. The file will be created
        if it does not exist, and its parent is an existing directory.
    """
    if root_logger is None:
        root_logger = logging.getLogger()
    root_logger.setLevel(level)
    console_h = logging.StreamHandler(sys.stdout)
    console_h.setLevel(level)
    console_h.setFormatter(logging.Formatter())
    root_logger.addHandler(console_h)
    if log_file is None:
        return root_logger.warning(f"Log file is not being used")
    if not log_file.parent.is_dir() or (log_file.exists() and not log_file.is_file()):
        return root_logger.warning(f"Log file cannot be created at '{log_file}'")
    file_h = logging.FileHandler(filename=log_file, mode="a")
    file_h.setLevel(logging.DEBUG)
    file_h.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
    root_logger.addHandler(file_h)


def parse_args(
    root_logger: Optional[logging.Logger] = None,
) -> errors.UnverdadError | None:
    """Parse args to configure and perform user chosen actions.

    Creates, configures, and runs an argparse.ArgumentParser.
    According to the parsed arguments, configure logging and run associated
    hook functions.
    """
    parser = argparse.ArgumentParser(
        prog=config.APP_NAME,
        description="manage mods for Guilty Gear Strive",
    )
    parser.set_defaults(logging_level=logging.WARNING)
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        "-v",
        "--verbose",
        help="detailed output",
        action="store_const",
        const=logging.INFO,
        dest="logging_level",
    )
    verbosity_group.add_argument(
        "--debug",
        help="extremely detailed output",
        action="store_const",
        const=logging.DEBUG,
        dest="logging_level",
    )
    verbosity_group.add_argument(
        "-q",
        "--quiet",
        help="silent output",
        action="store_const",
        const=logging.ERROR,
        dest="logging_level",
    )
    subparsers = parser.add_subparsers(
        title="subcommands",
        description="control mod installation",
        required=True,
    )
    for subcmd in subcommands.as_list():
        p = subcmd.attach(subparsers)
        p.set_defaults(hook=subcmd.hook, subparser=p)
    args = parser.parse_args()
    init_logging(
        level=args.logging_level,
        root_logger=root_logger,
        log_file=config.LOG_FILE,
    )
    return args.hook(args)
