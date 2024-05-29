"""Import all subcommands.

Designed to be imported under a namespace.
    example: `from unverdad import subcommands`
"""

from unverdad.subcommand import SubCommand
from unverdad.subcommands import config, import_mods, install, mod_registry, uninstall


def as_list() -> list[SubCommand]:
    """Return a new list of all subcommand modules."""
    return [config, import_mods, install, mod_registry, uninstall]
