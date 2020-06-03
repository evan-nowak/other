#!/usr/bin/env python3

"""
#########################
Visualize Bus Data
#########################

:Description:
    Create interactive heatmap of bus GPS points

:Usage:
    Run on server or locally

"""

import pytz
import numpy as np
import pandas as pd
from time import time
import geopandas as gpd
from datetime import timedelta, datetime

from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.layouts import row, column
from bokeh.models.tiles import WMTSTileSource
from bokeh.models import WheelZoomTool, ColumnDataSource, HoverTool, CrosshairTool, DatetimeTickFormatter, MultiLine, \
    BoxAnnotation, LabelSet, Patches, CustomJS, Span, Dropdown
from bokeh.transform import linear_cmap

from generic.notifier import notifier
from generic.load_data import load_data
from generic.geospatial import get_coords, to_xy, lat_to_y, lon_to_x

pd.set_option('mode.chained_assignment', None)

pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 220)

df_past, df_all, df_past_all = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
p_subset = column(sizing_mode='stretch_both', css_classes=['plot-holder'], name='right', visible=False)
p_lines = {}

today = datetime.now(tz=pytz.timezone('America/New_York'))
today = datetime.strftime(today, '%Y-%m-%d')
today = datetime.strptime(today, '%Y-%m-%d')

tomorrow = today + timedelta(days=1)

here = datetime.now(tz=pytz.timezone('America/New_York'))
here = datetime.strftime(here, '%Y-%m-%d %H')
here = datetime.strptime(here, '%Y-%m-%d %H')
there = datetime.now(pytz.utc)
there = datetime.strftime(there, '%Y-%m-%d %H')
there = datetime.strptime(there, '%Y-%m-%d %H')
diff = there - here

label_time = None


def get_data(first=False, recipients=None):
    if first:

        starts = [datetime.strftime(today - timedelta(days=n), '%Y-%m-%d %H:%M:%S') for n in range(29)][::7]
        ends = [datetime.strftime(today - timedelta(days=n), '%Y-%m-%d %H:%M:%S') for n in range(-1, 28)][::7]

        # GRAB ALL DATA FROM WAZE TABLE

        dfs = []
        for s, e, n in zip(starts[:1], ends[:1], [0]):
            temp = load_data('waze_api', s, e, date_col='Date_Time', time_zone='America/New_York', chunk_size=999999999)

            # temp.Date_Time = temp.Date_Time + pd.Timedelta(weeks=n)
            temp.Date_Time = temp.Date_Time.dt.tz_convert('America/New_York').dt.tz_localize(None)

            if temp.Date_Time.min() < today:
                temp.Date_Time = temp.Date_Time + pd.Timedelta(hours=1)
            elif temp.Date_Time.max() > tomorrow:
                temp.Date_Time = temp.Date_Time - pd.Timedelta(hours=1)

            dfs.append(temp)

        for s, e, n in zip(starts[1:], ends[1:], [1, 2, 3, 4]):
            # temp = load_data('waze_api', s, e, date_col='Date_Time', time_zone='America/New_York', chunk_size=999999999)

            s = ''.join(s.split('-')).split()[0]
            try:
                temp = pd.read_pickle('./data/{0}.pkl'.format(s))
            except:
                notifier(script_name='waze_live',
                         subject='Waze Live',
                         status='Historical data missing: {0}'.format(starts[n].split()[0]),
                         recipients=recipients)
                continue

            temp.Date_Time = temp.Date_Time + pd.Timedelta(weeks=n)
            temp.Date_Time = temp.Date_Time.dt.tz_convert('America/New_York').dt.tz_localize(None)

            if temp.Date_Time.min() < today:
                temp.Date_Time = temp.Date_Time + pd.Timedelta(hours=1)
            elif temp.Date_Time.max() > tomorrow:
                temp.Date_Time = temp.Date_Time - pd.Timedelta(hours=1)

            dfs.append(temp)

        df = dfs[0]
        df_past = pd.concat(dfs[1:], sort=False)

        return df, df_past

    else:

        # GRAB ALL DATA FROM WAZE TABLE

        df = load_data('waze_api', datetime.strftime(today, '%Y-%m-%d %H:%M:%S'), date_col='Date_Time',
                       time_zone='America/New_York', chunk_size=999999999)

        df.Date_Time = df.Date_Time.dt.tz_convert('America/New_York').dt.tz_localize(None)

        return df


