#!/usr/bin/env python3

"""
#########################
Update Internal Status Dashboard
#########################

:Description:
    Updates the internal status dashboard database table with the current status of the script

:Usage:
    Called from other scripts

"""

from generic.get_params import get_params


def update_internal_status_db(script, location, flag, description, date=None, db_table='internal_status_dashboard',
                              *args, **kwargs):
    """
    :Description:
    Pushes new status to the internal status dashboard database table
    Removes old status from the table

    :Params:
    script: Name of the script
        type: str
    location: Location of the script
        type: str
    flag: Did the script trip a flag?
        type: bool
    description: Description of the flag
        type: str
    date: Date/time that the script was run
        type: str
        default: None
    db_table: Name of the database table
        type: str
        default: internal_status_dashboard
    date_col: Name of the date column
        type: str
        default: date_time
    returns: Nothing, updates the internal status dashboard database table

    :Dependencies:
    Python3
    pandas

    :Example:
    update_internal_status_db('automation/waze/some_script', 'VM1', True, 'Something went wrong...script failed')
    """

    from time import gmtime, strftime
    from datetime import datetime
    from psycopg2 import connect

    params = get_params(*args, **kwargs)

    # Grab the current UTC date
    if date is None:
        date = gmtime()
        date = strftime('%Y-%m-%d %H:%M:%S', date)
        date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

    print(date)

    # Convert the flag to a string
    if flag:
        flag = 'FLAG'
    else:
        flag = ''

    # Assemble the database metadata
    conn_str = "host='{0}' dbname='{1}' port='{2}' user='{3}' password='{4}'".format(params['host'],
                                                                                     params['database'],
                                                                                     params['port'],
                                                                                     params['username'],
                                                                                     params['password'])

    # Connect to database
    conn = connect(conn_str)
    cursor = conn.cursor()

    command = '''SELECT COUNT(*) FROM ''' + \
              "{0}.\"{1}\" WHERE \"location\" LIKE '{2}' AND script LIKE '{3}'".format(params['schema'], db_table,
                                                                                       location, script)

    cursor.execute(command)
    conn.commit()

    records = cursor.fetchall()
    num = records[0][0]

    # Will fail if script doesn't exist in table yet
    if num == 1:
        # Update flag
        command = '''UPDATE ''' + '{0}."{1}" SET "flag"'.format(params['schema'], db_table) + \
                  " = '{0}' WHERE \"location\" LIKE '{1}' AND script LIKE '{2}'".format(flag, location, script)

        cursor.execute(command)
        conn.commit()

        # Update description
        command = '''UPDATE ''' + '{0}."{1}" SET "description"'.format(params['schema'], db_table) + \
                  " = '{0}' WHERE \"location\" LIKE '{1}' AND script LIKE '{2}'".format(description, location, script)

        cursor.execute(command)
        conn.commit()

        # Update date_time
        command = '''UPDATE ''' + '{0}."{1}" SET "date_time"'.format(params['schema'], db_table) + \
                  " = '{0}' WHERE \"location\" LIKE '{1}' AND script LIKE '{2}'".format(date, location, script)

        # Execute command
        cursor.execute(command)
        conn.commit()

    elif num == 0:
        print('script doesnt exist yet')
        from generic.to_db import to_db
        import pandas as pd

        df = pd.DataFrame({'script': script, 'date_time': date, 'location': location, 'flag': flag,
                           'description': description}, index=[0])

        # Push new status to database
        to_db(df, db_table)

    conn.close()


if __name__ == '__main__':

    print(__doc__)
