import argparse
from ggsmm.config import AppConfig, Config
import logging
import subprocess
import sys
logger = logging.getLogger(__name__)

def install_mods(config):
    logger.info("install mods")
    if not config.is_valid():
        msg = "invalid config! Aborting install"
        logger.error(msg)
        raise Exception(msg)
    config.install_dir.mkdir(exist_ok=True)
    result = subprocess.run(
            ['cp', '--verbose', '--recursive', config.mods_dir, config.install_dir], 
            capture_output=True,
            text=True)
    logger.debug(result.stdout)
    result.check_returncode()
    logger.info("install finished")
    return

def uninstall_mods(config):
    logger.info("uninstall mods")
    if not config.validate_install_dir():
        msg = "invalid install_dir! Aborting uninstall"
        logger.error(msg)
        raise Exception(msg)
    result = subprocess.run(
            ['rm', '--verbose', '--recursive', config.install_dir],
            capture_output=True,
            text=True)
    logger.debug(result.stdout)
    result.check_returncode()
    logger.info("uninstall finished")
    return

def config_verify(config):
    logger.info('verify config')
    if config.is_valid():
        logger.info('config is valid')
    else:
        logger.warning('config is NOT VALID')

class SubCommand:
    @property
    def name(self):
        pass

    @staticmethod
    def attach(subparsers) -> argparse.ArgumentParser:
        ...

    @staticmethod
    def hook(args):
        ...

class InstallSubCmd(SubCommand):
    @staticmethod
    def attach(subparsers) -> argparse.ArgumentParser:
        return subparsers.add_parser("install", help="install all mods")

    @staticmethod
    def hook(args):
        install_mods(args)

class UninstallSubCmd(SubCommand):
    @staticmethod
    def attach(subparsers) -> argparse.ArgumentParser:
        return subparsers.add_parser("uninstall", help="remove all mods from install location")

    @staticmethod
    def hook(args):
        uninstall_mods(args)

class ClearLogSubCmd(SubCommand):
    @staticmethod
    def attach(subparsers) -> argparse.ArgumentParser:
        p = subparsers.add_parser("clear-log", help="clear log and exit")
        p.set_defaults(fm='w', hook=lambda _: None)
        return p

class ConfigVerifySubCmd(SubCommand):
    @staticmethod
    def attach(subparsers) -> argparse.ArgumentParser:
        p = subparsers.add_parser("config-verify", help="verify config")
        return p

    @staticmethod
    def hook(args):
        config_verify(args)

def parse_args(
    root_logger = logging.getLogger(),
    subcommands = [
        InstallSubCmd,
        UninstallSubCmd,
        ClearLogSubCmd,
        ConfigVerifySubCmd,
    ],
):
    parser = argparse.ArgumentParser(description="manage mods for Guilty Gear Strive")
    parser.set_defaults(fm='a', out_lvl=logging.INFO, load_config=True)
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
    file_h = logging.FileHandler(filename=AppConfig.LOG_FILE, mode=args.fm)
    file_h.setLevel(logging.DEBUG)
    file_h.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
    root_logger.addHandler(file_h)

    args.config = Config.load()

    args.hook(args.config)
