"""Subcommand for imported mods.
"""

import argparse
import logging
import sqlite3
import uuid

from unverdad import config
from unverdad.data import builders, database, tables

logger = logging.getLogger(__name__)


def attach(subparsers):
    parser = subparsers.add_parser(
        "mod-registry",
        help="interact with imported, but not installed mods.",
    )
    game_opt = parser.add_argument_group(title="game")
    game_opt = game_opt.add_mutually_exclusive_group()
    game_opt.add_argument(
        "--game-id",
        help="Only include results for a particular game given its ID",
        type=uuid.UUID,
    )
    game_opt.add_argument(
        "--game-name",
        help="Only include results for a particular game given its NAME",
    )
    enabled_group = parser.add_mutually_exclusive_group()
    enabled_group.add_argument(
        "--enable",
        help="enable matching mods",
        action="store_true",
    )
    enabled_group.add_argument(
        "--disable",
        help="disable matching mods",
        action="store_true",
    )
    parser.add_argument(
        "--mod-id",
        "-m",
        help="Select MOD_ID",
        action="append",
        dest="mod_ids",
        default=[],
        type=uuid.UUID,
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


def __on_show(
    conf,
    con,
    cond: builders.ConditionBuilder,
):
    """"""
    data = []
    with con:
        sql_clause = cond.render()
        params = cond.params()
        if sql_clause:
            sql_clause = f"WHERE {sql_clause}"
        for mod_row in con.execute(f"SELECT * FROM mod {sql_clause}", params):
            s = "\n".join([f"| {key} = {mod_row[key]}" for key in mod_row.keys()])
            s = f"{mod_row["name"]}\n{s}"
            data.append(s)
    msg = "\n\n".join(data)
    logger.info(f"{msg}")


def __on_set(
    con: sqlite3.Connection,
    cond: builders.ConditionBuilder,
    enabled: bool,
) -> None:
    with con:
        con.execute(
            f"UPDATE mod SET enabled = :enabled WHERE {cond.render()}",
            cond.params() | {"enabled": enabled},
        )


def hook(args):
    """"""
    conditions = builders.ConditionBuilderBranch(
        combine_operator=builders.LogicalOperator.AND,
    )
    or_conds = conditions.add_subfilter(combine_operator=builders.LogicalOperator.OR)
    and_conds = conditions.add_subfilter(combine_operator=builders.LogicalOperator.AND)
    for mod_id in args.mod_ids:
        or_conds._add_param(column_name="mod_id", column_value=mod_id)
    for mod_name in args.mod_names:
        or_conds._add_param(column_name="name", column_value=mod_name)
    con = database.get_db()
    if args.game_id:
        and_conds._add_param(column_name="game_id", column_value=args.game_id)
    elif args.game_name:
        for game_row in con.execute(
            "SELECT * FROM game WHERE name = :name", {"name": args.game_name}
        ):
            game_entity = tables.game.GameEntity(**game_row)
            and_conds._add_param(
                column_name="game_id", column_value=game_entity.game_id
            )
    logger.debug(f"{conditions}")
    enable = None
    if args.enable:
        enable = True
    elif args.disable:
        enable = False
    if enable is not None:
        __on_set(
            con=con,
            cond=conditions,
            enabled=enable,
        )
    __on_show(
        conf=args.config,
        con=con,
        cond=conditions,
    )
