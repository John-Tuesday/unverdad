import argparse
from typing import Protocol

from unverdad import errors


class SubCommand(Protocol):
    """Factory for ArgumentParsers with a hook for when it's called."""

    def attach(self, subparsers) -> argparse.ArgumentParser:
        """Add parser to subparsers, configure, then return the result."""
        ...

    def hook(self, args) -> errors.Result[None]:
        """Perform action.

        Called after loading config and initializing logging.

        :param args: Namespace object resulting from the parsed args.
        """
        ...
