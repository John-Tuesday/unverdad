import logging
import sqlite3
import uuid

from unverdad.data import database, tables

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def sample_mods(game_id: uuid.UUID, len: int = 4) -> list[tables.mod.ModEntity]:
    return [
        tables.mod.ModEntity(
            mod_id=database._new_uuid(),
            game_id=game_id,
            name=f"Test {i}",
        )
        for i in range(0, len)
    ]


def sample_game() -> tables.game.GameEntity:
    return tables.game.GameEntity(game_id=database._new_uuid(), name="Guilty TEST TEST")


def sample_categories(len: int = 4) -> list[tables.category.CategoryEntity]:
    return [
        tables.category.CategoryEntity(
            category_id=database._new_uuid(),
            name=f"CAT {i}",
            parent_id=None,
        )
        for i in range(0, len)
    ]


def make_child_cat(parent_id: uuid.UUID) -> tables.category.CategoryEntity:
    return tables.category.CategoryEntity(
        category_id=database._new_uuid(),
        name=f"CHILD",
        parent_id=parent_id,
    )


def init_samples(con: sqlite3.Connection) -> uuid.UUID:
    with con:
        game = sample_game()
        tables.game.insert_one(con, game)
        mods = sample_mods(game_id=game.game_id)
        tables.mod.insert_many(con, mods)
        cats = sample_categories()
        parent_cat = cats[0]
        cats.append(make_child_cat(parent_id=parent_cat.category_id))
        tables.category.insert_many(con, cats)
        mod_cats = [
            tables.mod_category.ModCategoryEntity(
                mod_id=mods[1].mod_id, category_id=x.category_id
            )
            for x in cats
        ]
        tables.mod_category.insert_many(con, mod_cats)
        return parent_cat.category_id


def print_table(con, table_name: str):
    print(f"[{table_name}]")
    with con:
        for row in con.execute(f"SELECT * FROM {table_name}"):
            print(row)


def print_all(con):
    for t in ["game", "category", "mod", "mod_category"]:
        print_table(con, t)
        print("")
    print("---===---===---\n")


def main():
    con = database.get_db()
    print_all(con)
    parent_id = init_samples(con)
    con.commit()
    print_all(con)
    with con:
        tables.category.delete_many(con, [parent_id])
    con.commit()
    print_all(con)


main()
