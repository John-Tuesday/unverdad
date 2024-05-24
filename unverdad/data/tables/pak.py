"""SQL table for pak and sig files.

This table ties .pak and .sig files to each other and to a mod in the mod table.
Module level function are for manipulating the table.

"""

import dataclasses
import pathlib
import uuid

TABLE_NAME = "pak"


@dataclasses.dataclass
class PakEntity:
    """
    Attributes:
        pak_id: local id
        mod_id: associated mod id
        pak_path: filepath of .pak, relative to parent mod
        sig_path: filepath of .sig, relative to parent mod
    """

    pak_id: uuid.UUID
    mod_id: uuid.UUID
    pak_path: pathlib.Path
    sig_path: pathlib.Path


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
    pak_path path NOT NULL CHECK(pak_path LIKE '%.pak'),
    sig_path path NOT NULL CHECK(sig_path LIKE '%.sig'),
    FOREIGN KEY (mod_id)
    REFERENCES mod (mod_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
)
        """
        )


def insert_many(con, data: list[PakEntity]):
    """Insert each of data into pak table."""
    d = [dataclasses.asdict(x) for x in data]
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
