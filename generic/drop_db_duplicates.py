#!/usr/bin/env python

"""
#########################
Drop Database Duplicates
#########################

:Description:
Drop duplicate records from specified database table


"""

from generic.get_params import get_params


def drop_duplicates_from_db(db_table=None, groupby_cols=None, keep_last=True, *args, **kwargs):
    """
    :Description:
    Drop duplicate records from specified database table

    :Params:
    db_table: Name of the database table
        type: str
        default: None
    groupby_cols: list of columns to check for duplicates
        type: list
        default: None
    keep_last: keep the last duplicated entry?
        type: bool
        default: True
    returns: Nothing

    :Dependencies:
    Python3
    psycopg2

    :Example:
    drop_duplicates_from_db(db_table='Waze', groupby_cols=['ID', 'Date_Time'], keep_last=True)
    """

    import psycopg2

    params = get_params(*args, **kwargs)

    # Make sure the type is list
    if type(groupby_cols) == list:
        cols = '", "'.join(groupby_cols)
    else:
        cols = '", "'.join([groupby_cols])

    if keep_last:
        keep = 'MAX'
    else:
        keep = 'MIN'

    # Build command
    command = '''DELETE FROM ''' + '{0}."{1}" WHERE ctid NOT IN (SELECT {2}(ctid) FROM {0}."{1}" ' \
                                   'GROUP BY "{3}");'.format(params['schema'], db_table, keep, cols)

    # Assemble the database metadata
    conn_str = "host='{0}' dbname='{1}' port='{2}' user='{3}' password='{4}'".format(params['host'],
                                                                                     params['database'],
                                                                                     params['port'],
                                                                                     params['username'],
                                                                                     params['password'])

    # Connect to database
    conn = psycopg2.connect(conn_str)
    cursor = conn.cursor()

    # Execute command
    cursor.execute(command)
    conn.commit()


if __name__ == '__main__':

    print(__doc__)
