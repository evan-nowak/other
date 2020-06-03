#!/usr/bin/env python3

"""
#########################
Load Data
#########################

:Description:
    Load data from the database

:Usage:
    Called from other scripts

"""

from generic.get_params import get_params


def load_data(db_table=None, start=None, end=None, date_col='date_time', chunk_size=100000,
              time_zone='America/New_York', *args, **kwargs):
    """
    :Description:
    Load data from database

    :Params:
    db_table: Database table name
        type: str
        default: None
    start: Start date[time]
        type: str
        default: None
        format: YYYY-MM-DD [HH:MM:SS]
    end: End date[time]
        type: str
        default: None
        format: YYYY-MM-DD [HH:MM:SS]
    date_col: Datetime column
        type: str
        default: date_time
    chunk_size: Number of rows to load at a time
        type: int
        default: 100000

    :Returns:
    df: Data from given table for specified time frame
        type: pandas DataFrame

    :Dependencies:
    Python3
    psycopg2

    :Notes:
    If start is not given, all data before end will be loaded
    If end is not given, all data after start will be loaded
    If neither start nor end are given, all data will be loaded

    :Example:
    load_data(db_table='some_table', start='2019-01-01')
    """

    import psycopg2
    import pandas as pd

    params = get_params(*args, **kwargs)

    base_command = '''SELECT * FROM ''' + '{0}."{1}"'.format(params['schema'], db_table)

    # Create the database query
    if start is None and end is None:
        pass
    elif start is None:
        base_command = base_command + ' WHERE "{1}" < \'{2} {3}\''.format(db_table, date_col, end, time_zone)
    elif end is None:
        base_command = base_command + ' WHERE "{1}" >= \'{2} {3}\''.format(db_table, date_col, start, time_zone)
    else:
        base_command = base_command + ' WHERE "{1}" >= \'{2} {4}\' AND "{1}" < \'{3} {4}\''.format(db_table, date_col,
                                                                                                start, end, time_zone)

    # Assemble the database metadata
    conn_str = "host='{0}' dbname='{1}' port='{2}' user='{3}' password='{4}'".format(params['host'],
                                                                                     params['database'],
                                                                                     params['port'],
                                                                                     params['username'],
                                                                                     params['password'])

    # Connect to the database
    conn = psycopg2.connect(conn_str)
    cursor = conn.cursor()

    # Grab the first row from the database table
    # Needed to get the column names
    cursor.execute(base_command + ' LIMIT 1'.format(db_table))
    col_names = [desc[0] for desc in cursor.description]

    df = pd.DataFrame()

    # Iterate through the database rows
    # Needed if the query selection is too large to fit in the RAM
    n = 0
    while True:
        # Add LIMIT and OFFSET to the command
        command = base_command + " LIMIT " + str(chunk_size) + " OFFSET " + str(n * chunk_size)

        # Execute the command
        cursor.execute(command)
        records = cursor.fetchall()

        temp = pd.DataFrame(records)

        # Breaks when finished
        try:
            temp.columns = col_names
        except ValueError:
            break

        df = df.append(temp)

        n += 1

    del temp

    # Convert date column to datetime format
    try:
        df[date_col] = pd.to_datetime(df[date_col], infer_datetime_format=True)
    except:
        pass

    if df.empty:
        df = pd.DataFrame(columns=col_names)

    return df


if __name__ == '__main__':

    print(__doc__)
