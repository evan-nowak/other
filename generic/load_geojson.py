#!/usr/bin/etv python

"""

#########################
Load GeoJSON
#########################

Purpose:
--- Load and process GeoJSON file
--- Convert coordinates from lat / lon to Web Mercator

Usage:
--- Called from other functions

Parameters:
--- filename (GeoJSON filename)

Output:
--- y, x (lists of coordinates in Web Mercator format)

Dependencies:
--- Python3
--- numpy
--- pandas

"""

import math
import numpy as np


def load_file(filename):

    with open(filename) as infile:
        return infile.readlines()


def process_file(lines):

    coords = []
    for l in lines:
        temp = l.strip().strip(',')
        try:
            if temp != '0':
                coords.append(float(temp))
        except:
            pass

    return coords[1::2], coords[::2]


def convert_coords(lat, lon):

    y = np.asarray([lat2y(i) for i in lat])
    x = np.asarray([lon2x(i) for i in lon])

    return y, x


def lat2y(a, radius=6378137.0):

    return math.log(math.tan(math.pi / 4 + math.radians(a) / 2)) * radius


def lon2x(a, radius=6378137.0):

    return math.radians(a) * radius


def load_geojson(filename):

    lines = load_file(filename)

    lat, lon = process_file(lines)

    y, x = convert_coords(lat, lon)

    return y, x


if __name__ == '__main__':

    print(__doc__)
