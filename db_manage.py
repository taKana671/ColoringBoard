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


def get_names():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        names = [r[0] for r in conn.execute(SELECT_NAMES)]

    return names


def insert_data(data_p, data_v, data_f):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        conn.execute(PRAGMA_FOREIGN_KEY)

        insert_polyhedrons = 'INSERT INTO polyhedrons (id, name) VALUES (?, ?)'
        conn.executemany(insert_polyhedrons, data_p)
        insert_vertices = 'INSERT INTO vertices (id, row_num, vertex) VALUES (?, ?, ?)'
        conn.executemany(insert_vertices, data_v)
        insert_faces = 'INSERT INTO faces (id, row_num, face) VALUES (?, ?, ?)'
        conn.executemany(insert_faces, data_f)

        conn.commit()


def create_tables():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        conn.execute(PRAGMA_FOREIGN_KEY)

        for sql in (CREATE_POLYHEDRONS_TABLE, CREATE_VERTICES_TABLE, CREATE_FACES_TABLE):
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

SELECT_NAMES = '''
    SELECT name from polyhedrons;
'''

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


if __name__ == '__main__':
    # name = 'Elongated Pentagonal Rotunda'
    # print(get_faces(name))

    # create_tables()
    vertices = [
        (-0.29220218, -0.89930585, 0.32537191),
        (-0.76499524, -0.55580158, 0.32537191),
        (-0.94558612, 0.00000000, 0.32537191),
        (-0.76499524, 0.55580158, 0.32537191),
        (-0.29220218, 0.89930585, 0.32537191),
        (0.29220218, 0.89930585, 0.32537191),
        (0.76499524, 0.55580158, 0.32537191),
        (0.94558612, -0.00000000, 0.32537191),
        (0.76499524, -0.55580158, 0.32537191),
        (0.29220218, -0.89930585, 0.32537191),
        (0.00000000, -0.80436360, -0.17175213),
        (-0.76499524, -0.24856202, -0.17175213),
        (-0.47279306, 0.65074382, -0.17175213),
        (0.47279306, 0.65074382, -0.17175213),
        (0.76499524, -0.24856202, -0.17175213),
        (-0.29220218, -0.40218180, -0.47899169),
        (-0.47279306, 0.15361978, -0.47899169),
        (0.00000000, 0.49712404, -0.47899169),
        (0.47279306, 0.15361978, -0.47899169),
        (0.29220218, -0.40218180, -0.47899169),
    ]
    faces = [
        (0, 1, 11, 15, 10), (0, 10, 9), (0, 9, 8, 7, 6, 5, 4, 3, 2, 1),
        (1, 2, 11), (2, 3, 12, 16, 11), (3, 4, 12), (4, 5, 13, 17, 12),
        (5, 6, 13), (6, 7, 14, 18, 13), (7, 8, 14), (8, 9, 10, 19, 14),
        (10, 15, 19), (11, 16, 15), (12, 17, 16), (13, 18, 17),
        (14, 19, 18), (15, 16, 17, 18, 19)
    ]

    data_v = [('n06', i, item) for i, item in enumerate(vertices)]
    data_f = [('n06', i, item) for i, item in enumerate(faces)]
    data_p = [('n06', 'Pentagonal Rotunda')]


    # data_v = [('n21', i, item) for i, item in enumerate(vertices)]
    # data_f = [('n21', i, item) for i, item in enumerate(faces)]
    # data_p = [('n21', 'Elongated Pentagonal Rotunda')]
    
    insert_data(data_p, data_v, data_f)

    