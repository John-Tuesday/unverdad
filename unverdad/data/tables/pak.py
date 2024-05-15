"""SQL table for pak and sig files.

This table ties .pak and .sig files to each other and to a mod in the mod table.
Module level function are for manipulating the table.

"""

import dataclasses
import enum
import pathlib
import uuid
from typing import Optional

TABLE_NAME = "pak"


class PakError(enum.Enum):
    """Error types used by PakReport."""

    STEM_MISMATCH = enum.auto()
    PAK_WRONG_EXTENSION = enum.auto()
    SIG_WRONG_EXTENSION = enum.auto()


class PakReport:
    """Collection of errors, if any, found during pak validation."""

    def __init__(self):
        self.errors = []

    def add_error(self, error: PakError):
        self.errors.append(error)

    def is_good(self) -> bool:
        return len(self.errors) == 0

    def to_exception(self) -> Optional[Exception]:
        if self.is_good():
            return None
        msg = " ".join([f"{e}" for e in self.errors])
        return Exception(msg)

    def good_or_raise(self):
        e = self.to_exception()
        if e is None:
            return self
        raise e


@dataclasses.dataclass
class PakEntity:
    """
    Attributes:
        pak_id: local id
        mod_id: associated mod id
        pak_path: filepath of .pak, relative to mod home
        sig_path: filepath of .sig, relative to mod home
    """

    pak_id: uuid.UUID
    mod_id: uuid.UUID
    pak_path: pathlib.Path
    sig_path: pathlib.Path

    def _params(self):
        return dataclasses.asdict(self)

    def validate(self) -> PakReport:
        report = PakReport()
        if self.pak_path.suffix != ".pak":
            report.add_error(PakError.PAK_WRONG_EXTENSION)
        if self.sig_path.suffix != ".sig":
            report.add_error(PakError.SIG_WRONG_EXTENSION)
        if self.pak_path.stem != self.sig_path.stem:
            report.add_error(PakError.STEM_MISMATCH)
        return report


def create_table(con):
    """Create table if it doesn't exist.

    This function does not check if the schema is as expected.
    """
    with con:
        con.execute(
            """
CREATE TABLE IF NOT EXISTS pak (
    pak_id uuid NOT NULL PRIMARY KEY,
    mod_id uuid NOT NULL,
    pak_path path NOT NULL,
    sig_path path NOT NULL
)
        """
        )


def insert_many(con, data: list[PakEntity]):
    """Insert each of data into pak table."""
    d = [x._params() for x in data]
    with con:
        con.executemany(
            """
INSERT INTO pak (pak_id, mod_id, pak_path, sig_path)
VALUES (:pak_id, :mod_id, :pak_path, :sig_path)
        """,
            d,
        )


def delete_many(con, ids: list[uuid.UUID]):
    """Delete each row whose pak_id is in ids."""
    d = [{"pak_id": x} for x in ids]
    with con:
        con.executemany(
            """
DELETE FROM pak
VALUES pak_id = :pak_id
        """,
            d,
        )


def delete_all(con):
    """Delete all rows of table pak."""
    with con:
        con.execute("DELETE FROM pak")