def load_shape(fn='waze_routes.txt'):
    folder = '/home/lga_admin/live/'
    folder = ''
    gdf = gpd.read_file(folder + fn)

    gdf.dropna(how='any', inplace=True)

    gdf['geometry'] = gdf['geometry'].to_crs(epsg=4326)

    gdf['x'] = gdf.apply(get_coords, geom_col='geometry', coord_type='x', axis=1)
    gdf['y'] = gdf.apply(get_coords, geom_col='geometry', coord_type='y', axis=1)

    gdf['x'] = gdf['x'].apply(to_xy, coord='lon')
    gdf['y'] = gdf['y'].apply(to_xy, coord='lat')

    gdf.drop('geometry', 1, inplace=True)

    return gdf


def process_routes(gdf):
    gdf['route'] = gdf.name.str.split().str.get(0)

    gdf.route = pd.to_numeric(gdf.route, errors='coerce')

    gdf.dropna(subset=['route'], inplace=True)

    gdf.route = gdf.route.astype(int).astype(str)

    gdf.index = gdf.route

    gdf = gdf[['x', 'y']]

    gdf = gdf[~gdf.index.duplicated(keep='last')]

    return gdf


def get_route_info(zone_file_routes='waze_routes.txt'):

    df = pd.read_excel('LGA.xlsx', skiprows=1)

    df = df[['Waze Segment Name', '#.1', 'Route Length (mi)', 'Waze Live page']]
    df.columns = ['name', 'route', 'length', 'page']

    df.dropna(how='any', inplace=True)

    df.drop_duplicates(subset=['route'], keep='last', inplace=True)

    df_zones = load_shape(zone_file_routes)
    df_zones = process_routes(df_zones)

    df.route = df.route.astype(str)

    df['x'] = df.route.map(df_zones.x)
    df['y'] = df.route.map(df_zones.y)

    df.index = df['route']
    df = df[['name', 'length', 'x', 'y', 'page']]

    return df


def prep_data(df, past=False):
    df = df[['Date_Time', 'ID', 'Route_Time']].copy()

    df.Date_Time = pd.to_datetime(df.Date_Time, infer_datetime_format=True)
    df.ID = df.ID.astype(str)
    df.Route_Time = df.Route_Time.astype(int)

    df = df[df.ID.isin(route_info[selected_subset].index)]

    if past:
        df.rename(columns={'Date_Time': 'date_time', 'ID': 'route', 'Route_Time': 'travel_time_past'}, inplace=True)
        df.travel_time_past = df.travel_time_past.mask(df.travel_time_past < 0)
    else:
        df.rename(columns={'Date_Time': 'date_time', 'ID': 'route', 'Route_Time': 'travel_time'}, inplace=True)
        df.travel_time = df.travel_time.mask(df.travel_time < 0)

    dfs = []
    for key, grp in df.groupby('route'):
        temp = grp.resample('2T', on='date_time').mean().interpolate('pchip')
        temp['route'] = key

        dfs.append(temp)

    df = pd.concat(dfs, sort=False)

    df.reset_index(inplace=True)

    if past:
        df = df[['date_time', 'route', 'travel_time_past']]
    else:
        df = df[['date_time', 'route', 'travel_time']]

    return df


def calculate_speeds(df):
    df['name'] = df.route.map(route_info[selected_subset].name)
    df['length'] = df.route.map(route_info[selected_subset].length)

    df['x'] = df.route.map(route_info[selected_subset].x)
    df['y'] = df.route.map(route_info[selected_subset].y)

    # travel time goes to -1 when route breaks
    # df = df[~df.route.isin(df[df.travel_time < 0].route.unique())]

    df['speed'] = df.length / df.travel_time * 3600
    df['speed_past'] = df.length / df.travel_time_past * 3600

    # df.speed = df.speed.mask(df.speed < 0)
    # df.speed_past = df.speed_past.mask(df.speed_past < 0)

    df['speed_str'] = df.speed.fillna(-1).round().astype(int)
    df.speed_str = np.where(df.speed_str.values > 0, df.speed_str.astype(str).values + 'mph', 'No Data')

    df['speed_past_str'] = df.speed_past.fillna(-1).round().astype(int)
    df.speed_past_str = np.where(df.speed_past_str.values > 0, df.speed_past_str.astype(str).values + 'mph', 'No Data')

    df = df[['route', 'name', 'date_time', 'speed', 'speed_past', 'speed_str', 'speed_past_str', 'x', 'y']]

    df['filler'] = df[['speed', 'speed_past']].mean(axis=1).fillna(0)

    df1 = average_subset(df, 'All routes')

    return df, df1


