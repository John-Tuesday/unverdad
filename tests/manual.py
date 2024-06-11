from tests.data import fixture_database as fd
from unverdad import run
from unverdad.data import database


def manual_main():
    con = database._reset_db(db_path=None)
    print("IN MEMORY DATABASE")
    fd.insert_samples(con)
    print("TEST SAMPLES IN USE")
    run.parse_args()
    fd.print_all(con)


if __name__ == "__main__":
    manual_main()
