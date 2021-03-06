import geopandas as gpd
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-w", "--wgs", help="Path to WGS data")
parser.add_argument("-e", "--epsg", help="UTM EPSG Code, e.g. UTM 6N = 32606")
parser.add_argument("-u", "--utm", help="Export Path for UTM data")

args = parser.parse_args()
gdf = gpd.read_file(args.wgs)
epsg_str = 'epsg:' + str(args.epsg)
gdf_utm = gdf.to_crs({'init': epsg_str})

gdf_utm.to_file(args.utm)
gdf_utm.to_csv(args.utm[:-3]+'csv')
