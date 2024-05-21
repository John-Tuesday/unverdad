"""Install mods
"""

import argparse
import logging
import subprocess
import uuid

from unverdad.data import builders, database, views


def attach(subparsers) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("install", help="install all mods")
    parser.add_argument(
        "--dry-run",
        help="do not run any commands; instead, print what would have been run.",
        action="store_true",
    )
    parser.add_argument(
        "--mod-id",
        help="include mods by id",
        action="append",
        dest="mod_ids",
        default=[],
        type=uuid.UUID,
    )
    parser.add_argument(
        "--allow-disabled",
        help="do not automatically filter disabled mods",
        action="store_true",
    )
    return parser


def hook(args) -> None:
    logger = logging.getLogger(__name__)
    logger.info("install mods")
    conditions = builders.ConditionBuilderBranch(
        combine_operator=builders.LogicalOperator.AND
    )
    game_cond = conditions.add_subfilter(combine_operator=builders.LogicalOperator.AND)
    game_cond._add_param(
        column_name="game_path",
        column_value=None,
        operator=builders.CompareOperator.NOT_EQUAL,
    )
    mod_conds = conditions.add_subfilter(combine_operator=builders.LogicalOperator.OR)
    if not args.allow_disabled:
        cond = conditions.add_subfilter(combine_operator=builders.LogicalOperator.AND)
        cond._add_param(column_name="enabled", column_value=True)
    for mod_id in args.mod_ids:
        mod_conds._add_param(column_name="mod_id", column_value=mod_id)
    db = database.get_db()
    sql_statement = "SELECT * FROM v_mod"
    if conditions:
        sql_statement = f"{sql_statement}\nWHERE {conditions.render()}"
    logger.debug(f"{sql_statement=!s}")
    for mod_row in db.execute(sql_statement, conditions.params()):
        mod_id = mod_row["mod_id"]
        mod_name = mod_row["mod_name"]
        game_path = mod_row["game_path"]
        game_path_offset = mod_row["game_path_offset"]
        mod_home = mod_row["mods_home_relative_path"]
        game_name = mod_row["game_name"]
        game_id = mod_row["game_id"]
        if game_path is None:
            logger.error(
                f"skipping mod '{mod_name}' because game path is not defined for game '{game_name}' [{game_id}]"
            )
            continue
        destination = (game_path / game_path_offset).expanduser()
        if not destination.is_dir():
            logger.error(f"Game path offset is not a valid directory")
            continue
        destination = (destination / mod_home).resolve()
        if args.dry_run:
            logger.info(f"DRY: mkdir -p '{destination}'")
        else:
            destination.mkdir(parents=True, exist_ok=True)
        if not destination.is_dir():
            logger.error(f"{destination} destination is not a valid directory")
            continue
        mod_files = []
        for pak_row in db.execute(f"SELECT * FROM pak WHERE mod_id = ?", [mod_id]):
            path = args.config.mods_dir.expanduser() / pak_row["pak_path"]
            if not path.is_file():
                logger.error(
                    f"skipping mod '{mod_name}' because '{path}' is not a valid file"
                )
                mod_files = []
                break
            mod_files.append(path)
            path = args.config.mods_dir.expanduser() / pak_row["pak_path"]
            if not path.is_file():
                logger.error(
                    f"skipping mod '{mod_name}' because '{path}' is not a valid file"
                )
                mod_files = []
                break
            mod_files.append(path)
        logger.info(f"installing mod '{mod_name}' ({len(mod_files)} files)...")
        for path in mod_files:
            path = args.config.mods_dir.expanduser() / path
            cmd = ["cp", "--verbose", path, destination]
            if args.dry_run:
                print(f"DRY: {cmd}")
                continue
            logger.debug(f"command: {cmd}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )
            logger.debug(result.stdout)
            result.check_returncode()
