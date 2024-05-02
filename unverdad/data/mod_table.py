import dataclasses
from unverdad import errors
import logging
import pathlib
import sqlite3
from typing import Optional
import uuid
logger = logging.getLogger(__name__)

@dataclasses.dataclass
class ModMetadata:
    mod_id: Optional[uuid.UUID]
    name: str
    pak_path: pathlib.Path
    sig_path: pathlib.Path
    enabled: bool
    auto_generate_id: dataclasses.InitVar[bool] = True

    def __post_init__(self, auto_generate_id):
        if self.mod_id is None and auto_generate_id:
            self.mod_id = ModMetadata.generate_id()

    @staticmethod
    def generate_id() -> uuid.UUID:
        return uuid.uuid4()

    def params(self):
        return {
            'mod_id': self.mod_id,
            'name': self.name,
            'pak_path': self.pak_path,
            'sig_path': self.sig_path,
            'enabled': self.enabled,
        }

def _create_mod_table(con):
    logger.debug('create if not exists mod table')
    with con:
        con.execute("""
CREATE TABLE IF NOT EXISTS mod (
    mod_id uuid NOT NULL PRIMARY KEY,
    name TEXT,
    pak_path path NOT NULL UNIQUE,
    sig_path path NOT NULL UNIQUE,
    enabled bool CHECK (enabled = 0 or enabled = 1)
)
        """)

def _drop_mod_table(con):
    logger.debug('drop mod table')
    with con:
        con.execute("""
DROP TABLE IF EXISTS mod
        """)

def _insert_many_into_mod_table(con, data):
    logger.debug(f'insert into mod table: {data}')
    with con:
        con.executemany("""
INSERT INTO mod (mod_id, name, pak_path, sig_path, enabled)
VALUES (:mod_id, :name, :pak_path, :sig_path, :enabled)
        """, data)

def _delete_many_from_mod_table(con, data):
    logger.debug(f'delete from mod table: {data}')
    with con:
        con.executemany("""
DELETE FROM mod
WHERE mod_id = :mod_id
        """, data)

def _delete_all_from_mod_table(con):
    logger.debug(f'deleting all entries in mod table')
    with con:
        con.execute("""
DELETE FROM mod
        """)

def generate_metadata(dir:pathlib.Path, con):
    paks = dir.glob('**/*.pak')
    params = []
    for path in paks:
        sig_path = path.with_suffix('.sig')
        if not sig_path.exists():
            msg = f'Could not find matching .sig'
            logger.error(msg)
            raise Exception(msg)
        sig_path = sig_path.relative_to(dir)
        pak_path = path.relative_to(dir)
        metadata = ModMetadata(
            mod_id=None, name=path.stem, 
            pak_path=pak_path, sig_path=sig_path,
            enabled=True)
        params.append(metadata.params())
    _insert_many_into_mod_table(con, params)


