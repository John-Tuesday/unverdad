"""Gather (and verify) details of mods"""
import logging
logger = logging.getLogger(__name__)

def attach(subparsers):
    parser = subparsers.add_parser('info', help='detect and how actively installed mods')
    verify_sigs_g = parser.add_mutually_exclusive_group()
    verify_sigs_g.add_argument(
        '--verify-sigs',
        help='explicitly check for corresponding .sig files to each .pak',
        action='store_true', default=True)
    verify_sigs_g.add_argument(
        '--no-verify-sigs',
        help='explicitly skip the check for corresponding .sig files to each .pak',
        action='store_false', dest='verify_sigs')
    return parser

def hook(args):
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

