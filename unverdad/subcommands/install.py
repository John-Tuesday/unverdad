"""Install mods
"""

import argparse
import logging
import pathlib
import subprocess
import uuid

from unverdad import config
from unverdad.data import builders, database, tables, views


def attach(subparsers) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "install",
        help="install all mods",
        description="install all enabled mods to a game",
    )
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
    return parser


def __copy_files(
    files: list[pathlib.Path],
    dir: pathlib.Path,
    dry: bool = False,
):
    cmd = ["cp", "-n", *files, dir]
    if dry:
        print(*[f"'{x}'" if isinstance(x, pathlib.Path) else f"{x}" for x in cmd])
        return
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    result.check_returncode()


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
    elif args.game_name or config.SETTINGS.default_game.enabled:
        game_cond._add_param_expr(
            column_name="game_name",
            expression="match_name({column}, {param})",
            param_value=args.game_name or config.SETTINGS.default_game.name,
        )
    else:
        return logger.error("Specify a game or enable a default_game")
    mod_conds = conditions.add_subfilter(combine_operator=builders.LogicalOperator.OR)
    mod_conds._add_param(column_name="enabled", column_value=True)
    for mod_id in args.mod_ids:
        mod_conds._add_param(column_name="mod_id", column_value=mod_id)
    db = database.get_db()
    sql_statement = f"SELECT * FROM v_mod\nWHERE {conditions.render()}"
    logger.debug(f"{sql_statement=!s}")
    for mod_row in db.execute(sql_statement, conditions.params()):
        mod = views.ModView(**mod_row)
        destination = (mod.game_path / mod.game_path_offset).expanduser().resolve()
        if not destination.is_dir():
            return logger.error(f"Game path offset is not a valid directory")
        destination = mod.install_path.expanduser().resolve()
        if args.dry:
            print(f"mkdir -p '{destination}'")
        else:
            destination.mkdir(parents=True, exist_ok=True)
        mod_files = []
        for pak_row in db.execute(
            f"SELECT * FROM v_pak WHERE mod_id = ?", [mod.mod_id]
        ):
            pak = views.PakView(**pak_row)
            pak_path = (config.SETTINGS.mods_home / pak.pak_path).expanduser().resolve()
            sig_path = (config.SETTINGS.mods_home / pak.sig_path).expanduser().resolve()
            if not pak_path.is_file() or not sig_path.is_file():
                logger.error(f"'{pak_path}' and/or '{sig_path}' are not valid files")
                mod_files = []
                break
            mod_files.append(pak_path)
            mod_files.append(sig_path)
        logger.info(f"installing mod '{mod.mod_name}' ({len(mod_files)} files)...")
        __copy_files(files=mod_files, dir=destination, dry=args.dry)
