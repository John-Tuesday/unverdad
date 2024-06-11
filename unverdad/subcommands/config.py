import argparse

from unverdad import config, errors


def attach(subparsers) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "config",
        help="interact with current config",
        description="query config values",
    )
    parser.add_argument(
        "--show-help",
        help="include documentation comments",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    parser.add_argument(
        "--default",
        help="use the default config instead of the loaded one",
        action="store_true",
    )
    arg_group = parser.add_mutually_exclusive_group()
    arg_group.add_argument(
        "-l",
        "--list-all",
        help="list all config values",
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


def hook(args) -> errors.Result[None]:
    show_help = args.keys is None if args.show_help is None else args.show_help
    print(
        config.SCHEMA.format_export(
            namespace=config.SETTINGS if not args.default else None,
            keys=args.keys,
            show_help=show_help,
        )
    )
    return errors.GoodResult()
