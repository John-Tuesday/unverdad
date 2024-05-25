"""Install mods
"""

import argparse
import logging
import subprocess
import uuid

from unverdad.data import builders, database, tables, views


def attach(subparsers) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("install", help="install all mods")
    game_opt = parser.add_argument_group(
        title="game",
        description="choose the game in which to install the mods",
    )
    game_opt = game_opt.add_mutually_exclusive_group()
    game_opt.add_argument(
        "--game-id",
        help="internal id of the game",
        type=uuid.UUID,
    )
    game_opt.add_argument(
        "--game-name",
        help="name of the game",
    )
    parser.add_argument(
        "--dry",
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
    if args.game_id:
        game_cond._add_param(
            column_name="game_id",
            column_value=args.game_id,
        )
    elif args.game_name:
        game_cond._add_param(
            column_name="game_name",
            column_value=args.game_name.replace("_", r"\_")
            .replace("%", r"\%")
            .replace("\\", "\\\\"),
            operator=builders.CompareOperator.LIKE,
        )
    else:
        game_cond._add_param(
            column_name="game_name",
            column_value="Guilty Gear Strive",
            operator=builders.CompareOperator.LIKE,
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
        mod = views.ModView(**mod_row)
        if mod.game_path is None:
            logger.error(
                f"skipping mod '{mod.mod_name}' because game path is not defined for game '{mod.game_name}' [{mod.game_id}]"
            )
            continue
        destination = (mod.game_path / mod.game_path_offset).expanduser().resolve()
        if not destination.is_dir():
            logger.error(f"Game path offset is not a valid directory")
            continue
        destination = (destination / mod.mods_home_relative_path).resolve()
        if args.dry:
            logger.info(f"DRY: mkdir -p '{destination}'")
        else:
            destination.mkdir(parents=True, exist_ok=True)
        mod_files = []
        for pak_row in db.execute(
            f"SELECT * FROM v_pak WHERE mod_id = ?", [mod.mod_id]
        ):
            pak = views.PakView(**pak_row)
            path = (args.config.mods_dir / pak.pak_path).expanduser().resolve()
            if not path.is_file():
                logger.error(
                    f"skipping mod '{mod.mod_name}' because '{path}' is not a valid file"
                )
                mod_files = []
                break
            mod_files.append(path)
            path = (args.config.mods_dir / pak.sig_path).expanduser().resolve()
            if not path.is_file():
                logger.error(
                    f"skipping mod '{mod.mod_name}' because '{path}' is not a valid file"
                )
                mod_files = []
                break
            mod_files.append(path)
        logger.info(f"installing mod '{mod.mod_name}' ({len(mod_files)} files)...")
        for path in mod_files:
            path = args.config.mods_dir.expanduser() / path
            cmd = ["cp", "--verbose", path, destination]
            if args.dry:
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
