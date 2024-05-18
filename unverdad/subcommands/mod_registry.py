"""Subcommand for imported mods.
"""

import logging
import types
import uuid
from collections import abc
from typing import Optional

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
    parser.add_argument(
        "--game-id",
        help="Only include results for a particular game given its ID",
        action="store",
    )
    parser.add_argument(
        "--game-name",
        help="Only include results for a particular game given its NAME",
        action="store",
    )
    return parser


def __pretty_mod_row(mod_row):
    s = [f"enabled" if mod_row["enabled"] else "disabled"]
    s.append(f"mod id: '{mod_row["mod_id"]}'")
    s.append(f"game_id: '{mod_row["game_id"]}'")
    prefix = "  | "
    s = f"\n{prefix}".join(s)

    return f"{mod_row["name"]}\n{prefix}{s}"


def __on_show(
    conf,
    con,
    filter: filter_group.ConditionBuilder,
):
    """"""
    data = []
    with con:
        sql_clause = filter.render()
        params = filter.params()
        if sql_clause:
            sql_clause = f"WHERE {sql_clause}"
        for mod_row in con.execute(f"SELECT * FROM mod {sql_clause}", params):
            data.append(__pretty_mod_row(mod_row))
    msg = "\n".join(data)
    logger.info(f"{msg}")


def hook(args):
    """"""
    filter = filter_group.ConditionBuilderBranch(or_join=False)
    or_conds = filter.add_subfilter(or_join=True)
    and_conds = filter.add_subfilter(or_join=False)
    for mod_id in args.mod_ids:
        # filter.add_mod_id(uuid.UUID(mod_id))
        or_conds._add_param(column_name="mod_id", column_value=uuid.UUID(mod_id))
    for mod_name in args.mod_names:
        # filter.add_name(mod_name)
        or_conds._add_param(column_name="name", column_value=mod_name)
    if args.game_id:
        # game_id = uuid.UUID(args.game_id)
        and_conds._add_param(
            column_name="game_id", column_value=uuid.UUID(args.game_id)
        )
    if args.game_name:
        db = database.get_db(config.DB_FILE)
        for game_row in db.execute(
            "SELECT * FROM game WHERE name = :name", {"name": args.game_name}
        ):
            game_entity = tables.game.GameEntity(**game_row)
            # game_id = game_entity.game_id
            and_conds._add_param(
                column_name="game_id", column_value=game_entity.game_id
            )
    logger.debug(f"{filter}")
    __on_show(
        conf=args.config,
        con=database.get_db(config.DB_FILE),
        filter=filter,
    )
