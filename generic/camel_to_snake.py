#!/usr/bin/env python3

"""
#########################
Camel to Snake
#########################

:Description:
    Convert string from CamelCase to snake_case

:Usage:
    Called from other scripts

"""


def camel_to_snake(s):
    """
    :Description:
    Load data from database

    :Params:
    s: String in CamelCase
        type: str

    :Returns:
    s: String in snake_case
        type: str

    :Dependencies:
    Python3

    :Example:
    s = camel_to_snake('DateTime')
    """

    import re

    s = re.sub('([A-Z]{1})', r'_\1', s).lower().strip('_')

    return s


if __name__ == '__main__':

    print(__doc__)
