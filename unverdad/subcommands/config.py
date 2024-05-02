import argparse
import logging
logger = logging.getLogger(__name__)

from unverdad import config

def attach(subparsers) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        'config',
        help='interact with current config',
        description='query/set/verify config values')
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

def hook(args):
    logger.info('config')
    if args.keys:
        logger.info('get config value by one or more keys')
        try:
            lines = '\n'.join([f'    {args.config.toml_str_at(key)}' for key in args.keys])
            logger.info(f'{{\n{lines}\n}}')
        except config.ConfigKeyNotInSchema:
            pass

    elif args.list_all:
        logger.info('list all config options')
        logger.info(f'{args.config}')
    elif args.verify:
        logger.info('verify config')
        logger.info('verified ...')

