from unverdad.data.tables import game, mod, pak

def as_list():
    return [game, mod, pak]

def __init_tables(con):
    for table in as_list():
        table.create_table(con)

