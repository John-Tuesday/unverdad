import dataclasses
import uuid
from typing import Optional

TABLE_NAME = "mod"


@dataclasses.dataclass
class ModEntity:
    """
    Attributes:
        mod_id: mod id for local use
        gb_mod_id: gamebanana mod id
        game_id: game id for local use
    """

    mod_id: uuid.UUID
    game_id: uuid.UUID
    name: str
    gb_mod_id: Optional[str] = None
    enabled: bool = False

    def _params(self):
        return dataclasses.asdict(self)


def create_table(con):
    with con:
        con.execute(
            """
CREATE TABLE IF NOT EXISTS mod (
    mod_id uuid NOT NULL PRIMARY KEY,
    gb_mod_id,
    game_id uuid NOT NULL,
    name TEXT NOT NULL UNIQUE,
    enabled bool CHECK (enabled = 0 or enabled = 1)
)
        """
        )


def insert_many(con, data: list[ModEntity]):
    d = [x._params() for x in data]
    with con:
        con.executemany(
            """
INSERT INTO mod (mod_id, gb_mod_id, game_id, name, enabled)
VALUES (:mod_id, :gb_mod_id, :game_id, :name, :enabled)
        """,
            d,
        )


def delete_many(con, ids: list[uuid.UUID]):
    d = [{"mod_id": x} for x in ids]
    with con:
        con.executemany(
            """
DELETE FROM mod
WHERE mod_id = :mod_id
        """,
            d,
        )


def delete_all(con):
    with con:
        con.execute("DELETE FROM mod")
