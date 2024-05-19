import dataclasses
import uuid
from typing import Optional

TABLE_NAME = "mod_category"


@dataclasses.dataclass
class ModCategoryEntity:
    mod_id: uuid.UUID
    category_id: uuid.UUID


def create_table(con):
    with con:
        con.execute(
            """
        CREATE TABLE IF NOT EXISTS mod_category (
            mod_id uuid NOT NULL,
            category_id uuid NOT NULL,
            PRIMARY KEY (mod_id, category_id),
            FOREIGN KEY (mod_id)
            REFERENCES mod (mod_id)
                ON DELETE CASCADE,
            FOREIGN KEY (category_id)
            REFERENCES category (category_id)
                ON DELETE CASCADE
        )
            """
        )


def insert_many(con, data: list[ModCategoryEntity]):
    with con:
        con.executemany(
            """
        INSERT INTO mod_category (mod_id, category_id)
        VALUES (:mod_id, :category_id)
            """,
            [dataclasses.asdict(x) for x in data],
        )


def delete_all(con):
    with con:
        con.execute("DELETE FROM mod_category")