def find_outliers(df, outlier_limit=.5):

    df['outlier'] = (df.speed_past - df.speed) / df.speed_past

    df.outlier = np.where(df.outlier.fillna(0).values >= .5, 1, 0)

    return df


def initialize_data(first=False, pull_data=True):
    global df_past, df_all, df_past_all

    if first:
        df, df_past = get_data(first)
        df_all, df_past_all = df.copy(), df_past.copy()

        df_past = prep_data(df_past, past=True)
    else:
        if pull_data:
            df = get_data(first)
            df_all = df.copy()
        else:
            df = df_all.copy()
            df_past = df_past_all.copy()

            df_past = prep_data(df_past, past=True)

    df = prep_data(df)

    df = pd.merge(df, df_past, how='outer', on=['route', 'date_time'])

    df, df1 = calculate_speeds(df)

    df = find_outliers(df)

    cur_time = x_loc.data['x'][0] * 1000000

    df_map = df[df.date_time.astype('int64') <= cur_time].dropna(subset=['route', 'name', 'x', 'y', 'speed', 'outlier']).drop_duplicates(keep='last',
                                                                                   subset=['route']).copy()
    df0 = df[['date_time', 'route', 'name', 'speed', 'speed_past', 'speed_str', 'speed_past_str', 'filler']].copy()
    df1 = df1[['date_time', 'route', 'name', 'speed', 'speed_past', 'speed_str', 'speed_past_str', 'filler']]
    df_map = df_map[['route', 'name', 'speed', 'x', 'y', 'outlier']]

    df0 = df0.resample('2T', on='date_time').mean()

    return df, df0, df1, df_map


