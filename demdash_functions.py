import streamlit as st

import rioxarray
import matplotlib.pyplot as plt

import numpy as np
import geopandas as gpd
import xarray as xr


### TRANSECT TOOL FUNCTIONS

# POINT
def plot_point_elevation():
    raise NotImplementedError
def plot_point_slope():
    raise NotImplementedError
def plot_point_aspect():
    raise NotImplementedError

# BOX

#def get_polygon_elevation():
def get_average_elevation_time_series(geojson_filename, color="red"):
    gf_epsg4326 = gpd.read_file(geojson_filename)
    gf = gf_epsg4326.to_crs("epsg:32610")
    sgeom = gf.geometry.values[0]
    means = []
    for year in years:
        clipped = dems[2021].rio.clip(gf.geometry)
        means.append(clipped.mean().squeeze())

    fig,ax= plt.subplots(1,1,figsize=(6,3))
    ax.scatter(years, means, color=color)
    plt.legend()
    st.pyplot(fig)
    
def plot_polygon_elevation():
    # TODO this should use rasterstats
    raise NotImplementedError
def plot_polygon_slope():
    raise NotImplementedError
def plot_polygon_aspect():
    raise NotImplementedError

# LINE
def get_profile(gdf, dem):
     #TODO this only supports  1 SEGMENT and 1 YEAR
     # TODO point query thing support NaNs uw-cryo raster sampling library
     # TODO interpolation of elevation profile

    # Reuse plotProfile_elev code
    num = 100

    
    sgeom = gdf.geometry.values[0]
    
    distances = np.linspace(0, gdf.geometry.length.values[0], num) 
    points = [sgeom.interpolate(x) for x in distances]
    xs = xr.DataArray([p.x for p in points], dims='distance', coords=[distances])
    ys = xr.DataArray([p.y for p in points], dims='distance', coords=[distances])
    
    # sample elevation
    dss = dem.sel(x=xs, y=ys, method='nearest')
    
    # dss = ds['elevation'].sel(x=xs, y=ys, method='nearest')
    df = dss.to_dataframe(name='elevation')
    # print(dss)
    
    return distances, dss
    

def plot_line_elevation(gdf=None,ax=None, dems=None, years=None, name=None, color="blue"):
    colors = [] # TODO want a color graident instead of random colors
    for year in years:
        distances, dss = get_profile(gdf, dems[year])
        ax.plot(distances, dss.data.squeeze(), label=str(year))#, color=color)
        plt.legend()

def plot_line_slope(gdf,dem):
    raise NotImplementedError
    
def plot_line_aspect(gdf,dem):
    raise NotImplementedError
