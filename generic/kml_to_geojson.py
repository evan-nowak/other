#!/usr/bin/etv python

"""
#########################
KML to GeoJSON
#########################

Purpose
--- Convert a KML file to a GeoJSON file

Usage
--- Run as needed

Dependencies
--- Python3
--- bs4

Args
--- fn (str): Name of the KML file
        default: bus_stop_zones

Kwargs
--- out_fn (str): Name of the GeoJSON to save
        default: None (changes .KML to .TXT)

Output
--- Creates a GeoJSON file

"""


def kml_to_geojson(fn='bus_stop_zones', out_fn=None):

    import re
    from bs4 import BeautifulSoup

    # Load the KML file
    with open(fn.rstrip('.kml') + '.kml') as infile:
        kml = infile.read()

    # kml = re.sub(r'(<!\[CDATA\[)(.*?)(\]\]>)', r'\2', kml)

    kml = kml.replace('<![CDATA[', '')
    kml = kml.replace(']]</name>', '</name>')

    # Parse KML file with BeautifulSoup
    soup = BeautifulSoup(kml, 'lxml')

    # Header and footer code
    header = '{\n"type": "FeatureCollection",\n"features":\n[\n'
    footer = '\n]\n}'

    # generic zone code
    stop_code = '{\n"type": "Feature",\n"geometry":\n{\n"type": "{{{FEATURETYPE}}}",\n"coordinates":\n{{{BRACKET1}}}\n{{{COORDS}}}\n{{{BRACKET2}}}\n},\n"properties":\n{\n"name": "{{{NAME}}}"\n}\n}'

    names, coords, stops = [], [], []

    # Find data for each stop
    for p in soup.find_all('placemark'):

        # Find stop name
        n = p.find_all('name')[0].text

        # Find stop zone coordinates
        c = p.find_all('coordinates')[0].text.strip().split()

        # Format coordinates
        c = ['[' + i + ']' for i in c]
        c = ','.join(c)

        # Check feature type
        if len(p.find_all('polygon')) > 0:
            feature_type = 'Polygon'
            bracket_count = 2
        elif len(p.find_all('linestring')) > 0:
            feature_type = 'LineString'
            bracket_count = 1
        elif len(p.find_all('point')) > 0:
            feature_type = 'Point'
            bracket_count = 1
        else:
            continue

        # Plug name and coordinates into generic stop code
        temp = stop_code.replace('{{{COORDS}}}', c)
        temp = temp.replace('{{{NAME}}}', n)
        temp = temp.replace('{{{FEATURETYPE}}}', feature_type)
        temp = temp.replace('{{{BRACKET1}}}', '[' * bracket_count)
        temp = temp.replace('{{{BRACKET2}}}', ']' * bracket_count)

        stops.append(temp)

    # Join stops
    stops = ',\n'.join(stops)

    # Add header and footer to stop code
    geojson = header + stops + footer

    # If out_fn is None, use fn
    if out_fn is None:
        out_fn = fn

    # Write GeoJSON file
    with open(out_fn.rstrip('.kml') + '.txt', 'w') as outfile:
        outfile.write(geojson)


if __name__ == '__main__':

    kml_to_geojson('C:/Users/enowak/downloads/20200421 - JFK Shuttles.kml')