def create_line_plot(source, r=None, plot_height=None, y_range=None, sizing_mode='scale_width'):
    global time_loc

    if plot_height is None:
        plot_height = 100
        y_range = (0, 40)
        sizing_mode = 'scale_width'

    plot_width = 500

    border_color = '#262626'
    background_color = '#262626'
    grid_color = '#ffffff'
    grid_alpha = .1

    line_width_hist = 3
    line_width_cur = 4
    line_alpha_hist = 1
    line_alpha_cur = 1
    line_dash_cur = 'solid'
    line_dash_hist = 'solid'
    line_cap = 'round'
    line_color_hist = '#000000'
    line_color_cur = '#ffffff'

    box_colors = ['#a10000', '#fcba03', '#00a603']
    box_alpha = .33

    text_color = '#eeeeee'

    if r is None:
        title = 'Average speed on airport'
    else:
        title = route_info[selected_subset].loc[r, 'name']

    title_size = '18pt'
    title_font = 'helvetica'
    title_style = 'bold'
    title_color = 'black'
    title_off = 10

    # xaxis_label = name
    xaxis_size = '8pt'
    xaxis_font = 'helvetica'
    xaxis_style = 'normal'
    xaxis_color = 'black'
    xaxis_off = 10

    yaxis_label = 'mph'
    yaxis_size = '14pt'
    yaxis_font = 'helvetica'
    yaxis_style = 'normal'
    yaxis_color = 'black'
    yaxis_off = 10

    label_xoff = -115
    label_yoff = -10
    label_color = '#ffffff'

    name_x = 0
    name_y = 0
    name_xoff = 0
    name_yoff = 0
    name_color = '#ffffff'
    name_bg_color = '#000000'
    name_bg_alpha = .75
    name_alpha = 1
    name_align = 'left'

    x_range_padding = 10
    x_range = (today - timedelta(minutes=x_range_padding), tomorrow + timedelta(minutes=x_range_padding))

    TOOLS = 'hover,crosshair'

    p = figure(tools=TOOLS, plot_width=plot_width, plot_height=plot_height, toolbar_location=None,
               x_axis_type='datetime', sizing_mode=sizing_mode, css_classes=['plot'], y_range=y_range,
               x_range=x_range)

    low_box = BoxAnnotation(top=5, fill_alpha=box_alpha, fill_color=box_colors[0], line_alpha=0, line_width=0,
                            level='underlay')
    mid_box = BoxAnnotation(bottom=5, top=15, fill_alpha=box_alpha, fill_color=box_colors[1], line_alpha=0,
                            line_width=0, level='underlay')
    high_box = BoxAnnotation(bottom=15, fill_alpha=box_alpha, fill_color=box_colors[2], line_alpha=0, line_width=0,
                             level='underlay')

    p.add_layout(low_box)
    p.add_layout(mid_box)
    p.add_layout(high_box)

    # filler
    g = p.line('date_time', 'filler', line_alpha=0, source=source)

    # historical
    p.line('date_time', 'speed_past', line_width=line_width_hist, line_dash=line_dash_hist, color=line_color_hist,
           line_alpha=line_alpha_hist, source=source)

    # live
    p.line('date_time', 'speed', line_width=line_width_cur, line_dash=line_dash_cur, line_alpha=line_alpha_cur,
           color=line_color_cur, source=source, alpha=1)

    p.add_layout(time_loc)

    p.min_border_left = 10
    p.min_border_right = 10

    if plot_height is None:
        p.border_fill_color = None
        p.outline_line_color = None
    else:
        p.border_fill_color = background_color
        p.outline_line_color = background_color

    p.background_fill_color = background_color
    p.xgrid.grid_line_color = grid_color
    p.ygrid.grid_line_color = grid_color
    p.xgrid.grid_line_alpha = grid_alpha
    p.ygrid.grid_line_alpha = grid_alpha

    p.xaxis[0].formatter = DatetimeTickFormatter(hours=['%H:%M'])
    p.xaxis[0].ticker.desired_num_ticks = 24
    p.xaxis[0].ticker.num_minor_ticks = 4
    # p.x_range.range_padding = 0.015
    p.xaxis.axis_label_text_color = text_color
    p.xaxis.major_label_text_color = text_color
    p.xaxis.major_tick_line_color = text_color
    p.xaxis.minor_tick_line_color = text_color
    p.xaxis.axis_line_color = text_color

    p.y_range.start = 0

    # Title
    p.title.text = title
    p.title.text_font_style = title_style
    p.title.text_color = text_color

    # Y-axis
    p.yaxis.axis_label = yaxis_label
    p.yaxis.axis_label_text_color = text_color
    p.yaxis.major_label_text_color = text_color
    p.yaxis.major_tick_line_color = text_color
    p.yaxis.minor_tick_line_color = text_color
    p.yaxis.axis_label_standoff = yaxis_off
    # p.yaxis.axis_label_text_font = yaxis_font
    p.yaxis.axis_label_text_font_style = yaxis_style
    p.yaxis.axis_line_color = text_color

    # CrosshairTool
    crosshair = p.select(dict(type=CrosshairTool))
    crosshair.dimensions = 'height'
    crosshair.line_color = '#ffffff'
    crosshair.line_alpha = .33

    # HoverTool
    hover = p.select(dict(type=HoverTool))
    hover.renderers = [g]
    hover.mode = 'vline'
    hover.show_arrow = False
    hover.point_policy = 'follow_mouse'
    hover.tooltips = [
        ('Route', '@name'),
        ('Time', '@date_time{%H:%M}'),
        ('Speed (actual)', '@speed_str'),
        ('Speed (historical)', '@speed_past_str')
    ]
    hover.formatters = {'date_time': 'datetime'}

    p.js_on_event('tap', get_x_loc())

    return p


