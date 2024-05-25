import logging
import pathlib
import sqlite3
import uuid
from typing import Optional

from unverdad.data import schema, tables

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def sample_game() -> tables.game.GameEntity:
    game = tables.game.GameEntity(
        game_id=schema.new_uuid(),
        name="TEST GAME",
        game_path=pathlib.Path("game/root/"),
        game_path_offset=pathlib.Path("offset"),
        mods_home_relative_path=pathlib.Path("~mods"),
    )
    return game


def sample_mods(game_id: uuid.UUID, len: int = 4) -> list[tables.mod.ModEntity]:
    return [
        tables.mod.ModEntity(
            mod_id=schema.new_uuid(),
            game_id=game_id,
            name=f"Test {i}",
        )
        for i in range(0, len)
    ]


def sample_paks(
    mod_id: uuid.UUID,
    mod_name: str,
    len: int = 2,
) -> list[tables.pak.PakEntity]:
    mod_name = mod_name or "mod"
    return [
        tables.pak.PakEntity(
            pak_id=schema.new_uuid(),
            mod_id=mod_id,
            pak_path=pathlib.Path(f"relative/path/{mod_name}/ex_{i}.pak"),
            sig_path=pathlib.Path(f"relative/path/{mod_name}/ex_{i}.sig"),
        )
        for i in range(0, len)
    ]


def sample_categories(
    parent_id: Optional[uuid.UUID] = None,
    len: int = 4,
) -> list[tables.category.CategoryEntity]:
    return [
        tables.category.CategoryEntity(
            category_id=schema.new_uuid(),
            name=f"{"CHILD" if parent_id else "ROOT" } {i}",
            parent_id=parent_id,
        )
        for i in range(0, len)
    ]


def print_table(con, table_name: str):
    print(f"[{table_name}]")
    with con:
        for row in con.execute(f"SELECT * FROM {table_name}"):
            print(row)


def print_all(con: sqlite3.Connection):
    for t in [x.TABLE_NAME for x in tables.as_list()] + ["v_mod", "v_pak"]:
        print_table(con, t)
        print("")
    print("---===---===---\n")


def insert_samples(con: sqlite3.Connection):
    game = sample_game()
    mods = sample_mods(game_id=game.game_id)
    paks = []
    for mod in mods:
        paks.extend(sample_paks(mod_id=mod.mod_id, mod_name=mod.name))
    categories = []
    for category in sample_categories():
        categories.append(category)
        categories.extend(sample_categories(parent_id=category.category_id, len=2))
    mod_categories = []
    for mod, category in zip(mods[1:], categories):
        mod_categories.append(
            tables.mod_category.ModCategoryEntity(
                mod_id=mod.mod_id,
                category_id=category.category_id,
            )
        )
    tables.game.insert_one(con, game)
    tables.mod.insert_many(con, mods)
    tables.pak.insert_many(con, paks)
    tables.category.insert_many(con, categories)
    tables.mod_category.insert_many(con, mod_categories)
