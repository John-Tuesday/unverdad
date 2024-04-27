import argparse
from ggsmm.config import AppConfig, Config, ConfigError, ConfigKeyNotInSchema
import logging
import subprocess
import sys
from typing import override, Protocol
logger = logging.getLogger(__name__)

from ggsmm.subcommands import config, subcommand

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
        UninstallSubCmd.hook(args)
        InstallSubCmd.hook(args)

class ClearLogSubCmd(subcommand.SubCommand):
    """Clear log file."""
    @override
    def attach(self, subparsers) -> argparse.ArgumentParser:
        p = subparsers.add_parser("clear-log", help="clear log and exit")
        p.set_defaults(log_mode='w', hook=lambda _: logger.info('log cleared'))
        return p

class DetectInstalledSubCmd(subcommand.SubCommand):
    """Detect and show which mods are currently installed."""
    @override
    def attach(self, subparsers):
        p = subparsers.add_parser('detect', help='detect and how actively installed mods')
        g = p.add_mutually_exclusive_group()
        g.add_argument(
            '--verify-sigs',
            help='explicitly check for corresponding .sig files to each .pak',
            action='store_true', default=True)
        g.add_argument(
            '--no-verify-sigs',
            help='explicitly skip the check for corresponding .sig files to each .pak',
            action='store_false', dest='verify_sigs')
        return p

    @override
    def hook(self, args):
        logger.info('detecting installed mods')
        logger.debug(f'verify_sigs: {args.verify_sigs}')
        config = args.config
        mods_found = {f.stem: [1, 0] for f in config.install_dir.glob('**/*.pak')}
        if args.verify_sigs:
            for f in config.install_dir.glob('**/*.sig'):
                mods_found.setdefault(f.stem, [0, 0])[1] += 1
        def stats_str(stats):
            match stats:
                case [1, y] if not args.verify_sigs or y == 1:
                    return 'Loaded!'
                case [0, y]:
                    return 'There is not matching .pak'
                case [1, 0] if args.verify_sigs:
                    return 'There is no matching .sig'
                case _:
                    return 'Unknown error'
        msg = '\n'.join([f'{key}: {stats_str(value)}' for key, value in mods_found.items()])
        logger.info(f'{msg}')

def parse_args(
    root_logger: logging.Logger = logging.getLogger(),
    subcommands: list[subcommand.SubCommand] = [
        config, 
        InstallSubCmd(),
        UninstallSubCmd(),
        ReinstallSubCmd(),
        DetectInstalledSubCmd(),
        ClearLogSubCmd(),
    ]
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