def create_map(source, source_terminals, source_time):

    global label_time

    line_width = 7
    line_alpha = 1
    line_dash = 'solid'
    line_cap = 'square'
    line_join = 'round'
    outline_color = '#ffffff'
    outlier_color = '#fc8803'
    outlier_line_dash = 'solid'
    outlier_line_cap = 'square'

    time_size = '32pt'
    time_x = 0
    time_y = 0
    time_xoff = 0
    time_yoff = 0
    time_color = '#ffffff'
    time_bg_color = '#000000'
    time_bg_alpha = .75
    time_alpha = 1
    time_align = 'left'

    terminal_alpha = .25
    terminal_color = '#ffffff'

    colors = ['#a10000'] * 5 + ['#fcba03'] * 10 + ['#00a603'] * 5
    mapper = linear_cmap('speed', colors, 0, 20)

    ratio = 16 / 6
    zoom = 900

    plot_width = 1600
    plot_height = int(plot_width / ratio)

    tile_url = 'https://tiles.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@%sx.png'
    scale = 2  # 1 - low quality basemap / 2 - normal quality basemap / 4 - high quality basemap

    y_center, x_center = lat_to_y(40.771225), lon_to_x(-73.873578)

    x_range = (x_center - zoom, x_center + zoom)
    y_range = (y_center - zoom / ratio, y_center + zoom / ratio)

    x_range = tuple(int(i) for i in x_range)
    y_range = tuple(int(i) for i in y_range)

    TOOLS = 'pan,wheel_zoom,hover,tap'

    p = figure(tools=TOOLS, plot_width=plot_width, plot_height=plot_height, x_range=x_range, y_range=y_range,
               toolbar_location=None, sizing_mode='stretch_both', css_classes=['map'], name='map')

    tile_url = tile_url % scale
    p.add_tile(WMTSTileSource(url=tile_url, snap_to_zoom=True))

    # terminal shapes
    g0 = p.patches('x', 'y', source=source_terminals, fill_alpha=terminal_alpha, fill_color=terminal_color,
                   line_alpha=0)

    selected = Patches(fill_alpha=terminal_alpha, fill_color=terminal_color, line_alpha=0)
    nonselected = Patches(fill_alpha=terminal_alpha, fill_color=terminal_color, line_alpha=0)

    g0.selection_glyph = selected
    g0.nonselection_glyph = nonselected

    # outlier lines
    g2 = p.multi_line('x', 'y', line_width=line_width + 4, line_dash=outlier_line_dash, line_alpha='outlier', color=outlier_color,
                      source=source, line_cap=outlier_line_cap, line_join=line_join)

    selected = MultiLine(line_alpha='outlier', line_width=line_width + 4, line_color=outlier_color,
                         line_dash=outlier_line_dash, line_cap=outlier_line_cap, line_join=line_join)
    nonselected = MultiLine(line_alpha='outlier', line_width=line_width + 4, line_color=outlier_color,
                            line_dash=outlier_line_dash, line_cap=outlier_line_cap, line_join=line_join)

    g2.selection_glyph = selected
    g2.nonselection_glyph = nonselected

    # outline lines
    g1 = p.multi_line('x', 'y', line_width=line_width, line_dash=line_dash, alpha=0, color=outline_color, source=source,
                      line_cap=line_cap, line_join=line_join)

    selected = MultiLine(line_alpha=1, line_color=outline_color, line_width=line_width + 4, line_cap=line_cap,
                         line_join=line_join)
    nonselected = MultiLine(line_alpha=0, line_color=outline_color, line_width=line_width, line_cap=line_cap,
                            line_join=line_join)

    g1.selection_glyph = selected
    g1.nonselection_glyph = nonselected

    # normal lines
    g = p.multi_line('x', 'y', line_width=line_width, line_dash=line_dash, alpha=line_alpha, color=mapper,
                     source=source, line_cap=line_cap, line_join=line_join)

    selected = MultiLine(line_alpha=1, line_color=mapper, line_width=line_width, line_cap=line_cap, line_join=line_join)
    nonselected = MultiLine(line_alpha=line_alpha, line_color=mapper, line_width=line_width, line_cap=line_cap,
                            line_join=line_join)

    g.selection_glyph = selected
    g.nonselection_glyph = nonselected

    # Display the time on the map
    label_time = LabelSet(x=time_x, y=time_y, source=source_time, text='date_time', x_offset=time_xoff,
                          y_offset=time_yoff, text_color=time_color, text_alpha=time_alpha, text_align=time_align,
                          x_units='screen', y_units='screen', background_fill_color=time_bg_color,
                          background_fill_alpha=time_bg_alpha, text_font_size=time_size)

    p.add_layout(label_time)

    p.background_fill_color = None
    p.border_fill_color = None
    p.outline_line_color = None

    p.axis.visible = False
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    p.toolbar.active_scroll = p.select_one(WheelZoomTool)

    hover = p.select(dict(type=HoverTool))
    hover.show_arrow = False
    hover.renderers = [g1]
    hover.point_policy = 'follow_mouse'
    hover.tooltips = [
        ('Route', '@name'),
        ('Current Speed', '@speed{0f}mph')
    ]

    return p


def initialize_widgets(dropdown_menu, nextbus_menu):
    dropdown = Dropdown(label='Map: Overall', menu=dropdown_menu, css_classes=['dropdown'], button_type='default',
                        width=200, height=30, sizing_mode='fixed')
    dropdown.on_change('value', update_subset)

    nextbus = Dropdown(label='Red Shuttle', menu=nextbus_menu, css_classes=['dropdown'], button_type='default',
                       width=200, height=30, sizing_mode='fixed', visible=False)
    nextbus.on_change('value', update_nextbus)

    return row(dropdown, nextbus, css_classes=['widgets'], sizing_mode='scale_height', name='widgets')


