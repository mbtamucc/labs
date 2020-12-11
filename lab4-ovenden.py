import numpy as np
import os
import rasterio 
from rasterio.plot import show, show_hist
import glob
from scipy.spatial import cKDTree

in_data_dir = r'C:\Users\mmbur\OneDrive\Documents\GEOG5092 - Automation and Programming\lab4\data'
raster_files = glob.glob(in_data_dir + '/*tif')

#set up the moving window parameters
win_rows = 11
win_cols= 9

#open raster files
slope_ras = rasterio.open(os.path.join(in_data_dir, 'slope.tif'))
wind_ras = rasterio.open(os.path.join(in_data_dir, 'ws80m.tif'))
urban_ras = rasterio.open(os.path.join(in_data_dir, 'urban_areas.tif'))
water_ras = rasterio.open(os.path.join(in_data_dir, 'water_bodies.tif'))
protected_areas_ras = rasterio.open(os.path.join(in_data_dir, 'protected_areas.tif'))

#read raster files
slope_arr = slope_ras.read(1)
wind_arr = wind_ras.read(1)
urban_arr = urban_ras.read(1)
water_arr = water_ras.read(1)
protected_areas_arr = protected_areas_ras.read(1)

#reclassify values less than zero to zero
win_arr = np.where(wind_arr < 0, 0, wind_arr)
slope_arr = np.where(slope_arr < 0, 0, slope_arr)

#extract the metadata 
meta = urban_ras.meta

#returns an array of ones with the shape and type of input and will be used in the moving window function
mask = np.ones((win_rows, win_cols))

#define a funciton for the moving window
def mean_filter(ma, mask):
        #return a new array of a given shape filled with zeros
        pct_array = np.zeros(ma.shape)
        win_area = float(mask.sum())
        row_dim = mask.shape[0]//2
        col_dim = mask.shape[1]//2
        for row in range(row_dim, ma.shape[0]-row_dim):
                 for col in range(col_dim, ma.shape[1] - row_dim):
                        win = ma[row-row_dim: row+row_dim+1,
                                col-col_dim:col+col_dim+1]
                        pct_array[row,col] = win.sum()
        return pct_array/win_area

#reclassify slope, average slope of less than 15 degrees is necessary for the development plans.
slope_sites = mean_filter(slope_arr, mask)
slope_sites = np.where(slope_arr < 15, 1, 0)
print('Sum of Slope sites:', slope_sites.sum())

#wind sites must be greater than 8.5
wind_sites = mean_filter(win_arr, mask)
wind_sites = np.where(wind_sites > 8.5, 1, 0)
print('Sum of Wind sites:', wind_sites.sum())

#the site cannot contain urban areas
urban_sites = mean_filter(urban_arr, mask)
urban_sites = np.where(urban_sites != 1, 1, 0)
print('Sum of Urban sites:' , urban_sites.sum())

#Less than 2% of land can be covered by water bodies.
water_sites = mean_filter(water_arr, mask)
water_sites = np.where(water_sites < 0.02, 1, 0)
print('Sum of Water sites:' , water_sites.sum())

#Less than 5% of the site can be within protected areas
protected_area_sites = mean_filter(protected_areas_arr, mask)
protected_area_sites = np.where(protected_area_sites < 0.05, 1, 0)
print('Sum of protected sites:' , protected_area_sites.sum())


#determine suitable sites and reclassify
sum_sites =wind_sites + slope_sites + urban_sites + water_sites + protected_area_sites
suit_arr = np.where(sum_sites ==5, 1, 0)


#update the metadata for the output raster
meta.update({'dtype':'float64', 'nodata' : 0})

#create the output raster 
with rasterio.open(os.path.join(in_data_dir, 'suitable_sites.tif'), 'w', **meta) as dest:
            dest.write(suit_arr.astype('float64'), indexes = 1)

suitable_sites = rasterio.open(os.path.join(in_data_dir, 'suitable_sites.tif'))
suitable_sites = suitable_sites.read(1)
show(suitable_sites)

print('There are ' , suit_arr.sum(), 'potential suitable sites')


##distance analysis
xs = []
ys = []
with open(os.path.join(in_data_dir, 'transmission_stations.txt')) as coords:
    lines = coords.readlines()[1:]
    for l in lines:
        x,y = l.split(',')
        xs.append(float(x))
        ys.append(float(y))
    #np.vstack is for pixel data with height (first axis) width (second axis), concatenates along the first axis
    stations = np.vstack([xs, ys])
    stations = stations.T

with rasterio.open(os.path.join(in_data_dir, 'suitable_sites.tif')) as file:
    bounds = file.bounds
    topLeft = (bounds[0], bounds[3])
    lowRight = (bounds[2], bounds[1])
    cellSize = 1000
    x_coords = np.arange(topLeft[0] + cellSize/2, lowRight[0], cellSize) #gives range of x coordinates
    y_coords = np.arange(lowRight[1] + cellSize/2, topLeft[1], cellSize) #gives range of y coordinates 
    #meshgrid cretaes a rectangular grid out of two given one-dim arrays reprenting cartesian indexing       
    x,y = np.meshgrid(x_coords, y_coords)
    #np.c_ tranlates slice objects to concatenation along the second axes, flatten returns the array in one dimension
    coord = (np.c_[x.flatten(), y.flatten()])

#provides an index into a set of k-dimensional points which can be used to rapidly look up the nearest neighbors of any point.
tree = cKDTree(coord)

#performs the nearest neighbor operations, with k being the nearest neighbors to return 
dd, ii = tree.query(stations, k=5)


print('The maximum distance to the closest transmission substation among all of the suitable sites is ' 
      +  str(dd.max()) + ' meters')
print('The minimum distance to the closest transmission substation among all of the suitable sites is ' 
      +  str(dd.min()) + ' meters')