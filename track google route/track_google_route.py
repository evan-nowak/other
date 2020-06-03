#!/usr/bin/env python3

"""
#########################
Track Google Route
#########################

:Description:
    Gets historical data from Google API for specified route

:Usage:
    Called as needed

"""

import pandas as pd


def load_routes(fn, sheet):
    """
    :Description:
    Gets travel time information using Google Directions API

    :Params:
    fn: Name of the file that has the route data
        type: str
    sheet: Name of the sheet that has the routes
        type: str
    returns:
        type: dict

    :Dependencies:
    Python3
    pandas

    :Example:
    load_routes('some_routes.xlsx', 'the_route_sheet')
    """

    # Load the file
    df = pd.read_excel(fn, sheet_name=sheet)

    return df


def format_data(df):

    # Drop the first column
    df = df.iloc[:, 1:]

    d = {}

    # Format data
    for c in df.columns:
        temp = df[c]

        # Generate name from Origin / Destination / Route
        name = '{0}_{1}'.format(temp[0], temp[1]).replace(' ', '')

        # Via
        via = temp[2]

        # Remove Origin / Destination / Route
        temp = temp.dropna()[3:].tolist()

        # Get Origin / Destination coordinates
        temp_o = temp.pop(0)
        temp_d = temp.pop()

        # Generate waypoints code from waypoint coordinates
        if len(temp) > 0:
            temp = 'via:' + '|via:'.join(temp)
        else:
            temp = ''

        try:
            d[name].append([via, temp_o, temp_d, temp])
        except KeyError:
            d[name] = []
            d[name].append([via, temp_o, temp_d, temp])

    return d


def get_travel_time(key, orig, dest, wps, dep_time, mod='driving', avd='ferries', trafmod='best_guess'):
    """
    :Description:
    Gets travel time information using Google Directions API

    :Params:
    orig: Origin as lat/long string
        type: str
        format: 40.1234, -73.1234
    dest: Destination as lat/long string
        type: str
        format: 40.1234, -73.1234
    wps: Waypoints as series of lat/long strings
        type: str
        format: via:40.1234, -73.1234|via:40.1234, -73.1234|via:40.1234, -73.1234
    mod: Travel mode (driving, transit, walking, bicycling)
        type: str
        default: driving
    avd: Avoid (ferries, tolls, highways, indoor)
        type: str
        default: ferries
    trafmod: Traffic model (best_guess, pessimistic, optimistic)
        type: str
        default: best_guess
    returns: Results of request - distance (mi), usual travel time (mins), and actual travel time (mins)
        type: tuple
        format: (distance, usual travel time, actual travel time)

    :Dependencies:
    Python3
    googlemaps

    :Example:
    get_travel_time(key, orig, dest, wps)
    """

    import googlemaps

    gmaps = googlemaps.Client(key=key)

    directions_result = gmaps.directions(orig, dest, waypoints=wps, mode=mod, avoid=avd, traffic_model=trafmod,
                                         departure_time=dep_time)

    # Get values
    distance = directions_result[0]['legs'][0]['distance']['value']                 # Distance (meters)
    duration = directions_result[0]['legs'][0]['duration']['value']                 # Usual time (seconds)
    traffic = directions_result[0]['legs'][0]['duration_in_traffic']['value']       # Time in Traffic (seconds)

    # Convert units
    distance = round(distance * 0.00062137, 2)      # Convert meters to miles
    duration = round(duration / 60, 2)              # Convert seconds to minutes
    traffic = round(traffic / 60, 2)                # Convert seconds to minutes

    return distance, duration, traffic


def track_google_route(key, fn, sheet, all_times):

    route = load_routes(fn, sheet)

    route.fillna('', inplace=True)

    route = route[['full_name', 'start', 'end', 'midpoints']]

    data = {'BBNR': route.values}

    # data = format_data(route)

    # data = {'Brooklyn': [
    #     ['B20', '40.665460, -73.867520', '40.657010, -73.889340', 'via:40.665330, -73.868450|'
    #                                                               'via:40.665190, -73.869380|'
    #                                                               'via:40.665070, -73.870610|'
    #                                                               'via:40.663650, -73.873930|'
    #                                                               'via:40.662940, -73.875570|'
    #                                                               'via:40.661530, -73.878840']
    # ]}

    for d in data:

        print(d)

        dfs = []

        cols = []

        for i in data[d]:

            print('\t' + i[0])

            temp = pd.DataFrame()

            temp_cols = [i[0] + j for j in ['_distance', '_usual_time', '_actual_time']]
            cols.extend(temp_cols)

            for dep_time in all_times:

                # Convert date time to string
                time_str = datetime.strftime(dep_time, '%Y-%m-%d %H:%M:%S')

                results = get_travel_time(key, i[1], i[2], i[3], dep_time)

                temp = temp.append(pd.DataFrame({i[0] + '_distance': results[0], i[0] + '_usual_time': results[1],
                                                 i[0] + '_actual_time': results[2]}, index=[time_str]))

            dfs.append(temp)

        df = pd.concat(dfs, axis=1)

        df = df[cols]

        fn_out = 'C:/Users/enowak/OneDrive - Sam Schwartz Engineering/projects/brooklyn_bus_network/google_speeds/output/' + d + '.xlsx'

        fn_out = fn_out.replace('&', '')

        df.to_excel(fn_out)


if __name__ == '__main__':

    from datetime import datetime, timedelta

    start = '2021-05-15 00:00'
    start = datetime.strptime(start, '%Y-%m-%d %H:%M')

    times = [start + timedelta(hours=1)*i for i in range(24)]

    all_times = []
    for i in [0, 1, 3]:
        for t in times:
            all_times.append(t + timedelta(days=i))

    key = 'AIzaSyCI_hjpO2lBFlubAikgtgxrEGy1DqOWRYo'

    fn = 'C:/Users/enowak/OneDrive - Sam Schwartz Engineering/projects/brooklyn_bus_network/google_speeds/BBNR - Google API inputs.xlsx'
    sheet = 'new_data'

    track_google_route(key, fn, sheet, all_times)
