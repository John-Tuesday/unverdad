"""Gather (and verify) details of mods"""
import dataclasses
import enum
import logging
import pathlib
from typing import Optional
logger = logging.getLogger(__name__)

@enum.unique
class _Target(enum.Flag):
    INSTALLED = enum.auto()
    IMPORTED = enum.auto()
    ALL = INSTALLED | IMPORTED

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
    target_g = parser.add_mutually_exclusive_group()
    target_g.add_argument(
        '-i', '--installed-only',
        help='only process mods in install_dir',
        action='store_const', const=_Target.INSTALLED,
        dest='target',
    )
    target_g.add_argument(
        '-u', '--imported-only',
        help='only process mods in mods_dir',
        action='store_const', const=_Target.IMPORTED,
        dest='target',
    )
    target_g.add_argument(
        '-a', '--all',
        help='process mods in installed and imported mods',
        action='store_const', const=_Target.ALL,
        dest='target',
    )
    parser.set_defaults(target=_Target.ALL)
    return parser

@dataclasses.dataclass
class _ModInfo:
    name: str
    pak_path: Optional[pathlib.Path]
    sig_path: Optional[pathlib.Path] = None
    errors: list[str] = dataclasses.field(default_factory=list)

    def status_long(self) -> str:
        if self.errors:
            return '\n'.join(self.errors)
        return 'Okay!'

    def status_short(self) -> str:
        if self.errors:
            return 'ERROR'
        return 'Okay!'

    def pretty_long(self) -> str:
        return f"'{self.name}': {self.status_long()}"

    def pretty_short(self) -> str:
        return f"'{self.name}': {self.status_short()}"

def __detect_mods(dir:pathlib.Path, verify_sigs:bool=True) -> dict[str, _ModInfo]:
    paks = dir.glob('**/*.pak')
    report = {}
    for path in paks:
        if path.stem in report:
            msg = f'Another mod (.pak) with the same was found <{path}>'
            logger.error(msg)
            report[path.stem].errors += msg
        else:
            report[path.stem] = _ModInfo(name=path.stem, pak_path=path)
    if not verify_sigs:
        return report
    for path in dir.glob('**/*.sig'):
        if path.stem in report:
            report[path.stem].sig_path = path
        else:
            msg = f'Mod signature (.sig) without matching (.pak) <{path}>'
            logger.error(msg)
            report[path.stem] = _ModInfo(name=path.stem, pak_path=None, sig_path=path, errors=[msg])
    return report

def hook(args):
    logger.info(f'retrieving info')
    logger.debug(f'target: {args.target}')
    logger.debug(f'verify_sigs: {args.verify_sigs}')
    config = args.config
    reports = {}
    if _Target.INSTALLED in args.target:
        logger.debug(f'detect mods for {_Target.INSTALLED} at <{config.install_dir}>')
        reports[_Target.INSTALLED] = __detect_mods(config.install_dir, verify_sigs=args.verify_sigs)
    if _Target.IMPORTED in args.target:
        logger.debug(f'detect mods for {_Target.IMPORTED} at <{config.mods_dir}>')
        reports[_Target.IMPORTED] = __detect_mods(config.mods_dir, verify_sigs=args.verify_sigs)
    for target, report in reports.items():
        print(f'{target.name}')
        tab = '  '
        for info in report.values():
            print(f'{tab}{info.pretty_short()}')