def get_x_loc():
    return CustomJS(args=dict(x_loc=x_loc, time_loc=time_loc, label_time=label_time, end_time=end_time), code="""        
        var x = Math.round(Number(cb_obj["x"]) / 1) * 1;

        if (x > (new Date().getTime() - new Date().getTimezoneOffset() * 60000)) {
          x = end_time;
          a = 0;
          label_time.text_color = '#ffffff';
        } else {
          a = 1;
          label_time.text_color = '#fc8803';
        }

        x_loc.data = {"x": [x]};
        
        time_loc.location = x;
        time_loc.line_alpha = a;
    """)


def average_subset(df, name, routes=None):

    if routes is None:
        df1 = df[['date_time', 'speed', 'speed_past', 'filler']].resample('2T', on='date_time').mean().reset_index()
    else:
        df1 = df[df.route.isin(routes)][['date_time', 'speed', 'speed_past', 'filler']].resample('2T',
                                                                                                 on='date_time').mean().reset_index()
    df1['speed_str'] = df1.speed.fillna(-1).round().astype(int)
    df1.speed_str = np.where(df1.speed_str.values > 0, df1.speed_str.astype(str).values + 'mph', 'No Data')

    df1['speed_past_str'] = df1.speed_past.fillna(-1).round().astype(int)
    df1.speed_past_str = np.where(df1.speed_past_str.values > 0, df1.speed_past_str.astype(str).values + 'mph', 'No Data')

    df1['route'] = 0
    df1['name'] = name

    return df1


def update_data():
    global df, df1

    df, df0, df1, df_map = initialize_data()

    if selected_subset == 'overall':
        if len(selected_routes) == 0:
            df0 = df1.copy()
        elif len(selected_routes) == 1:
            df0 = df[df.route.isin(selected_routes)].copy()
        else:
            route_name = route_info[selected_subset].loc[selected_routes, 'name']
            if not isinstance(route_name, str):
                route_name = ' + '.join(route_name.values)
            df0 = average_subset(df, route_name, selected_routes)

    else:
        df0 = df.copy()

    source.data.update({
        'date_time': df0.date_time.values,
        'speed': df0.speed.values,
        'speed_past': df0.speed_past.values,
        'speed_str': df0.speed_str.values,
        'filler': df0.filler.values,
        'speed_past_str': df0.speed_past_str.values,
        'route': df0.route.values,
        'name': df0.name.values
    })
    source_map.data.update({
        'speed': df_map.speed.values,
        # 'speed_past': df_map.speed_past.values,
        'route': df_map.route.values,
        'name': df_map.name.values,
        'x': df_map.x.values,
        'y': df_map.y.values,
        'outlier': df_map.outlier.values
    })
    if selected_subset != 'overall':
        for r in df_map.route.unique():
            temp = df0[df0.route == r]
            selected_cds[r].data.update({
                'date_time': temp.date_time.values,
                'speed': temp.speed.values,
                'speed_past': temp.speed_past.values,
                'speed_str': temp.speed_str.values,
                'filler': temp.filler.values,
                'speed_past_str': temp.speed_past_str.values,
                'route': temp.route.values,
                'name': temp.name.values
            })

    time_str = datetime.now(pytz.timezone('America/New_York')).timestamp()
    time_str = datetime.fromtimestamp(min(time_str, x_loc.data['x'][0] / 1000 + diff.total_seconds()),
                                      tz=pytz.timezone('America/New_York'))
    time_str = datetime.strftime(time_str, '%H:%M:%S')

    source_time.patch({'date_time': [(0, time_str)]})


def update_timestamp():

    with open('./timestamp.txt', 'w') as outfile:
        outfile.write(str(int(time())))


def update_visibility():
    return CustomJS(args=dict(fig=p_subset), code="""
        if (fig.visible) {
            var visibility = "block";
        } else {
            var visibility = "None";
        }
        document.getElementById('right').style.display = visibility;
    """)


route_info = get_route_info()

