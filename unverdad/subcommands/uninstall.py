import argparse
import logging
import pathlib
import subprocess
import uuid

from unverdad.data import builders, database, tables, views

logger = logging.getLogger(__name__)


def attach(subparsers) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("uninstall", help="uninstall all mods for a game")
    parser.add_argument(
        "--dry",
        help="print isnt",
        action="store_true",
    )
    game_opt = parser.add_argument_group(
        title="game",
        description="choose the game in which to uninstall the mods",
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
    return parser


def __remove_dir(dir: pathlib.Path, dry: bool = False):
    cmd = ["rm", "--verbose", "--recursive", dir]
    if dry:
        print(*cmd)
        return
    if not dir.is_dir():
        logger.warning(f"tried to recursively remove '{dir}' but it's not a directory.")
        return
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    logger.debug(result.stdout)
    result.check_returncode()


def hook(args):
    sql_statement = """SELECT * FROM game WHERE """
    param = {}
    if args.game_id:
        sql_statement += "game_id = :game_id"
        param["game_id"] = args.game_id
    else:
        sql_statement += "name = :game_name"
        param["game_name"] = args.game_name or "Guilty Gear Strive"
    con = database.get_db()
    game_row = con.execute(sql_statement, param).fetchone()
    mods_home = game_row["game_path"]
    if game_row["game_path_offset"]:
        mods_home = mods_home / game_row["game_path_offset"]
    if game_row["mods_home_relative_path"]:
        mods_home = mods_home / game_row["mods_home_relative_path"]
    mods_home = mods_home.expanduser().resolve()
    __remove_dir(mods_home, dry=args.dry)
