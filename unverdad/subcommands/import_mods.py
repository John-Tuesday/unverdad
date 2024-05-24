"""Import mods and mod metadata"""

import argparse
import enum
import logging
import pathlib
import sqlite3
import subprocess
import uuid
from typing import Optional

from unverdad.data import database, defaults, schema, tables

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
        help="import mods. if name is unspecified, use the first directory name or first file name (minus the suffix) in that order.",
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
    parser.add_argument(
        "--default",
        help="install all default values",
        action="store_true",
    )
    parser.add_argument(
        "--refresh",
        help="Remove old metadata and reparse metadata",
        action="store_true",
        default=True,
    )
    return parser


class ImportError(enum.Enum):
    MISSING_SIG = enum.auto()
    MISSING_PAK = enum.auto()
    PAK_ERROR = enum.auto()


class ImportReport:
    def __init__(self):
        self.errors = []

    def add_error(self, error: ImportError):
        self.errors.append(error)


def __auto_add_mods(
    con,
    dir: pathlib.Path,
    game_id: uuid.UUID,
    root_dir: pathlib.Path,
) -> ImportReport:
    report = ImportReport()
    logger.debug(f"auto_add_mods: {dir=}")
    for pak_path in dir.glob("**/*.pak"):
        sig_path = pak_path.with_suffix(".sig")
        if not sig_path.is_file():
            report.add_error(ImportError.MISSING_SIG)
            continue
        mod_id = schema.new_uuid()
        mod_name = pak_path.stem
        mod_entity = tables.mod.ModEntity(
            mod_id=mod_id,
            game_id=game_id,
            name=mod_name,
        )
        pak_entity = tables.pak.PakEntity(
            pak_id=schema.new_uuid(),
            mod_id=mod_id,
            pak_path=pak_path.relative_to(root_dir),
            sig_path=sig_path.relative_to(root_dir),
        )
        pak_report = pak_entity.validate()
        if not pak_report.is_good():
            report.add_error(ImportError.PAK_ERROR)
            continue
        tables.mod.insert_many(con, [mod_entity])
        tables.pak.insert_many(con, [pak_entity])
    return report


def __game_id_name(
    con: sqlite3.Connection,
    name: Optional[str] = None,
    game_id: Optional[uuid.UUID] = None,
) -> tuple[uuid.UUID, str] | None:
    sql_select = f"SELECT name, game_id FROM game WHERE "
    if game_id:
        sql_select += "game_id = ?"
    elif name:
        sql_select += "name LIKE ?"
    else:
        raise ValueError()
    row = con.execute(sql_select, [game_id or name]).fetchone()
    return row and (row["game_id"], row["name"])


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
    conf = args.config
    con = database.get_db()

    game_id = __game_id_name(
        con=con,
        game_id=args.game_id,
        name=args.game_name or "Guilty Gear Strive",
    )
    if game_id is None:
        msg = f"No game exists for '{args.game_name}'"
        logger.error(msg)
        return
    game_id, game_name = game_id

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
        logger.error(f"mod name could not be determined")
        return
    parent_dir = conf.mods_dir / game_name / mod_name
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
    with con:
        tables.mod.insert_many(con, [mod])
        tables.pak.insert_many(con, paks)
    # if args.default:
    #     logger.info("reinstall defaults")
    #     defaults.insert_defaults(con)
    # elif args.refresh:
    #     logger.info(f"refresh metadata")
    #     with con:
    #         tables.mod.delete_all(con)
    #         mods_dir = conf.mods_dir.expanduser().resolve()
    #         __auto_add_mods(
    #             con=con,
    #             dir=mods_dir,
    #             game_id=schema.new_uuid(),
    #             root_dir=mods_dir,
    #         )
    #     print("[mod]")
    #     for row in con.execute("SELECT * FROM mod"):
    #         print(row)