route_info = dict(
    overall=route_info[route_info.page.str.contains('main')].copy(),
    ta=route_info[route_info.page.str.contains('TA')].copy(),
    tb=route_info[route_info.page.str.contains('TB')].copy(),
    tc=route_info[route_info.page.str.contains('TC')].copy(),
    sr=route_info[route_info.page.str.contains('SR')].copy(),
    sb=route_info[route_info.page.str.contains('SB')].copy(),
    sp=route_info[route_info.page.str.contains('SP')].copy(),
    tsb=route_info[route_info.page.str.contains('TSB')].copy(),
    tsc=route_info[route_info.page.str.contains('TSC')].copy(),
    tsd=route_info[route_info.page.str.contains('TSD')].copy()
)

selected_subset = 'overall'

end_time = tomorrow.timestamp() * 1000
x_loc = ColumnDataSource({'x': [end_time]})

time_loc = Span(location=x_loc.data['x'][0], dimension='height', line_width=3, line_color='#fc8803', line_alpha=0)

df, df0, df1, df_map = initialize_data(True)

selected_routes = []
selected_cds = {}

df0 = df1.copy()

source = ColumnDataSource(df0)
source_map = ColumnDataSource(df_map)

source_terminals = ColumnDataSource(load_shape('terminals.txt'))

source_time = ColumnDataSource(
    {'date_time': [datetime.strftime(datetime.now(pytz.timezone('America/New_York')), '%H:%M:%S')]})

source.remove('index')
source_map.remove('index')


def update_selection(attr, old, new):
    global selected_routes

    selected_routes = source_map.data['route'][new]

    if selected_subset == 'overall':

        if len(selected_routes) == 0:
            route_name = 'Average speed on airport'
            df0 = df1.copy()
        elif len(selected_routes) == 1:
            route_name = route_info[selected_subset].loc[selected_routes, 'name']
            if not isinstance(route_name, str):
                route_name = ' + '.join(route_name.values)
            df0 = df[df.route.isin(selected_routes)].copy()
        else:
            route_name = route_info[selected_subset].loc[selected_routes, 'name']
            if not isinstance(route_name, str):
                route_name = ' + '.join(route_name.values)
            df0 = average_subset(df, route_name, selected_routes)

        source.data.update({
            'date_time': df0.date_time.values,
            'speed': df0.speed.values,
            'speed_past': df0.speed_past.values,
            'speed_str': df0.speed_str.values,
            'filler': df0.filler.values,
            'speed_past_str': df0.speed_past_str.values,
            'route': df0.route.values,
            'name': df0.name.values
        })

        p_average.title.text = route_name

    else:

        if len(selected_routes) == 0:
            p_subset.children = [p_lines[i] for i in sorted(df_map.route.unique())]

        else:
            p_subset.children = [p_lines[i] for i in selected_routes[::-1]]


def update_map(attr, old, new):
    global df_map

    cur_time = new['x'][0] * 1000000

    df_map = df[df.date_time.astype('int64') <= cur_time].dropna().drop_duplicates(keep='last', subset=['route']).copy()
    df_map = df_map[['route', 'name', 'speed', 'speed_past', 'x', 'y', 'outlier']]

    source_map.data.update({
        'speed': df_map.speed.values,
        'route': df_map.route.values,
        'name': df_map.name.values,
        'x': df_map.x.values,
        'y': df_map.y.values,
        'outlier': df_map.outlier.values
    })

    time_str = datetime.now(pytz.timezone('America/New_York')).timestamp()
    time_str = datetime.fromtimestamp(min(time_str, x_loc.data['x'][0] / 1000 + diff.total_seconds()),
                                      tz=pytz.timezone('America/New_York'))
    time_str = datetime.strftime(time_str, '%H:%M:%S')

    source_time.patch({'date_time': [(0, time_str)]})


