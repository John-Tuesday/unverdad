import pathlib
import sqlite3
import uuid

sqlite3.register_converter('bool', lambda b: False if int(b) == 0 else True)
sqlite3.register_adapter(bool, lambda b: 1 if b else 0)
sqlite3.register_converter('path', lambda b: pathlib.Path(b.decode()))
sqlite3.register_adapter(pathlib.PosixPath, lambda p: p.as_posix())
sqlite3.register_converter('uuid', lambda b: uuid.UUID(bytes=b))
sqlite3.register_adapter(uuid.UUID, lambda p: p.bytes)

__dbs = {}

def get_db(db, **kwargs):
    return __dbs.setdefault(
        db, 
        sqlite3.connect(
            db, 
            autocommit=False, 
            detect_types=sqlite3.PARSE_DECLTYPES,
            **kwargs)
    )

def _new_uuid() -> uuid.UUID:
    return uuid.uuid4()
