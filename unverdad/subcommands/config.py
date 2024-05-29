import argparse
import logging

from unverdad.config import user_config

logger = logging.getLogger(__name__)


def attach(subparsers) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "config",
        help="interact with current config",
        description="query/set/verify config values",
    )
    g = parser.add_mutually_exclusive_group()
    g.add_argument(
        "-l",
        "--list-all",
        help="list all config key-value pairs",
        action="store_true",
    )
    g.add_argument(
        "-g",
        "--get",
        help="get config value from key",
        action="extend",
        nargs="+",
        dest="keys",
        metavar="KEY",
    )
    return parser


def hook(args):
    logger.info("config")
    if args.keys:
        logger.info("get config value by one or more keys")
        value = user_config.SCHEMA.format_export_keys(args.config, *args.keys)
        logger.info(value)
    elif args.list_all:
        logger.info("list all config options")
        logger.info(f"{args.config}")
