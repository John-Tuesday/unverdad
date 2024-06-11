import sys

from unverdad import run


def main():
    run.mkdir_homes()
    return run.parse_args().code


if __name__ == "__main__":
    sys.exit(main())
