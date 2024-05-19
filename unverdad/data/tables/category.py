import dataclasses
import uuid
from typing import Optional

TABLE_NAME = "category"


@dataclasses.dataclass
class CategoryEntity:
    category_id: uuid.UUID
    name: str
    parent_id: Optional[uuid.UUID] = None


def create_table(con):
    with con:
        con.execute(
            """
        CREATE TABLE IF NOT EXISTS category (
            category_id uuid NOT NULL PRIMARY KEY,
            parent_id uuid,
            name TEXT NOT NULL,
            FOREIGN KEY (parent_id)
            REFERENCES category (category_id)
                ON DELETE CASCADE
        )
            """
        )


def insert_many(con, data: list[CategoryEntity]):
    with con:
        con.executemany(
            """
        INSERT INTO category (category_id, parent_id, name)
        VALUES (:category_id, :parent_id, :name)
            """,
            [dataclasses.asdict(x) for x in data],
        )


def delete_many(con, data: list[uuid.UUID]):
    with con:
        con.executemany(
            """
        DELETE FROM category
        WHERE category_id = :category_id
            """,
            [{"category_id": x} for x in data],
        )


def delete_all(con):
    with con:
        con.execute("DELETE FROM category")
