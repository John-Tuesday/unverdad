"""Import mods and mod metadata"""

import enum
import logging
import pathlib
import uuid

from unverdad.data import database, tables

logger = logging.getLogger(__name__)


def attach(subparsers):
    parser = subparsers.add_parser(
        "import",
        help="import mods",
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
        mod_id = database._new_uuid()
        mod_name = pak_path.stem
        mod_entity = tables.mod.ModEntity(
            mod_id=mod_id,
            game_id=game_id,
            name=mod_name,
        )
        pak_entity = tables.pak.PakEntity(
            pak_id=database._new_uuid(),
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


def hook(args):
    conf = args.config
    if args.refresh:
        logger.info(f"refresh metadata")
        con = database.get_db()
        with con:
            tables.mod.delete_all(con)
            mods_dir = conf.mods_dir.expanduser().resolve()
            __auto_add_mods(
                con=con,
                dir=mods_dir,
                game_id=database._new_uuid(),
                root_dir=mods_dir,
            )
        print("[mod]")
        for row in con.execute("SELECT * FROM mod"):
            print(row)
