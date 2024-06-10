import sys

from unverdad import commands


def main():
    commands.mkdir_homes()
    return commands.parse_args()


if __name__ == "__main__":
    sys.exit(main())
