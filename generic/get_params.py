#!/usr/bin/env python3

"""
#########################
Get Params
#########################

:Description:
    Loads the database parameters

:Usage:
    Called from other scripts

"""


def get_params(param_file='db_params.txt', user_file=None, param_loc=None, user_loc=None, *args, **kwargs):
    """
    :Description:
    Load the database parameters from file

    :Params:
    param_file: Name of database parameter file
        type: str
        default: db_params.txt
    param_loc: Location of database parameter file
        type: str
        default: None
    returns: Database parameters
        type: dict
        format:{'host': 'host',
                'database': 'database',
                'schema': 'schema',
                'port': 'port'}

    :Dependencies:
    Python3
    psycopg2

    :Notes:
    param_loc defaults to home directory

    :Example:
    params = get_params(param_loc='/home/admin/params')
    """

    import os

    if param_loc is None:
        param_loc = os.path.expanduser('~')

    with open(os.path.join(param_loc, param_file)) as infile:
        params = infile.read().strip()

    params = params.split('\n')
    params = {i.split('\t')[0].strip(): i.split('\t')[1].strip() for i in params}

    # if user is specified, use that user 
    if user_file is not None:
        user = get_user(user_file=user_file, user_loc=user_loc)
        params.update(user)

    return params


def get_user(user_file='db_user.txt', user_loc=None):
    """
    :Description:
    Load the database username/password from file

    :Params:
    user_file: Name of database username/password file
        type: str
        default: db_user.txt
    user_loc: Location of database username/password file
        type: str
        default: None
    returns: Database username/password
        type: dict
        format:{'username': 'username',
                'password': 'password'}

    :Dependencies:
    Python3
    psycopg2

    :Notes:
    user_loc defaults to home directory

    :Example:
    user = get_user(user_loc='/home/admin/params')
    """

    import os

    if user_loc is None:
        user_loc = os.path.expanduser('~')

    with open(os.path.join(user_loc, user_file)) as infile:
        params = infile.read().strip()

    params = params.split('\n')
    params = {i.split('\t')[0].strip(): i.split('\t')[1].strip() for i in params}

    return params


if __name__ == '__main__':

    print(__doc__)
