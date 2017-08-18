import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.pylab as pylab
import argparse
from scipy import ndimage


parser = argparse.ArgumentParser()
parser.add_argument("-p", "--probe", help="Path to MagnaProbe file to plot")
args = parser.parse_args()

pylab.rcParams['figure.figsize'] = 16, 10
probes = gpd.read_file(args.probe)

probes.plot(column='Depth_m', markersize=7, cmap='coolwarm')
plt.show()


def heatmap(d, bins=(100,100), smoothing=1.3, cmap='coolwarm'):
    def getx(pt):
        return pt.coords[0][0]

    def gety(pt):
        return pt.coords[0][1]

    x = list(d.geometry.apply(getx))
    y = list(d.geometry.apply(gety))
    heatmap, xedges, yedges = np.histogram2d(y, x, bins=bins)
    extent = [yedges[0], yedges[-1], xedges[-1], xedges[0]]

    logheatmap = np.log(heatmap)
    logheatmap[np.isneginf(logheatmap)] = 0
    logheatmap = ndimage.filters.gaussian_filter(logheatmap, smoothing, mode='nearest')

    plt.imshow(logheatmap, cmap=cmap, extent=extent)
    plt.colorbar()
    plt.gca().invert_yaxis()
    plt.show()

heatmap(probes, bins=50, smoothing=1.5)

probes['Depth_m'].plot()
plt.show()