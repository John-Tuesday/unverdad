import argparse
import logging
from typing import Protocol
logger = logging.getLogger(__name__)

class SubCommand(Protocol):
    """Factory for ArgumentParsers with a hook for when it's called."""
    def attach(self, subparsers) -> argparse.ArgumentParser: 
        """Add parser to subparsers, configure, then return the result."""
        ...

    def hook(self, args) -> None: 
        """Perform action.

        Called immediately after loading config.

        Args:
            args:
                Namespace object resulting from the parsed args; plus,
                args.config holds the resulting config.Config object.
        """
        ...

def add_subcommand(subparsers, subcmd: SubCommand) -> argparse.ArgumentParser:
    parser = subcmd.attach(subparsers)
    parser.set_defaults(hook=subcmd.hook)
    return parser
