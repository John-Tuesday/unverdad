"""Import all subcommands.

Designed to be imported under a namespace.
    example: `from unverdad import subcommands`
"""

from unverdad.subcommands import config, import_mods, info, install, mod_registry


def as_list():
    """Return a new list of all subcommand modules."""
    return [info, config, import_mods, install, mod_registry]
