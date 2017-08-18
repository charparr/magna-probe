#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-r", "--raw", help="Path to raw MangaProbe data (*.dat)")
parser.add_argument("-b", "--bad", nargs='+', type=int, help="ID #s of bad points, sep. by spaces")
parser.add_argument("-t", "--top", nargs='+', type=int, help="ID #s of over-top points, sep. by spaces")
parser.add_argument("-d", "--deep", nargs='+', type=float, help="Depths of over-top points, sep. by spaces")
parser.add_argument("-c", "--csv", help="Path for cleaned CSV output")
parser.add_argument("-s", "--shp", help="Path for cleaned Shapefile output")
args = parser.parse_args()

# Read in raw MagnaProbe data (*.dat) to a DataFrame and clean columns and headers
data = pd.read_csv(args.raw, header=1)
col_names = []
for col in data.columns:
    col_names.append(col + '_' + str(data[col][0]))
data.columns = col_names
data = data.ix[2::]

# Consolidate coordinate information, rename some columns, and convert depth [cm] to depth [m]
data['latd'] = data['LatitudeDDDDD_nan'].values.astype(float)
data['lat'] = data['latitude_a_degrees'].astype(float)+data['latd']
data['longd'] = data['LongitudeDDDDD_nan'].values.astype(float)
data['lon'] = data['Longitude_a_degrees'].astype(float)+data['longd']
data['Depth_m'] = data['DepthCm_nan'].values.astype(float) / 100.0
data['ID'] = data['Counter_nan'].astype(int)
data['DateTime'] = data['TIMESTAMP_TS']
data['id_check'] = data['ID'].astype(str)
data['id_check'] = data['id_check'].apply(lambda x: x[0:2])

# Remove calibration points (typically sequences of 0-120-0-120-0-120...)
# These are ideally keyed in with a different counter number starting 99...
data = data[data.id_check != str(99)]
# We can also check for the 0-120 sequence in case the operator didn't change the counter to 99:
# But there are lots of variations we should test for (e.g. 0-0-120, 120-0-0, 0-0-0-120, 120-120-0...
# So these patterns look ugly..but they work!
# A-B patterns
calibration1 = (data['Depth_m'] >= 1.19) & (data['Depth_m'].shift(-1) <= 0.02)
calibration2 = (data['Depth_m'] <= 0.02) & (data['Depth_m'].shift(-1) >= 1.19)
calibration3 = (data['Depth_m'] >= 1.19) & (data['Depth_m'].shift(+1) <= 0.02)
calibration4 = (data['Depth_m'] <= 0.02) & (data['Depth_m'].shift(+1) >= 1.19)
# A-A-B patterns
calibration5 = (data['Depth_m'] <= 0.02) & (data['Depth_m'].shift(-1) <= 0.02) & (data['Depth_m'].shift(-2) >= 1.19)
calibration6 = (data['Depth_m'] >= 1.19) & (data['Depth_m'].shift(-1) >= 1.19) & (data['Depth_m'].shift(-2) <= 0.02)
calibration7 = (data['Depth_m'] <= 0.02) & (data['Depth_m'].shift(+1) <= 0.02) & (data['Depth_m'].shift(+2) >= 1.19)
calibration8 = (data['Depth_m'] >= 1.19) & (data['Depth_m'].shift(+1) >= 1.19) & (data['Depth_m'].shift(+2) <= 0.02)
# A-A-A-B patterns
calibration9 = (data['Depth_m'] <= 0.02) & (data['Depth_m'].shift(-1) <= 0.02) & (data['Depth_m'].shift(-2) <= 0.02) &\
 (data['Depth_m'].shift(-3) >= 1.19)
calibration10 = (data['Depth_m'] >= 1.19) & (data['Depth_m'].shift(-1) >= 1.19) & (data['Depth_m'].shift(-2) >= 1.19) &\
 (data['Depth_m'].shift(-3) <= 0.02)
calibration11 = (data['Depth_m'] <= 0.02) & (data['Depth_m'].shift(+1) <= 0.02) & (data['Depth_m'].shift(+2) <= 0.02) &\
 (data['Depth_m'].shift(+3) >= 1.19)
calibration12 = (data['Depth_m'] >= 1.19) & (data['Depth_m'].shift(+1) >= 1.19) & (data['Depth_m'].shift(+2) >= 1.19) &\
 (data['Depth_m'].shift(+3) <= 0.02)
# Boolean for entire set of calibration patterns
calibration_patterns = calibration1 | calibration2 | calibration3 | calibration4 |\
                       calibration5 | calibration6 | calibration7 | calibration8 |\
                       calibration9 | calibration10 | calibration11 | calibration12
# Drop the rows that match MagnaProbe calibration patterns
data = data.drop(data[calibration_patterns].index)

# Slice the columns of interest (position, depth, time, ID)
data = data[['ID', 'lat', 'lon', 'DateTime', 'Depth_m']]

# Print the Head and Tail so the user can check the data
print("First 10 Measurements...")
print(data.head(10))
print("Last 10 Measurements...")
print(data.tail(10))

# We also need to remove the occasional bad point (accidental button press, etc.)
# These are recorded in the field book and provided as a CLI argument by counter ID
if args.bad:
    data = data[~data['ID'].isin(args.bad)]

# We also may need to edit points where the snow depth was greater than 1.2 m (the MagnaProbe max)
# And replace them with a new depth if we measured one
# This info is provided as two separate CLI arguments, the ID and the new depth
if args.top:
    for i, d in zip(args.top, args.deep):
        data.set_value(data[data['ID'] == i].index, 'Depth_m', d / 100.0)

# Create lat lon coordinates
data['geometry'] = data.apply(lambda x: Point((float(x.lon), float(x.lat))), axis=1)

# Transfer information to a GeoDataFrame
geo_df = gpd.GeoDataFrame(data, geometry='geometry', crs='epsg:4326')
print("Depth [m] Summary Statistics...")
print(geo_df['Depth_m'].describe())
# Write the Outputs
if args.csv:
    print("Writing .csv...")
    geo_df.to_csv(args.csv)
if args.shp:
    print("Writing ShapeFile...")
    geo_df.to_file(args.shp)
print("Complete.")
