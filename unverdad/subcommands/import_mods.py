"""Import mods and mod metadata"""

import argparse
import logging
import pathlib
import sqlite3
import subprocess
import uuid
from typing import Optional

from unverdad import config
from unverdad.data import database, schema, tables

logger = logging.getLogger(__name__)


def _dir_path(path_str: str) -> pathlib.Path:
    path = pathlib.Path(path_str).resolve()
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"'{path_str}' is not a valid directory")
    return path


def _pak_path(path_str: str) -> tuple[pathlib.Path, pathlib.Path]:
    pak_path = pathlib.Path(path_str).with_suffix(".pak").resolve()
    sig_path = pathlib.Path(path_str).with_suffix(".sig").resolve()
    if not pak_path.is_file():
        raise argparse.ArgumentTypeError(f"'{pak_path}' is not a valid file.")
    if not sig_path.is_file():
        raise argparse.ArgumentTypeError(f"'{sig_path}' is not a valid file.")
    return (pak_path, sig_path)


def attach(subparsers):
    parser = subparsers.add_parser(
        "import",
        help="import mods",
        description="import mods. if name is unspecified, use the first directory name or first file name (minus the suffix) in that order.",
    )
    parser.add_argument(
        "--dry",
        help="do no perform commands; instead, print the commands.",
        action="store_true",
    )
    game_opt = parser.add_mutually_exclusive_group()
    game_opt.add_argument(
        "--game-id",
        help="internal id of the game",
        action="store",
        type=uuid.UUID,
    )
    game_opt.add_argument(
        "--game-name",
        help="name of the game",
        action="store",
    )
    path_args = parser.add_argument_group(
        title="import paths",
        description="Specify directories or specific files to import. Each option may be used more than once.",
    )
    path_args.add_argument(
        "--dir",
        "--directory",
        help="directory containing files to import. directories are flattened.",
        action="append",
        type=_dir_path,
    )
    path_args.add_argument(
        "--file",
        help="path to file to a .pak or .sig file, optionally with no file exention. It then tries the path with a .pak then .sig suffix, replace or appending as necessary.",
        action="append",
        type=_pak_path,
    )
    parser.add_argument(
        "name",
        help="name to be used instead automatically naming",
        nargs="?",
    )
    return parser


def __game_id_name(
    con: sqlite3.Connection,
    name: Optional[str] = None,
    game_id: Optional[uuid.UUID] = None,
) -> tuple[uuid.UUID, str] | str:
    sql_select = f"SELECT name, game_id FROM game WHERE "
    if game_id:
        sql_select += "game_id = ?"
    elif name or config.SETTINGS.default_game.enabled:
        sql_select += "match_name(name, ?)"
    else:
        return "Specify a game or enable a default game"
    row = con.execute(
        sql_select,
        [game_id or name or config.SETTINGS.default_game.name],
    ).fetchone()
    if not row:
        message = f"Could not find game with"
        if game_id:
            return f"{message} id '{game_id}'"
        return f"{message} name '{name or config.SETTINGS.default_game.name}'"
    return (row["game_id"], row["name"])


def __copy_files(files: list[pathlib.Path], dir: pathlib.Path, dry: bool = False):
    cmd = ["cp", "-n"] + files + [dir]
    if dry:
        print(*cmd)
        return
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    result.check_returncode()


def hook(args):
    con = database.get_db()

    match __game_id_name(con=con, game_id=args.game_id, name=args.game_name):
        case (id, name):
            game_id = id
            game_name = name
        case str(msg):
            return logger.error(msg)

    files = args.file or []
    dirs = args.dir or []
    for dir in dirs:
        for pak_path in dir.glob("**/*.pak"):
            files.append(_pak_path(pak_path))

    mod_name = None
    if args.name:
        mod_name = args.name
    elif len(dirs) > 0:
        mod_name = dirs[0].name
    elif len(files) > 0:
        mod_name = files[0][0].stem
    if mod_name is None:
        return logger.error(f"mod name could not be determined")

    parent_dir = config.SETTINGS.mods_home / game_name / mod_name
    parent_dir = parent_dir.expanduser().resolve()
    if args.dry:
        print(f"mkdir -p {parent_dir}")
    else:
        parent_dir.mkdir(parents=True)
    mod = tables.mod.ModEntity(
        mod_id=schema.new_uuid(),
        game_id=game_id,
        name=mod_name,
    )
    paks = [
        tables.pak.PakEntity(
            pak_id=schema.new_uuid(),
            mod_id=mod.mod_id,
            pak_path=pak_path.name,
            sig_path=sig_path.name,
        )
        for pak_path, sig_path in files
    ]
    files = [file for pak in files for file in pak]
    __copy_files(files=files, dir=parent_dir, dry=args.dry)
    if args.dry:
        return print(f"import mod {mod} with paks {paks}")
    with con:
        tables.mod.insert_many(con, [mod])
        tables.pak.insert_many(con, paks)
