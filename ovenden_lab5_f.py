import numpy as np
import os
import rasterio 
from rasterio.plot import show, show_hist
import glob
import scipy
from lab5functions import *
import pandas as pd


in_data_dir = r'C:\Users\mmbur\OneDrive\Documents\GEOG5092 - Automation and Programming\lab5\data'
os.chdir(in_data_dir)
forest_dir =('L5_Big_Elk/')

files = sorted(os.listdir(forest_dir))
files = [i for i in files if i.endswith('.tif')]
b3s = [forest_dir+i for i in files if i.endswith('B3.tif')]
b4s = [forest_dir+i for i in files if i.endswith('B4.tif')]


with rasterio.open(in_data_dir + './corpuschristi_dem.tif', 'r') as dem_file:
    dem = dem_file.read(1)
    dem_profile = dem_file.profile
    #calculates the slope and aspect using the DEM with a cell size of 30
    s,a = slopeAspect(dem, 30)
    #recalculates the aspect to 8 cardinal directions using the fuction 
    aspect = reclassAspect(a)
    #using a bin size of 10, recalculate the slope grid into 10 classes using the function
    s = reclassByHisto(s, 10)
    #print(s,a)
    dem_profile
    
    

#calculate the NDVI for all years of analysis from landsat images
#calculate the recover ratio for each pixel for each year
#use ravel or flatten, then vstack, then polyfit

with rasterio.open(in_data_dir + './fire_perimeter.tif') as fire_ras:
    fire_arr = fire_ras.read(1)
    fire_profile = fire_ras.profile
    aspectBurn= np.where(fire_arr == 1, a, np.nan)
    slopeBurn = np.where(fire_arr ==1, s, np.nan)


rrs = []
for i in range(len(b3s)):
    with rasterio.open(b3s[i]) as b3_ras:
        b3 = b3_ras.read(1).astype(np.float32)
    with rasterio.open(b4s[i]) as b4_ras:
        b4 = b4_ras.read(1).astype(np.float32)
    ndvi = (b4 - b3) / (b4 + b3)
    ndviforMean = ndvi[fire_arr ==2].mean()
    rr= ndvi/ndviforMean
    print(rr[fire_arr ==1].mean())
    rrs.append(rr.flatten())

ndviSlp = np.zeros_like(rrs[0])
xs = range(10)
for px in range(rrs[0].size):
    ys = [p[px] for p in rrs]
    ndviSlp[px] = scipy.polyfit(xs, ys, 1)[0]
outStack = np.vstack(rrs)
fit = scipy.polyfit(range(10), outStack, 1)[0]
ndviSlp=fit.reshape(b3.shape)
print('mean RR:' , ndviSlp[fire_arr ==1].mean())
ndviSlp[fire_arr!=1]=np.nan

def ZonalStats(zone_raster, value_raster, output_csv):
    
    max_stats = []
    mean_stats = []
    min_stats = []
    count_stats = []
    std_stats = []
    
    for u in np.unique(zone_raster):
        ras = np.where(zone_raster == u, np.nan)

        min_stats.append(np.nanmin(ras * value_raster))
        max_stats.append(np.nanmax(ras * value_raster))
        mean_stats.append(np.nanmean(ras * value_raster))
        std_stats.append(np.nanstd(ras * value_raster))
        count_stats.append(np.where(value_raster > 0, 1, 0).sum())

    zonal_stats = {'Count': count_stats, 'Mean': mean_stats, 'Stdev': std_stats, 'Min': min_stats, 'Max': max_stats}
    df = pd.DataFrame(zonal_stats)
    df.to_csv(output_csv)
    return df
    

ZonalStats(ndviSlp, aspectBurn, "slp.csv")
ZonalStats(ndviSlp, slopeBurn, "aspect.csv")

fire_profile['nodata'] = -99
fire_profile['dtype'] = np.float64
with rasterio.open('coefficient_recovery.tif', 'w', **fire_profile) as ds:
    ds.write_band(1, ndviSlp)