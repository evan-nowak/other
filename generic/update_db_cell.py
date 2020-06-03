#!/usr/bin/env python3

"""
#########################
Update Database Cell
#########################

:Description:
    Updates a specific cell of a database table

:Usage:
    Called from other scripts

"""

from generic.get_params import get_params


def update_db_cell(db_table=None, new_value=None, new_column=None, column_values=None, update_all=False, indent='',
                   *args, **kwargs):
    """
    :Description:
    Pushes new status to the internal status dashboard database table
    Removes old status from the table

    :Params:
    db_table: Name of the database table
        type: str
        default: None
    new_value: New value for the cell
        type: str
        default: None
    new_column: Column of the new value
        type: str
        default: None
    column_values: Column names and values to match
        type: dict
        format: {column_name_0: value_0, column_name_1: value_1, ...}
        default: None
    update_all: Update every cell matching column_values?
        type: bool
        default: False
    text:
        type: bool
        default: False
    returns: Nothing, updates the specified cell of a database table

    :Dependencies:
    Python3
    pandas
    psycopg2

    :Notes:
    If new_value is set to None, the row will be deleted

    :Example:
    update_internal_status_db('automation/waze/some_script', 'VM1', True, 'Something went wrong...script failed')
    """

    from psycopg2 import connect

    params = get_params(*args, **kwargs)

    wheres = []

    for i in column_values:
        wheres.append("\"{0}\" = '{1}'".format(i, column_values[i]))

    wheres = ' AND '.join(wheres)

    command = '''SELECT COUNT(*) FROM ''' + '{0}."{1}" WHERE {2}'.format(params['schema'], db_table, wheres)

    # Assemble the database metadata
    conn_str = "host='{0}' dbname='{1}' port='{2}' user='{3}' password='{4}'".format(params['host'],
                                                                                     params['database'],
                                                                                     params['port'],
                                                                                     params['username'],
                                                                                     params['password'])

    # Connect to database
    conn = connect(conn_str)
    cursor = conn.cursor()

    cursor.execute(command)
    conn.commit()

    records = cursor.fetchall()
    num = records[0][0]

    if num == 1:

        if new_value is not None:
            command = '''UPDATE ''' + '{0}."{1}" SET "{2}" = \'{3}\' WHERE {4}'.format(params['schema'], db_table,
                                                                                       new_column, new_value, wheres)
            msg = 'Value updated'
        else:
            command = '''DELETE FROM ''' + '{0}."{1}" WHERE {2}'.format(params['schema'], db_table, wheres)
            msg = 'Row deleted'

        # Execute command
        cursor.execute(command)
        conn.commit()

        print(indent + msg)

    elif num == 0:

        print(indent + 'Location not found')

    elif (num > 1) & update_all:

        if new_value is not None:
            command = '''UPDATE ''' + '{0}."{1}" SET "{2}" = \'{3}\' WHERE {4}'.format(params['schema'], db_table,
                                                                                       new_column, new_value, wheres)
            msg = 'All values updated'
        else:
            command = '''DELETE FROM ''' + '{0}."{1}" WHERE {2}'.format(params['schema'], db_table, wheres)
            msg = 'All rows deleted'

        # Execute command
        cursor.execute(command)
        conn.commit()

        print(indent + msg)

    else:
        print(indent + 'Multiple locations found. Be more specific or set "update_all=True" to update value in all locations.')

    conn.close()


if __name__ == '__main__':

    print(__doc__)
