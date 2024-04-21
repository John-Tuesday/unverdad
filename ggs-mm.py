#!/usr/bin/env python3
import argparse
import logging
import os
import pathlib
import subprocess
import sys
import tomllib
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

APP_NAME = 'ggs-mm'

USER_HOME = os.environ['HOME']
XDG_DATA_HOME = os.getenv('XDG_DATA_HOME', f"{USER_HOME}/.local/share")
DATA_HOME = pathlib.Path(XDG_DATA_HOME) / APP_NAME
XDG_CONFIG_HOME = os.getenv('XDG_CONFIG_HOME', f"{USER_HOME}/.config")
CONFIG_HOME = pathlib.Path(XDG_CONFIG_HOME) / APP_NAME
XDG_STATE_HOME = os.getenv('XDG_STATE_HOME', f"{USER_HOME}/.local/state")
STATE_HOME = pathlib.Path(XDG_STATE_HOME) / APP_NAME

LOG_FILE = STATE_HOME / 'log'

def getDataHome():
    xdg = os.getenv('XDG_DATA_HOME', os.path.expandvars("$HOME/.local/share"))
    return pathlib.Path(xdg, APP_NAME)

class Config:
    def __init__(self, mods_dir, install_parent_dir):
        self.__mods_dir = pathlib.Path(mods_dir).expanduser()
        self.__install_parent_dir = pathlib.Path(install_parent_dir).expanduser()
        self.__install_dir = self.__install_parent_dir / '~mods'

    def mods_dir(self):
        return self.__mods_dir

    def install_parent_dir(self):
        return self.__install_parent_dir

    def install_dir(self):
        return self.__install_dir

    @staticmethod
    def load(config_path):
        data = dict()
        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        return Config(mods_dir = data['mods_dir'], install_parent_dir = data['install_parent_dir'])

def install_mods(mods_dir, install_dir):
    # verify_dir mods_dir
    if not mods_dir.is_dir():
        raise Exception(f'mods_dir is not a directory <{mods_dir}>')
    install_dir.mkdir(exist_ok=True)
    result = subprocess.run(
            ['cp', '--verbose', '--recursive', mods_dir, install_dir], 
            capture_output=True,
            text=True)
    logger.debug(result.stdout)
    result.check_returncode()
    return

def uninstall_mods(install_dir):
    if not install_dir.is_dir():
        raise Exception(f'install_parent_dir is not a directory <{install_dir}>')
    result = subprocess.run(
            ['rm', '--verbose', '--recursive', install_dir],
            capture_output=True,
            text=True)
    logger.debug(result.stdout)
    result.check_returncode()
    return

def load_config():
    logger.debug('loading config')
    return Config.load(CONFIG_HOME/'config.toml')

def on_install(args):
    logger.info('install mods')
    config = load_config()
    install_mods(config.mods_dir(), config.install_dir())
    return

def on_uninstall(args):
    logger.info('uninstall mods')
    config = load_config()
    uninstall_mods(config.install_dir())
    return

def on_clear_log(args):
    logger.info("log cleared")
    return

def main():
    parser = argparse.ArgumentParser(description="manage mods for Guilty Gear Strive")
    parser.set_defaults(fm='a', out_lvl=logging.INFO)
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
    clear_log_p.set_defaults(hook=on_clear_log, fm='w')
    args = parser.parse_args()

    console_h = logging.StreamHandler(sys.stdout)
    console_h.setLevel(args.out_lvl)
    console_h.setFormatter(logging.Formatter())
    logger.addHandler(console_h)
    file_h = logging.FileHandler(filename=LOG_FILE, mode=args.fm)
    file_h.setLevel(logging.DEBUG)
    file_h.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
    logger.addHandler(file_h)

    args.hook(args)

if __name__ == '__main__':
    main()
