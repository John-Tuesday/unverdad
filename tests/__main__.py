import unverdad
from tests.data import fixture_database as fd
from unverdad.data import database


def main():
    con = database._reset_db(db_path=None)
    print("IN MEMORY DATABASE")
    fd.insert_samples(con)
    print("TEST SAMPLES IN USE")
    unverdad.main()
    fd.print_all(con)


main()
