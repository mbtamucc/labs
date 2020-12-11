import os
import glob
from shapely.geometry import Polygon
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
from rasterstats import zonal_stats

#set environmenents and folder structure
#img_list contains 2 raster files for agriculural cover over 3 districts in Tanzania. 
#WGS84

os.chdir(r'C:\Users\mmbur\OneDrive\Documents\GEOG5092 - Automation and Programming\lab2\lab2_data\data')
img_list = glob.glob('../*/*/*.tif')
filenames = glob.glob('../*/*/*.txt')

#a dictionary allows the user to create a pre-defined data structure such as column names
districts = {'district':[], 'num_coords':[], 'geometry':[]}
for x in filenames:
    #slice the file name x in the path filenames to grab only the district name
    polyname = x[-14:-4]
    #read the csv file, file has a space delineation
    data = pd.read_csv(x, delim_whitespace=True)
    #create a tuple to hold the coordinates. Read through data X column and data y columns as a list
    coordlist = list(zip(data["X"],data["Y"]))
    #create polygon using shapely
    poly = Polygon(coordlist)
    #use matplotlib to plot exterior polygon tuples
    x,y = poly.exterior.xy
    plt.plot(x,y)
    #create and populate fields (num_coords and districts) with a geodataframe created from dictionaries 
    districts['district'].append(polyname)
    districts['num_coords'].append(len(coordlist))
    districts['geometry'].append(poly)
    
#creating a geopandas datafrom from dictionaries
districts_gdf= gpd.GeoDataFrame.from_dict(districts)
districts_gdf.crs = {'init': 'epsg:4326'}
outfc = 'districts_test.shp'
districts_gdf.to_file(driver = 'ESRI Shapefile', filename = outfc)
shp = gpd.read_file(outfc)
print(shp)


x_df = pd.DataFrame()

for img in img_list:
    outname = img[-13:-9]
    x = (zonal_stats(shp, img, stats='count sum'))
    outname = pd.DataFrame(x)
    outname['district'] = shp['district']
    outname['year']=img[-13:-9]
    outname['percent cover'] = (outname['sum']/outname['count'] * 100)
    x_df = x_df.append(outname)
    
print("In" + " " + x_df["year"] + " " + x_df["district"] + " " + "has" + " " + x_df['percent cover'].map('{:,.1f}'.format) + "% agricultural land cover") 


