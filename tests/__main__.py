from tests.data import fixture_database as fd
from unverdad.data import database


def main():
    con = database.get_db()
    fd.print_all(con)
    fd.insert_samples(con)
    fd.print_all(con)


main()
