"""Subcommand for imported mods.
"""

import logging
import uuid

from unverdad import config
from unverdad.data import database, filter_group, tables

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
    parser.add_argument(
        "--mod-id",
        "-m",
        help="Select MOD_ID",
        action="append",
        dest="mod_ids",
        default=[],
    )
    parser.add_argument(
        "--mod-name",
        "-n",
        help="Select NAME of mod",
        action="append",
        dest="mod_names",
        default=[],
    )
    return parser


def __pretty_mod_row(mod_row):
    s = [f"enabled" if mod_row["enabled"] else "disabled"]
    s.append(f"mod id: '{mod_row["mod_id"]}'")
    prefix = "  | "
    s = f"\n{prefix}".join(s)

    return f"{mod_row["name"]}\n{prefix}{s}"


def __on_show_all(conf, con):
    """"""
    data = []
    with con:
        for mod_row in con.execute("SELECT * FROM mod"):
            data.append(__pretty_mod_row(mod_row))
    msg = "\n".join(data)
    logger.info(f"{msg}")


def __on_show(conf, con, filter: filter_group.FilterGroup):
    """"""
    data = []
    with con:
        where_clause = filter.where_clause()
        params = filter.where_params()
        for mod_row in con.execute(f"SELECT * FROM mod {where_clause}", params):
            data.append(__pretty_mod_row(mod_row))
    msg = "\n".join(data)
    logger.info(f"{msg}")


def hook(args):
    """"""
    filter = filter_group.FilterGroup(tables.mod.ModEntity)
    for mod_id in args.mod_ids:
        filter.add_mod_id(uuid.UUID(mod_id))
        logger.debug(f"{filter}")
    logger.debug(f"{filter}")
    for mod_name in args.mod_names:
        filter.add_name(mod_name)
    logger.debug(f"{filter}")
    if filter.is_not_empty():
        __on_show(args.config, con=database.get_db(config.DB_FILE), filter=filter)
    elif args.show_all:
        __on_show_all(args.config, con=database.get_db(config.DB_FILE))
