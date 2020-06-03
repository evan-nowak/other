#!/usr/bin/env python3

"""
#########################
Create Database Column
#########################

:Description:
    Add a column to a database table

:Usage:
    Called from other scripts

"""

from generic.get_params import get_params


def create_new_column(db_table, col_name, col_type, *args, **kwargs):
    """
    :Description:
    Add a column to a database table

    :Params:
    db_table: Database table name
        type: str
    col_name: Name of the new column
        type: str
    col_type: Datatype of the new column
        type: str

    :Returns:
    Nothing, creates new column in database table if it doesn't exist

    :Dependencies:
    Python3
    psycopg2

    :Example:
    create_new_column('some_table', 'new_col', 'integer')
    """

    import psycopg2

    params = get_params(*args, **kwargs)

    # Assemble the database metadata
    conn_str = "host='{0}' dbname='{1}' port='{2}' user='{3}' password='{4}'".format(params['host'],
                                                                                     params['database'],
                                                                                     params['port'],
                                                                                     params['username'],
                                                                                     params['password'])

    base_command = '''SELECT * FROM ''' + params['schema']

    # Create the database query
    command = base_command + '."{0}" ADD COLUMN IF NOT EXISTS "{1}" {2}'.format(db_table, col_name, col_type)

    # Connect to the database
    conn = psycopg2.connect(conn_str)
    cursor = conn.cursor()

    # Execute the command
    cursor.execute(command)

    conn.commit()


if __name__ == '__main__':

    print(__doc__)
