from unverdad.data.tables import category, game, mod, mod_category, pak


def as_list():
    return [category, game, mod, mod_category, pak]


def init_tables(con):
    for table in as_list():
        table.create_table(con)
