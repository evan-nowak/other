#!/usr/bin/etv python

"""
#########################
GTFS to GeoJSON
#########################

Purpose
--- Convert GTFS files to GeoJSON

Usage
--- Run as needed

Dependencies
--- Python3
--- pandas

Kwargs
--- folder_in (str): Folder containing GTFS files
        default: input
--- folder_out (str): Folder to save GeoJSON files
        default: output

Output
--- Creates GeoJSON files

"""

import os
import pandas as pd


def get_files(folder_in='input'):

    fs = os.listdir(folder_in)
    fs = {i.split('.')[0]: i for i in fs}
    
    return fs


def load_files(fs, folder_in='input'):
    
    dfs = {}
    
    for f in fs:
        dfs[f] = pd.read_csv('/'.join([folder_in, fs[f]]), low_memory=False)

    return dfs


def transform_shapes(shapes):

    temp = []
    for key, grp in shapes.groupby('shape_id'):
        coords = grp.sort_values('shape_pt_sequence')[['shape_pt_lon', 'shape_pt_lat']].values
        temp.append({'shape_id': key, 'coords': coords})

    shapes = pd.DataFrame(temp)

    shapes.index = shapes.shape_id

    shapes = shapes.coords

    return shapes


def transform_stops(stops):

    stops['coords'] = list(stops[['stop_lon', 'stop_lat']].values)

    stops.drop(['stop_lon', 'stop_lat'], axis=1, inplace=True)

    return stops


def transform_routes(routes):
    
    routes.rename(columns={'route_color': 'stroke'}, inplace=True)
    routes.stroke = '#' + routes.stroke.str.lstrip('#')
    
    return routes


def map_coords(trips, routes, shapes):

    trips['coords'] = trips.shape_id.map(shapes)

    temp = trips.copy()
    temp.drop_duplicates(subset=['route_id'], inplace=True)
    temp.index = temp.route_id

    routes['coords'] = routes.route_id.map(temp.coords)

    return trips, routes


def convert_to_geojson(df):

    header = '{\n"type": "FeatureCollection",\n"features":\n[\n'
    footer = '\n]\n}'

    feat_code = '{\n"type": "Feature",\n"geometry":\n{\n"type": "{{{TYPE}}}",\n"coordinates":\n{{{COORDS}}}\n},\n"properties":\n{\n{{{PROPS}}}\n}\n}'

    prop_code = '"prop": "{{{PROP}}}"'

    cols = list(df.columns)
    cols.remove('coords')

    dd = df.copy()

    dd.dropna(subset=['coords'], axis=0, inplace=True)
    
    dd.fillna('', inplace=True)

    for c in cols:
        dd[c] = dd[c].astype(str)

    dd.coords = dd.coords.apply(lambda x: ''.join(str(x.tolist()).split()))

    dd = dd.T.to_dict()

    feats = []

    for i in dd:

        props = []

        for c in cols:
            prop = prop_code.replace('prop', c)
            prop = prop.replace('{{{PROP}}}', dd[i][c])

            props.append(prop)

        props = ',\n'.join(props)

        feat = feat_code.replace('{{{PROPS}}}', props)
        feat = feat.replace('{{{COORDS}}}', dd[i]['coords'])

        if dd[i]['coords'][1] == '[':
            feat_type = 'LineString'
        else:
            feat_type = 'Point'

        feat = feat.replace('{{{TYPE}}}', feat_type)

        feats.append(feat)

    feats = ',\n'.join(feats)

    geojson = header + feats + footer
    
    return geojson


def save_files(jsons, folder_out='output'):
    
    for i in jsons:
        with open('/'.join([folder_out, i]) + '.geojson', 'w') as outfile:
            outfile.write(jsons[i])


def gtfs_to_geojson(folder_in='input', folder_out='output'):
    
    print('getting filenames')
    fs = get_files(folder_in)
    
    print('loading files')
    dfs = load_files(fs, folder_in)
    
    print('transforming data')
    dfs['shapes'] = transform_shapes(dfs['shapes'])
    dfs['stops'] = transform_stops(dfs['stops'])
    dfs['routes'] = transform_routes(dfs['routes'])
    
    print('mapping data')
    dfs['trips'], dfs['routes'] = map_coords(dfs['trips'], dfs['routes'], dfs['shapes'])
    
    print('converting to json')
    jsons = {}
    jsons['routes'] = convert_to_geojson(dfs['routes'])
    jsons['stops'] = convert_to_geojson(dfs['stops'])
    
    print('saving files')
    save_files(jsons, folder_out)
    
    print('\ndone')
    

if __name__ == '__main__':
    gtfs_to_geojson()
