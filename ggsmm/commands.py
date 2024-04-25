import argparse
from ggsmm.config import AppConfig, Config, ConfigError, ConfigKeyNotInSchema
import logging
import subprocess
import sys
from typing import override, Protocol
logger = logging.getLogger(__name__)

class SubCommand(Protocol):
    """Factory for ArgumentParsers with a hook for when it's called."""
    @staticmethod
    def attach(subparsers) -> argparse.ArgumentParser: 
        """Add parser to subparsers, configure, then return the result."""
        ...

    @staticmethod
    def hook(args) -> None: 
        """Perform action.

        Called immediately after loading config.

        Args:
            args:
                Namespace object resulting from the parsed args; plus,
                args.config holds the resulting config.Config object.
        """
        ...

class InstallSubCmd(SubCommand):
    """"Install mods."""
    @override
    @staticmethod
    def attach(subparsers) -> argparse.ArgumentParser:
        return subparsers.add_parser("install", help="install all mods")

    @override
    @staticmethod
    def hook(args):
        logger.info("install mods")
        config = args.config
        config.install_dir.mkdir(exist_ok=True)
        result = subprocess.run(
                ['cp', '--verbose', '--recursive', config.mods_dir, config.install_dir], 
                capture_output=True,
                text=True)
        logger.debug(result.stdout)
        result.check_returncode()
        logger.info("install finished")
        return

class UninstallSubCmd(SubCommand):
    """Uninstall mods."""
    @override
    @staticmethod
    def attach(subparsers) -> argparse.ArgumentParser:
        return subparsers.add_parser("uninstall", help="remove all mods from install location")

    @override
    @staticmethod
    def hook(args):
        logger.info("uninstall mods")
        config = args.config
        result = subprocess.run(
                ['rm', '--verbose', '--recursive', config.install_dir],
                capture_output=True,
                text=True)
        logger.debug(result.stdout)
        result.check_returncode()
        logger.info("uninstall finished")
        return

class ReinstallSubCmd(SubCommand):
    """Uninstall mods, then install mods."""
    @override
    @staticmethod
    def attach(subparsers) -> argparse.ArgumentParser:
        return subparsers.add_parser("reinstall", help="equivalent to uninstall then install")

    @override
    @staticmethod
    def hook(args):
        logger.info("reinstall")
        UninstallSubCmd.hook(args)
        InstallSubCmd.hook(args)

class ClearLogSubCmd(SubCommand):
    """Clear log file."""
    @override
    @staticmethod
    def attach(subparsers) -> argparse.ArgumentParser:
        p = subparsers.add_parser("clear-log", help="clear log and exit")
        p.set_defaults(log_mode='w', hook=lambda _: logger.info('log cleared'))
        return p

class ConfigSubCmd(SubCommand):
    """Config related sub commands."""
    @override
    @staticmethod
    def attach(subparsers) -> argparse.ArgumentParser:
        parser = subparsers.add_parser('config', help='interact with current config')
        g = parser.add_mutually_exclusive_group()
        g.add_argument(
            '-l', '--list-all', 
            help='list all config key-value pairs',
            action="store_true")
        g.add_argument(
            '-g', '--get', 
            help='get config value from key',
            action="extend", nargs='+',
            dest='keys', metavar='KEY')
        g.add_argument(
            '--verify',
            help='verify config file is valid',
            action='store_true')
        return parser

    @override
    @staticmethod
    def hook(args):
        logger.info('config')
        if args.keys:
            logger.info('get config value by one or more keys')
            try:
                lines = '\n'.join([f'    {args.config.toml_str_at(key)}' for key in args.keys])
                logger.info(f'{{\n{lines}\n}}')
            except ConfigKeyNotInSchema:
                pass

        elif args.list_all:
            logger.info('list all config options')
            logger.info(f'{args.config}')
        elif args.verify:
            logger.info('verify config')
            logger.info('verified ...')

def parse_args(
    root_logger: logging.Logger = logging.getLogger(),
    subcommands: list[type[SubCommand]] = [
        InstallSubCmd,
        UninstallSubCmd,
        ReinstallSubCmd,
        ConfigSubCmd,
        ClearLogSubCmd,
    ],
):
    """Parse args to configure and perform user chosen actions.

    Creates, configures, and runs an argparse.ArgumentParser.
    According to the parsed arguments, configure logging and run associated
    hook functions.
    """
    parser = argparse.ArgumentParser(description="manage mods for Guilty Gear Strive")
    parser.set_defaults(log_mode='a', out_lvl=logging.INFO)
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument("-v", "--verbose", help="detailed output", action="store_const", const=logging.DEBUG, dest='out_lvl')
    verbosity_group.add_argument("-q", "--quiet", help="silent output", action="store_const", const=logging.ERROR, dest='out_lvl')
    subparsers = parser.add_subparsers(
            title="subcommands",
            description="control mod installation",
            required=True,
            )
    for subcmd in subcommands:
        p = subcmd.attach(subparsers)
        p.set_defaults(hook=subcmd.hook)
    args = parser.parse_args()

    # init logger handles
    console_h = logging.StreamHandler(sys.stdout)
    console_h.setLevel(args.out_lvl)
    console_h.setFormatter(logging.Formatter())
    root_logger.addHandler(console_h)
    file_h = logging.FileHandler(filename=AppConfig.LOG_FILE, mode=args.log_mode)
    file_h.setLevel(logging.DEBUG)
    file_h.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
    root_logger.addHandler(file_h)

    args.config = Config.load_toml()
    args.hook(args)