def update_subset(attr, old, new):
    global selected_subset, df, df1, p_lines, df_map

    if (old == 'overall') & (new != 'overall'):
        p_average.visible = False
    elif (old != 'overall') & (new == 'overall'):
        p_average.visible = True

    # change title of dropdown
    widgets.children[0].label = 'Map: ' + dropdown_dict[new]

    # change subset of routes
    selected_subset = new

    # reset subset of line plots
    p_lines = {}
    p_subset.children = p_subset.children[:0]

    df, df0, df1, df_map = initialize_data(pull_data=False)

    if new == 'overall':
        df0 = df1.copy()
    else:
        df0 = df.copy()

    source.data.update({
        'date_time': df0.date_time.values,
        'speed': df0.speed.values,
        'speed_past': df0.speed_past.values,
        'speed_str': df0.speed_str.values,
        'filler': df0.filler.values,
        'speed_past_str': df0.speed_past_str.values,
        'route': df0.route.values,
        'name': df0.name.values
    })

    source_map.data.update({
        'speed': df_map.speed.values,
        'route': df_map.route.values,
        'name': df_map.name.values,
        'x': df_map.x.values,
        'y': df_map.y.values,
        'outlier': df_map.outlier.values
    })

    if new in nextbus_dict.keys():
        widgets.children[1].visible = True
    else:
        widgets.children[1].visible = False

    if new == 'overall':
        p_average.visible = True
        p_subset.visible = False

    else:
        p_average.visible = False

        # create line plots for each route in subset
        for r in sorted(df_map.route.unique()):

            temp = df0[df0.route == r]

            selected_cds[r] = ColumnDataSource({
                'date_time': temp.date_time.values,
                'speed': temp.speed.values,
                'speed_past': temp.speed_past.values,
                'speed_str': temp.speed_str.values,
                'filler': temp.filler.values,
                'speed_past_str': temp.speed_past_str.values,
                'route': temp.route.values,
                'name': temp.name.values
            })

            p_lines[r] = create_line_plot(selected_cds[r], r)
            p_subset.children += [p_lines[r]]

        p_subset.visible = True

    # reset map selection
    source_map.selected.indices = []


def update_nextbus(attr, old, new):
    global selected_subset, df, df1, p_lines, df_map

    # change title of dropdown
    widgets.children[1].label = nextbus_dict[new]

    # change subset of routes
    selected_subset = new

    # reset subset of line plots
    p_lines = {}
    p_subset.children = p_subset.children[:0]

    df, df0, df1, df_map = initialize_data(pull_data=False)

    df0 = df.copy()

    source.data.update({
        'date_time': df0.date_time.values,
        'speed': df0.speed.values,
        'speed_past': df0.speed_past.values,
        'speed_str': df0.speed_str.values,
        'filler': df0.filler.values,
        'speed_past_str': df0.speed_past_str.values,
        'route': df0.route.values,
        'name': df0.name.values
    })

    source_map.data.update({
        'speed': df_map.speed.values,
        'route': df_map.route.values,
        'name': df_map.name.values,
        'x': df_map.x.values,
        'y': df_map.y.values,
        'outlier': df_map.outlier.values
    })

    # create line plots for each route in subset
    for r in sorted(df_map.route.unique()):

        temp = df0[df0.route == r]

        selected_cds[r] = ColumnDataSource({
            'date_time': temp.date_time.values,
            'speed': temp.speed.values,
            'speed_past': temp.speed_past.values,
            'speed_str': temp.speed_str.values,
            'filler': temp.filler.values,
            'speed_past_str': temp.speed_past_str.values,
            'route': temp.route.values,
            'name': temp.name.values
        })

        p_lines[r] = create_line_plot(selected_cds[r], r)
        p_subset.children += [p_lines[r]]

    # reset map selection
    source_map.selected.indices = []


dropdown_menu = [
    ('Overall', 'overall'),
    ('Terminal A', 'ta'),
    ('Terminal B', 'tb'),
    ('Terminal C/D', 'tc'),
    ('NextBus', 'sr')
]
dropdown_dict = dict([i[::-1] for i in dropdown_menu])

nextbus_menu = [
    ('Red Shuttle', 'sr'),
    ('Blue Shuttle', 'sb'),
    ('Purple Shuttle', 'sp'),
    ('Taxi Shuttle - Terminal B', 'tsb'),
    ('Taxi Shuttle - Terminal C', 'tsc'),
    ('Taxi Shuttle - Terminal D', 'tsd')
]
nextbus_dict = dict([i[::-1] for i in nextbus_menu])

widgets = initialize_widgets(dropdown_menu, nextbus_menu)

p_map = create_map(source_map, source_terminals, source_time)
p_average = create_line_plot(source, plot_height=50)

source_map.selected.on_change('indices', update_selection)

p_subset.js_on_change('visible', update_visibility())

x_loc.on_change('data', update_map)

# c = column(widgets, p_average, p_map, sizing_mode='stretch_both', css_classes=['left-side'], name='left')
# curdoc().add_root(c)

top = column(widgets, p_average, sizing_mode='stretch_both', css_classes=['top'], name='top')

curdoc().add_root(top)
curdoc().add_root(p_map)

curdoc().add_root(p_subset)

curdoc().add_periodic_callback(update_data, 30 * 1000)
curdoc().add_periodic_callback(update_timestamp, 15 * 60 * 1000)

curdoc().title = 'Waze Live'
