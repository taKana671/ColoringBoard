import sqlite3
from contextlib import closing


DB_NAME = 'polyhedrons.db'


sqlite3.register_adapter(tuple, lambda x: ','.join(str(i) for i in x))
sqlite3.register_converter('INTTUPLE', lambda x: tuple(int(i) for i in x.split(b',')))
sqlite3.register_converter('FLOATTUPLE', lambda x: tuple(float(i) for i in x.split(b',')))


def _get_data(sql, name):
    with closing(sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES)) as conn:
        for r in conn.execute(sql, (name,)):
            yield r[0]


def get_vertices(name):
    vertices = [v for v in _get_data(SELECT_VERTEX, name)]
    return vertices


def get_faces(name):
    faces = [f for f in _get_data(SELECT_FACE, name)]
    return faces


def get_items():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        items = {r[0]: r[1] for r in conn.execute(SELECT_ITEMS)}

    return items


def get_sub_items(prefix):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        names = [r[0] for r in conn.execute(SELECT_SUB_ITEMS, (prefix + '%',))]

    return names


def insert_data(sql, data):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        conn.execute(PRAGMA_FOREIGN_KEY)
        conn.executemany(sql, data)
        conn.commit()


def create_tables():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        conn.execute(PRAGMA_FOREIGN_KEY)

        for sql in (CREATE_POLYHEDRONS_TABLE, CREATE_VERTICES_TABLE,
                    CREATE_FACES_TABLE, CREATE_ITEMS_TABLE):
            conn.execute(sql)
        conn.commit()


SELECT_FACE = '''
    SELECT face
    FROM faces as f
    INNER JOIN polyhedrons AS p ON f.id = p.id
    WHERE p.name = ?
    ORDER BY f.row_num;
'''

SELECT_VERTEX = '''
    SELECT vertex
    FROM vertices as v
    INNER JOIN polyhedrons AS p ON v.id = p.id
    WHERE p.name = ?
    ORDER BY v.row_num;
'''

SELECT_ITEMS = '''
    SELECT name, id FROM items;
'''

SELECT_SUB_ITEMS = '''
    SELECT name FROM polyhedrons
    WHERE id like ?
'''

PRAGMA_FOREIGN_KEY = '''
    PRAGMA foreign_keys = 1
'''

CREATE_ITEMS_TABLE = '''
    CREATE TABLE IF NOT EXISTS items (
        id TEXT PRIMARY KEY,
        name TEXT UNIQUE
    );
'''

CREATE_POLYHEDRONS_TABLE = '''
    CREATE TABLE IF NOT EXISTS polyhedrons (
        id TEXT PRIMARY KEY,
        name TEXT
    );
'''

CREATE_VERTICES_TABLE = '''
    CREATE TABLE IF NOT EXISTS vertices (
        id TEXT,
        row_num INTEGER,
        vertex FLOATTUPLE,
        PRIMARY KEY(id, row_num),
        FOREIGN KEY(id) REFERENCES polyhedrons(id)
    );
'''

CREATE_FACES_TABLE = '''
    CREATE TABLE IF NOT EXISTS faces (
        id TEXT,
        row_num INTEGER,
        face INTTUPLE,
        PRIMARY KEY(id, row_num),
        FOREIGN KEY(id) REFERENCES polyhedrons(id)
    );
'''

INSERT_POLYHEDRONS = 'INSERT INTO polyhedrons (id, name) VALUES (?, ?)'
INSERT_VERTICES = 'INSERT INTO vertices (id, row_num, vertex) VALUES (?, ?, ?)'
INSERT_FACES = 'INSERT INTO faces (id, row_num, face) VALUES (?, ?, ?)'


if __name__ == '__main__':
    create_tables()