import sys

from unverdad import commands


def main():
    commands.mkdir_homes()
    return 0 if commands.parse_args() is None else -1


if __name__ == "__main__":
    sys.exit(main())
