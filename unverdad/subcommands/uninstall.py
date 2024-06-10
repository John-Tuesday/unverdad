import argparse
import logging
import pathlib
import subprocess
import uuid

from unverdad import config, errors
from unverdad.data import database, tables

logger = logging.getLogger(__name__)


def attach(subparsers) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "uninstall",
        help="uninstall mods for a game",
        description="uninstall all mods for a given game",
    )
    parser.add_argument(
        "--dry",
        help="do not perform any actions; print what would be done instead",
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
        return logger.warning(
            f"tried to recursively remove '{dir}' but is not a directory."
        )
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    logger.debug(result.stdout)
    result.check_returncode()


def hook(args) -> errors.UnverdadError | None:
    sql_statement = """SELECT * FROM game WHERE """
    param = {}
    if args.game_id:
        sql_statement += "game_id = :game_id"
        param["game_id"] = args.game_id
    elif args.game_name or config.SETTINGS.default_game.enabled:
        sql_statement += "match_name(name, :game_name)"
        param["game_name"] = args.game_name or config.SETTINGS.default_game.name
    else:
        args.subparser.error("specify a game or enable default_game")
    con = database.get_db()
    game_row = con.execute(sql_statement, param).fetchone()
    if game_row is None:
        return errors.UnverdadError("no game found")
    game = tables.game.GameEntity(**game_row)
    if game.game_path is None:
        return errors.UnverdadError("game path needs to be set")
    mods_home = game.game_path / game.game_path_offset / game.mods_home_relative_path
    mods_home = mods_home.expanduser().resolve()
    __remove_dir(mods_home, dry=args.dry)
