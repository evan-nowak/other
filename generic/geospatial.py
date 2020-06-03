#!/usr/bin/env python3

"""
#########################
Geospatial
#########################

:Description:
    Collection of geospatial functions

:Usage:
    Called from other scripts

:To-Do:
    Add function to calculate radius of Earth, given latitude

"""

import math
import numpy as np


def get_xy_coords(geometry, coord_type):
    """
    Returns either x or y coordinates from  geometry coordinate sequence. Used with LineString and Polygon geometries.
    """

    if coord_type == 'x':
        return geometry.coords.xy[0]
    elif coord_type == 'y':
        return geometry.coords.xy[1]


def get_poly_coords(geometry, coord_type):
    """
    Returns Coordinates of Polygon using the Exterior of the Polygon.
    """
    ext = geometry.exterior
    return get_xy_coords(ext, coord_type)


def get_coords(row, geom_col, coord_type):
    """
    Returns coordinates ('x' or 'y') of a geometry (Point, LineString or Polygon) as a list
    (if geometry is LineString or Polygon).
    Can handle also MultiGeometries.
    """
    # Get geometry
    geom = row[geom_col]

    # Check the geometry type
    gtype = geom.geom_type

    # "Normal" geometries
    # -------------------

    if gtype == "Point":
        return get_point_coords(geom, coord_type)
    elif gtype == "LineString":
        return list(get_line_coords(geom, coord_type))
    elif gtype == "Polygon":
        return list(get_poly_coords(geom, coord_type))

    # Multi geometries
    # ----------------

    else:
        return list(multi_geom_handler(geom, coord_type, gtype))


def get_line_coords(geometry, coord_type):
    """ Returns Coordinates of Linestring object."""
    return get_xy_coords(geometry, coord_type)


def get_point_coords(geometry, coord_type):
    """ Returns Coordinates of Point object."""
    if coord_type == 'x':
        return geometry.x
    elif coord_type == 'y':
        return geometry.y


def multi_geom_handler(multi_geometry, coord_type, geom_type):
    """
    Function for handling multi-geometries. Can be MultiPoint, MultiLineString or MultiPolygon.
    Returns a list of coordinates where all parts of Multi-geometries are merged into a single list.
    Individual geometries are separated with np.nan which is how Bokeh wants them.
    # Bokeh documentation regarding the Multi-geometry issues can be found here (it is an open issue)
    # https://github.com/bokeh/bokeh/issues/2321
    """

    for i, part in enumerate(multi_geometry):
        # On the first part of the Multi-geometry initialize the coord_array (np.array)
        if i == 0:
            if geom_type == "MultiPoint":
                coord_arrays = np.append(get_point_coords(part, coord_type), np.nan)
            elif geom_type == "MultiLineString":
                coord_arrays = np.append(get_line_coords(part, coord_type), np.nan)
            elif geom_type == "MultiPolygon":
                coord_arrays = np.append(get_poly_coords(part, coord_type), np.nan)
        else:
            if geom_type == "MultiPoint":
                coord_arrays = np.concatenate([coord_arrays, np.append(get_point_coords(part, coord_type), np.nan)])
            elif geom_type == "MultiLineString":
                coord_arrays = np.concatenate([coord_arrays, np.append(get_line_coords(part, coord_type), np.nan)])
            elif geom_type == "MultiPolygon":
                coord_arrays = np.concatenate([coord_arrays, np.append(get_poly_coords(part, coord_type), np.nan)])

    # Return the coordinates
    return coord_arrays


def lat_to_y(a, radius=6378137.0):
    """
    :Description:
    Convert latitude to Web Mercator (y)

    :Params:
    a: Latitude
        type: int/float
    radius: Radius of the Earth at latitude
        type: float
        default: 6378137.0 (NYC)

    :Returns:
    String in snake_case
        type: float

    :Dependencies:
    Python3

    :Example:
    y = lat_to_y(40.700700)
    """

    return math.log(math.tan(math.pi / 4 + math.radians(a) / 2)) * radius


def lon_to_x(a, radius=6378137.0):
    """
    :Description:
    Convert latitude to Web Mercator (y)

    :Params:
    a: Latitude
        type: int/float
    radius: Radius of the Earth at latitude
        type: float
        default: 6378137.0 (NYC)

    :Returns:
    String in snake_case
        type: float

    :Dependencies:
    Python3

    :Example:
    y = lat_to_y(40.700700)
    """

    return math.radians(a) * radius


def l2x(x):
    """
    Wrapper function for lon_to_x
    """

    for row in x:
        try:
            return np.asarray([lon_to_x(i) for i in row])
        except:
            return lon_to_x(row)


def l2y(x):
    """
    Wrapper function for lat_to_y
    """

    for row in x:
        try:
            return np.asarray([lat_to_y(i) for i in row])
        except:
            return lat_to_y(row)


def to_x(x):
    """
    Vectorizes l2x
    """

    f = np.vectorize(l2x)

    return f(x.values)


def to_y(x):
    """
    Vectorizes l2y
    """

    f = np.vectorize(l2y)

    return f(x.values)


def to_xy(row, coord='lat'):
    if coord == 'lat':
        try:
            return np.asarray([lat_to_y(i) for i in row])
        except:
            return lat_to_y(row)
    else:
        try:
            return np.asarray([lon_to_x(i) for i in row])
        except:
            return lon_to_x(row)


def calculate_earth_radius(B):
    r1 = 6378.137  # equator
    r2 = 6356.752  # poles
    return np.sqrt(
        ((r1 ** 2 * np.cos(B)) ** 2 + (r2 ** 2 * np.sin(B)) ** 2) / ((r1 * np.cos(B)) ** 2 + (r2 * np.sin(B)) ** 2))


def haversine(loc1, loc2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """

    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(np.radians, [loc1[0], loc1[1], loc2[0], loc2[1]])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))

    B = np.mean([lat1, lat2])

    r = calculate_earth_radius(B)

    return c * r


def calculate_length(x):
    x = np.array(x.coords)

    dists = 0
    for i in range(1, len(x)):
        dists += haversine(x[i][:2], x[i - 1][:2])

    return dists


if __name__ == '__main__':
    print(__doc__)
