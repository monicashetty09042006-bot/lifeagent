import os, pathlib, sqlite3
from contextlib import closing

HERE = pathlib.Path(__file__).resolve().parent
DB_PATH = os.getenv("DB_PATH", str(HERE.parent / "lifeagent.db"))

def conn():
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c

def q(sql, args=(), one=False):
    with closing(conn()) as c:
        rows = [dict(r) for r in c.execute(sql, args).fetchall()]
    return (rows[0] if rows else None) if one else rows

def x(sql, args=()):
    with closing(conn()) as c:
        cur = c.execute(sql, args)
        c.commit()
        return cur.lastrowid

def init():
    with closing(conn()) as c:
        c.executescript((HERE / "schema.sql").read_text())
        c.commit()
    if not q("SELECT id FROM users LIMIT 1"):
        from .seed import seed
        seed()
