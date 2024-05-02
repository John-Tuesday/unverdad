"""Import mods and mod metadata"""
import logging
logger = logging.getLogger(__name__)

from unverdad import config
from unverdad.data import database
from unverdad.data import mod_table

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
        con = database.get_db(config.DB_FILE)
        with con:
            mod_table._create_mod_table(con)
            mod_table._delete_all_from_mod_table(con)
            mod_table.generate_metadata(conf.mods_dir, con)
        for row in con.execute('SELECT * FROM mod'):
            print(row)
        

