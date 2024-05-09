import dataclasses
import uuid
from typing import Optional

TABLE_NAME = "game"

@dataclasses.dataclass
class GameEntity:
    game_id: uuid.UUID
    name: str
    gb_game_id: Optional[str] = None

    def _params(self):
        return dataclasses.asdict(self)

def create_table(con):
    with con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS game (
            game_id uuid NOT NULL PRIMARY KEY,
            gb_game_id TEXT,
            name TEXT
        )
        """)

def insert_one(con, data:GameEntity):
    with con:
        con.execute("""
        INSERT INTO game (game_id, gb_game_id, name)
        VALUES (:game_id, :gb_game_id, :name)
        """, data._params())

def delete_many(con, ids:list[uuid.UUID]):
    with con:
        con.executemany("""
        DELETE FROM game
        WHERE game_id = :game_id
        """, [{"game_id":x} for x in ids])

def delete_all(con):
    with con:
        con.execute("""DELETE FROM game""")

