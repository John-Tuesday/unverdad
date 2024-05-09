"""Subcommand for imported mods.
"""

import logging

from unverdad import config
from unverdad.data import database, tables

logger = logging.getLogger(__name__)


def attach(subparsers):
    parser = subparsers.add_parser(
        "mod-registry", help="interact with imported, but not installed mods."
    )
    parser.add_argument(
        "--show-all",
        help="Show all mods in registry",
        action="store_true",
        default=True,
    )
    return parser


def __pretty_mod_row(mod_row):
    s = f"enabled" if mod_row["enabled"] else "disabled"

    return f"{mod_row["name"]}\n  | {s}"


def __on_show_all(conf, con):
    """"""
    data = []
    with con:
        for mod_row in con.execute("SELECT * FROM mod"):
            data.append(__pretty_mod_row(mod_row))
    msg = "\n".join(data)
    logger.info(f"{msg}")


def hook(args):
    """"""
    __on_show_all(args.config, con=database.get_db(config.DB_FILE))
