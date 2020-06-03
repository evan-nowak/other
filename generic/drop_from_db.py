#!/usr/bin/env python

"""
#########################
Drop Database Entries
#########################

:Description:
    Drop records from specified database table

:Usage:
    Called from other scripts

"""

from generic.get_params import get_params


def drop_from_db(db_table=None, date_col='date_time', pre_date=None, post_date=None, *args, **kwargs):
    """
    :Description:
    Drops all entries between the start/end dates from the specified database table

    :Params:
    db_table: The name of the database table
        type: str
        default: None
    date_col: The name of the date column
        type: str
        default: None
    pre_date: The starting date
        type: str
        format: YYYY-MM-DD
        default: None
    post_date: The ending date
        type: str
        format: YYYY-MM-DD
        default: None
    returns: Nothing

    :Dependencies:
    Python3
    psycopg2

    :Notes:
    Will grab all data if start/end dates are not specified

    :Example:
    drop_from_db(db_table='Waze', date_col='Date_Time', start='2018-01-01', end='2018-02-01')
    """

    import psycopg2

    params = get_params(*args, **kwargs)

    print('{0}\n{1}\t-\t{2}\n'.format(db_table, pre_date, post_date))

    # Build command
    if (pre_date is None) and (post_date is None):
        command = '''DELETE FROM ''' + '{0}."{1}"'.format(params['schema'], db_table)
    elif pre_date is None:
        command = '''DELETE FROM ''' + '{0}."{1}" WHERE "{2}" < \'{3}\''.format(params['schema'], db_table, date_col,
                                                                                post_date)
    elif post_date is None:
        command = '''DELETE FROM ''' + '{0}."{1}" WHERE "{2}" >= \'{3}\''.format(params['schema'], db_table, date_col,
                                                                                 pre_date)
    else:
        command = '''DELETE FROM ''' + '{0}."{1}" WHERE "{2}" >= \'{3}\' AND "{2}" < \'{4}\''.format(params['schema'],
                                                                                                     db_table,
                                                                                                     date_col,
                                                                                                     pre_date,
                                                                                                     post_date)

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
