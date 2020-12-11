import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, Point, LineString
import os
import glob
from rasterstats import zonal_stats
import fiona
import numpy as np
import random
import sys

#working with vector geometery and sampling
data_file = r'C:\Users\mmbur\OneDrive\Documents\GEOG5092 - Automation and Programming\lab3\lab3_data\lab3.gpkg' 
#assign the layers to a variable so that you can reuse it, in order to separate the files within the geopackage, you need to set up a condition
layers = fiona.listlayers(data_file) 
#print(layers)
#ssurgo_poly = [f for f in layers if f.startswith('ssurgo')]
watershed_list = [f for f in layers if f.startswith('wdbhu')]
random.seed(0)

#use bounds to limit coordinate generation and then check to see if coordinate is inside of polygon
#generate random point then check to see if its within polygon
#bounds is your square, check to see if your point falls within polygon until you have the right number of points
#focus on one watershed first for sampling 
#use a for loop to handle the HUC8 then use HUC12 parse out file name

#define funciton to convert to sqkm
#def convert_distance(sqkm):
  #sqkm = shape_area/1000000
  #return sqkm

sample_points = {'point_id' : [], 'geometry' : [], 'HUC' : []}
#define function to determine if point is within the polygon
def in_extent(bounds):
    x = random.uniform(bounds[0], bounds[2])
    y = random.uniform(bounds[1], bounds[3])
    p = (Point(x,y))
    return p

#for each watershed in my watershed list, for each polygon in my watershed list
for layer in watershed_list:
    watershed_output = gpd.read_file(data_file, layer = layer)
    listname = [f for f in watershed_output.columns if 'HUC' in f][0]
    #print(listname)
    #use iterrows so you have the polygon and the name of the HUCcode
    for idx, row in watershed_output.iterrows():
        bounds = row['geometry'].bounds
        sqkm = row['Shape_Area']/1000000
        n = (int(round(sqkm*0.05)))
        i = 0
        #goal for the while loop, is you genereate points then append
        while i < n:
            in_extent(bounds)
            #print(p)
            #x = random.uniform(bounds[0], bounds[2])
            #y = random.uniform(bounds[1], bounds[3])
            #p = (Point(x,y))
            #shapely feature logic if polygon contains point, then append point to final list
            if row['geometry'].contains(p):
                sample_points['HUC'].append(listname)
                sample_points['geometry'].append(p)
                sample_points['point_id'].append(row[listname][0:8])
                i = i+1
               
#print(sample_points)     
crs = {'init': 'espg:4326'}    
df = gpd.GeoDataFrame(sample_points, crs=crs)
df.groupby(['point_id']).count()   

ssurgo_output = gpd.read_file(data_file, layer = 'ssurgo_mapunits_lab3')
ssurgo_output.crs=crs
#join the ssurgo with the stratified sampling points using a spatial join
#  
join = gpd.sjoin(df, ssurgo_output, how="left", op="within")

final_df = gpd.GeoDataFrame(join.groupby(['HUC', 'point_id']).mean())
final_df.iloc[:, [False, True, False, False]]


