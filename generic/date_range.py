#!/usr/bin/env python

"""
#########################
Date Range
#########################

:Description:
    Generates a date range based on starting/ending dates and/or number of days

:Usage:
    Called from other scripts

:Notes:
    The function needs exactly two of the three arguments to work
    When providing the start and end dates, both will be in the resulting list

"""


def date_range(start=None, end=None, day_count=None):
    """
    :Description:
    Generates a date range
    Generates a date range using two of the following: starting date, ending date, day count

    :Params:
    start: The starting date
        type: str
        format: YYYY-MM-DD
        default: None
    end: The ending date
        type: str
        format: YYYY-MM-DD
        default: None
    day_count: The number of days in the range
        type: int
        default: None
    returns: Range of dates in ascending order
        type: list

    :Dependencies:
    Python3

    :Notes:
    The function needs exactly two of the arguments to work

    :Example:
    date_range(start='2018-01-01', end='2018-02-01')
    """

    from datetime import datetime, timedelta

    # If start is provided, validate format
    if start is not None:
        try:
            start = datetime.strptime(start, '%Y-%m-%d')
        except Exception:
            raise Exception('Please provide dates in the following format: YYYY-MM-DD')

    # If end is provided, validate format
    if end is not None:
        try:
            end = datetime.strptime(end, '%Y-%m-%d')
        except Exception:
            raise Exception('Please provide dates in the following format: YYYY-MM-DD')

    # If day_count is provided, validate format
    if day_count is not None:
        try:
            day_count = int(day_count)
        except Exception:
            raise Exception('Day count must be a number')

    # Create date range using start/end dates
    if (start is not None) and (end is not None) and (day_count is None):
        dates = [datetime.strftime(start + timedelta(days=n), '%Y-%m-%d') for n in range(int((end - start).days) + 1)]

    # Create date range using start date and day count
    elif (start is not None) and (day_count is not None) and (end is None):
        dates = [datetime.strftime(start + timedelta(days=n), '%Y-%m-%d') for n in range(day_count)]

    # Create date range using end date and day count
    elif (end is not None) and (day_count is not None) and (start is None):
        dates = [datetime.strftime(end - timedelta(days=n), '%Y-%m-%d') for n in range(day_count)][::-1]

    else:
        raise Exception('Please provide exactly 2 arguments')

    print('{0} - {1}'.format(dates[0], dates[-1]))

    return dates


if __name__ == '__main__':

    print(__doc__)
