import argparse
import logging

from unverdad import config

logger = logging.getLogger(__name__)


def attach(subparsers) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "config",
        help="interact with current config",
        description="query config values",
    )
    arg_group = parser.add_mutually_exclusive_group()
    arg_group.add_argument(
        "-l",
        "--list-all",
        help="list all config key-value pairs",
        action="store_true",
    )
    arg_group.add_argument(
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
    if args.keys:
        logger.info("[config] get by keys")
        value = config.SCHEMA.format_export(config.SETTINGS, keys=args.keys)
        print(value)
    elif args.list_all or not args.keys:
        logger.info("[config] list all config options")
        print(config.SETTINGS)
