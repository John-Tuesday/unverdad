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

def parse_args(on_install = install_mods, on_uninstall = uninstall_mods, on_clear_log = lambda _: None, on_config_verify = config_verify, root_logger = logging.getLogger()):
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
    install_p   = subparsers.add_parser("install", help="install all mods")
    install_p.set_defaults(hook=on_install)
    uninstall_p = subparsers.add_parser("uninstall", help="remove all mods from install location")
    uninstall_p.set_defaults(hook=on_uninstall)
    clear_log_p = subparsers.add_parser("clear-log", help="clear log and exit")
    clear_log_p.set_defaults(hook=on_clear_log, fm='w', load_config=False)
    config_verify_p = subparsers.add_parser("config-verify", help="verify config")
    config_verify_p.set_defaults(hook=on_config_verify)
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

    if args.load_config:
        args.config = Config.load()

    args.hook(args.config)
