import sqlite3
from contextlib import closing

import pandas as pd

sqlite3.register_adapter(tuple, lambda x: ','.join(str(i) for i in x))
sqlite3.register_converter('Tuple', lambda x: tuple(i.decode('utf-8') for i in x.split(b',')))


def create_df(sql, params=None):
    with closing(sqlite3.connect('polyhedrons.db')) as conn:
        df = pd.read_sql(sql, conn, params=params)

    return df


def insert_data(data_p, data_v, data_f):
    with closing(sqlite3.connect('polyhedrons.db')) as conn:
        conn.execute(PRAGMA_FOREIGN_KEY)

        insert_polyhedrons = 'INSERT INTO polyhedrons (id, name) VALUES (?, ?)'
        conn.executemany(insert_polyhedrons, data_p)
        insert_vertices = 'INSERT INTO vertices (id, row_num, vertex) VALUES (?, ?, ?)'
        conn.executemany(insert_vertices, data_v)
        insert_faces = 'INSERT INTO faces (id, row_num, face) VALUES (?, ?, ?)'
        conn.executemany(insert_faces, data_f)

        conn.commit()


def create_tables():
    with closing(sqlite3.connect('polyhedrons.db')) as conn:
        conn.execute(PRAGMA_FOREIGN_KEY)

        for sql in (CREATE_POLYHEDRONS_TABLE, CREATE_VERTICES_TABLE, CREATE_FACES_TABLE):
            conn.execute(sql)
        conn.commit()


PRAGMA_FOREIGN_KEY = '''
    PRAGMA foreign_keys = 1
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
        vertex TUPLE,
        PRIMARY KEY(id, row_num),
        FOREIGN KEY(id) REFERENCES polyhedrons(id)
    );
'''

CREATE_FACES_TABLE = '''
    CREATE TABLE IF NOT EXISTS faces (
        id TEXT,
        row_num INTEGER,
        face TUPLE,
        color_pattern
        PRIMARY KEY(id, row_num),
        FOREIGN KEY(id) REFERENCES polyhedrons(id)
    );
'''


if __name__ == '__main__':
    # create_tables()
    vertices = [
        (-0.26010839, -0.80053131, 0.01968437),
        (-0.68097260, -0.49475556, 0.01968437),
        (-0.84172843, 0.00000000, 0.01968437),
        (-0.68097260, 0.49475556, 0.01968437),
        (-0.26010839, 0.80053131, 0.01968437),
        (0.26010839, 0.80053131, 0.01968437),
        (0.68097260, 0.49475556, 0.01968437),
        (0.84172843, 0.00000000, 0.01968437),
        (0.68097260, -0.49475556, 0.01968437),
        (0.26010839, -0.80053131, 0.01968437),
        (0.00000000, -0.71601697, -0.42283845),
        (-0.68097260, -0.22126141, -0.42283845),
        (-0.42086421, 0.57926990, -0.42283845),
        (0.42086421, 0.57926990, -0.42283845),
        (0.68097260, -0.22126141, -0.42283845),
        (-0.26010839, -0.35800848, -0.69633260),
        (-0.42086421, 0.13674707, -0.69633260),
        (0.00000000, 0.44252282, -0.69633260),
        (0.42086421, 0.13674707, -0.69633260),
        (0.26010839, -0.35800848, -0.69633260),
        (-0.26010839, -0.80053131, 0.53990115),
        (0.26010839, -0.80053131, 0.53990115),
        (0.68097260, -0.49475556, 0.53990115),
        (0.84172843, 0.00000000, 0.53990115),
        (0.68097260, 0.49475556, 0.53990115),
        (0.26010839, 0.80053131, 0.53990115),
        (-0.26010839, 0.80053131, 0.53990115),
        (-0.68097260, 0.49475556, 0.53990115),
        (-0.84172843, 0.00000000, 0.53990115),
        (-0.68097260, -0.49475556, 0.53990115),
    ]
    faces = [
        (0, 1, 11, 15, 10), (0, 10, 9), (0, 9, 21, 20), (0, 20, 29, 1),
        (1, 2, 11), (1, 29, 28, 2), (2, 3, 12, 16, 11), (2, 28, 27, 3),
        (3, 4, 12), (3, 27, 26, 4), (4, 5, 13, 17, 12), (4, 26, 25, 5),
        (5, 6, 13), (5, 25, 24, 6), (6, 7, 14, 18, 13), (6, 24, 23, 7),
        (7, 8, 14), (7, 23, 22, 8), (8, 9, 10, 19, 14), (8, 22, 21, 9),
        (10, 15, 19), (11, 16, 15), (12, 17, 16), (13, 18, 17), (14, 19, 18),
        (15, 16, 17, 18, 19), (20, 21, 22, 23, 24, 25, 26, 27, 28, 29)
    ]
    
    data_v = [('n21', i, item) for i, item in enumerate(vertices)]
    data_f = [('n21', i, item) for i, item in enumerate(faces)]
    data_p = [('n21', 'Elongated Pentagonal Rotunda')]
    
    insert_data(data_p, data_v, data_f)
