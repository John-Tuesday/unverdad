"""Import mods and mod metadata"""
import logging
logger = logging.getLogger(__name__)

from ggsmm import config
from ggsmm import mod_metadata as meta

def attach(subparsers):
    parser = subparsers.add_parser(
        'import',
        help='import mods',
    )
    parser.add_argument(
        '--refresh',
        help='Remove old metadata and reparse metadata',
        action='store_true', default=True,
    )
    return parser

def hook(args):
    conf = args.config
    if args.refresh:
        logger.info(f'refresh metadata')
        con = meta.get_db(config.AppConfig.DB_FILE)
        with con:
            meta._create_mod_table(con)
            meta._delete_all_from_mod_table(con)
            meta.generate_metadata(conf.mods_dir, con)
        for row in con.execute('SELECT * FROM mod'):
            print(row)
        

