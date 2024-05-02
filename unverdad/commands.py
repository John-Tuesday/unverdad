import argparse
from unverdad.config import AppConfig, Config
import logging
import subprocess
import sys
from typing import override
logger = logging.getLogger(__name__)

from unverdad import subcommands
from unverdad.subcommands import subcommand

class InstallSubCmd(subcommand.SubCommand):
    """"Install mods."""
    @override
    def attach(self, subparsers) -> argparse.ArgumentParser:
        return subparsers.add_parser("install", help="install all mods")

    @override
    def hook(self, args):
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

class UninstallSubCmd(subcommand.SubCommand):
    """Uninstall mods."""
    @override
    def attach(self, subparsers) -> argparse.ArgumentParser:
        return subparsers.add_parser("uninstall", help="remove all mods from install location")

    @override
    def hook(self, args):
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

class ReinstallSubCmd(subcommand.SubCommand):
    """Uninstall mods, then install mods."""
    @override
    def attach(self, subparsers) -> argparse.ArgumentParser:
        return subparsers.add_parser("reinstall", help="equivalent to uninstall then install")

    @override
    def hook(self, args):
        logger.info("reinstall")
        UninstallSubCmd().hook(args)
        InstallSubCmd().hook(args)

class ClearLogSubCmd(subcommand.SubCommand):
    """Clear log file."""
    @override
    def attach(self, subparsers) -> argparse.ArgumentParser:
        p = subparsers.add_parser("clear-log", help="clear log and exit")
        p.set_defaults(log_mode='w', hook=lambda _: logger.info('log cleared'))
        return p

def parse_args(
    root_logger: logging.Logger = logging.getLogger(),
    subcommands: list[subcommand.SubCommand] = [
        # subcommands.config, 
        InstallSubCmd(),
        UninstallSubCmd(),
        ReinstallSubCmd(),
        # subcommands.info,
        ClearLogSubCmd(),
    ] + subcommands.as_list()
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

