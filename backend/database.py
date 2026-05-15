from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor

from backend.config import DATABASE_URL

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
)
"""


def init_db() -> None:
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_USERS_TABLE)
        conn.commit()


@contextmanager
def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_cursor(dict_cursor: bool = False):
    factory = RealDictCursor if dict_cursor else None
    with get_connection() as conn:
        with conn.cursor(cursor_factory=factory) as cur:
            yield conn, cur
