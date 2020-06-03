#!/usr/bin/env python3

"""
#########################
To DB
#########################

:Description:
    Pushes data to the selected database table

:Usage:
    Called from other scripts

"""


def check_if_table_exists(cursor, schema, db_table):
    command = '''SELECT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = ''' + \
              "'{0}' AND TABLE_NAME = '{1}')".format(schema, db_table)

    cursor.execute(command)

    return cursor.fetchone()[0]


def create_table(df, db_table, params, d_types):
    import sqlalchemy

    engine = sqlalchemy.create_engine('postgresql+psycopg2://{0}:{1}@{2}/{3}'.format(params['username'],
                                                                                     params['password'],
                                                                                     params['host'],
                                                                                     params['database']))

    # Convert data types from string to SQLAlchemy format
    if d_types is not None:
        for i in d_types:
            if d_types[i].lower() == 'bigint':
                d_types[i] = sqlalchemy.BIGINT
            elif d_types[i].lower() == 'binary':
                d_types[i] = sqlalchemy.BINARY
            elif d_types[i].lower() == 'bool':
                d_types[i] = sqlalchemy.BOOLEAN
            elif d_types[i].lower() == 'boolean':
                d_types[i] = sqlalchemy.BOOLEAN
            elif d_types[i].lower() == 'char':
                d_types[i] = sqlalchemy.CHAR
            elif d_types[i].lower() == 'clob':
                d_types[i] = sqlalchemy.CLOB
            elif d_types[i].lower() == 'date':
                d_types[i] = sqlalchemy.DATE
            elif d_types[i].lower() == 'datetime':
                d_types[i] = sqlalchemy.DATETIME
            elif d_types[i].lower() == 'decimal':
                d_types[i] = sqlalchemy.DECIMAL
            elif d_types[i].lower() == 'float':
                d_types[i] = sqlalchemy.FLOAT
            elif d_types[i].lower() == 'integer':
                d_types[i] = sqlalchemy.INTEGER
            elif d_types[i].lower() == 'int':
                d_types[i] = sqlalchemy.INTEGER
            elif d_types[i].lower() == 'json':
                d_types[i] = sqlalchemy.JSON
            elif d_types[i].lower() == 'nchar':
                d_types[i] = sqlalchemy.NCHAR
            elif d_types[i].lower() == 'numeric':
                d_types[i] = sqlalchemy.NUMERIC
            elif d_types[i].lower() == 'nvarchar':
                d_types[i] = sqlalchemy.NVARCHAR
            elif d_types[i].lower() == 'real':
                d_types[i] = sqlalchemy.REAL
            elif d_types[i].lower() == 'smallint':
                d_types[i] = sqlalchemy.SMALLINT
            elif d_types[i].lower() == 'text':
                d_types[i] = sqlalchemy.TEXT
            elif d_types[i].lower() == 'time':
                d_types[i] = sqlalchemy.TIME
            elif d_types[i].lower() == 'timestamp':
                d_types[i] = sqlalchemy.TIMESTAMP
            elif d_types[i].lower() == 'text':
                d_types[i] = sqlalchemy.TEXT
            elif d_types[i].lower() == 'varbinary':
                d_types[i] = sqlalchemy.VARBINARY
            elif d_types[i].lower() == 'varchar':
                d_types[i] = sqlalchemy.VARCHAR

    df.to_sql(db_table, engine, dtype=d_types, schema=params['schema'])


def to_db_new(df, db_table, d_types=None, index=False, chunk_size=None, *args, **kwargs):
    """
    :Description:
    Pushes data to the selected database table

    :Params:
    df: Data
        type: pandas DataFrame
    db_table: The name of the database table
        type: str
    d_types: The datatypes of each column
        type: dict
        default: None
    index: Whether or not to use index
        type: bool
        default: False
    chunk_size: Number of rows to send at a time
        type: int
        default: None
    returns: Nothing, pushes data to database table

    :Dependencies:
    Python3
    sqlalchemy

    :Example:
    to_db_new(df, 'Waze')
    """

    import psycopg2
    import traceback
    from pandas.api.types import is_numeric_dtype
    from generic.get_params import get_params

    params = get_params(*args, **kwargs)

    dd = df.copy()

    if index:
        df.reset_index(inplace=True)

    cols = dd.columns

    for c in cols:
        if is_numeric_dtype(dd[c]):
            dd[c] = dd[c].astype(str)
        else:
            dd[c] = dd[c].astype(str)
            dd[c] = "'" + dd[c] + "'"

    dd = dd.to_numpy()

    # Assemble the database metadata
    conn_str = "host='{0}' dbname='{1}' port='{2}' user='{3}' password='{4}'".format(params['host'],
                                                                                     params['database'],
                                                                                     params['port'],
                                                                                     params['username'],
                                                                                     params['password'])

    try:
        # Connect to database
        conn = psycopg2.connect(conn_str)

        # Create new cursor
        cursor = conn.cursor()

        n = 0
        L = len(dd)
        cols = ', '.join(['"{0}"'.format(i) for i in cols])

        if chunk_size is None:
            chunk_size = L

        exists = check_if_table_exists(cursor, params['schema'], db_table)

        if not exists:
            create_table(df.head(0), db_table, params, d_types)

        command = '''INSERT INTO ''' + '{0}."{1}" ({2}) VALUES ('.format(params['schema'], db_table, cols)

        while n < L:
            # Chunk data and convert to string
            data = "), (".join([", ".join(i) for i in dd[n: n + chunk_size]]) + ')'

            # Execute command
            cursor.execute(command + data)

            n += chunk_size

        # Commit changes to database
        conn.commit()

        # Close connection to database
        cursor.close()

    except:
        print(traceback.format_exc())
    finally:
        # Make sure connection to database is closed
        if conn is not None:
            conn.close()


if __name__ == '__main__':

    print(__doc__)
