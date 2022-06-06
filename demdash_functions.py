import streamlit as st

import rioxarray
import matplotlib.pyplot as plt
import seaborn as sns
import rasterio

import numpy as np
import geopandas as gpd
import xarray as xr
from osgeo import gdal


### TRANSECT TOOL FUNCTIONS

# POINT
def plot_point_elevation(gdf, ax, dems, years, title="Elevation time series @ point"):
    """Plot time series of DEM values at this point"""
    # TODO prefer to use time series stack
    assert len(gdf.geometry) == 1, "only expecting 1 point"
    values = []
    for year in years:
        value = dems[year].sel(x=gdf.geometry.x[0], y=gdf.geometry.y[0], method="nearest")
        values.append(value)

    ax.plot(years, values)
    ax.set_ylabel("Elevation (meters)")
    ax.set_xlabel("Year")
    ax.ticklabel_format(useOffset=False)
    # ax.legend()
    ax.set_title(title)

def plot_point_slope(gdf, ax, dems, years, title="Slope time series @ point"):
    assert len(gdf.geometry) == 1, "only expecting 1 point"
    values = []
    for year in years:
        dem = dems[year]
        slope = compute_slope(dem)
        value = slope.sel(x=gdf.geometry.x[0], y=gdf.geometry.y[0], method="nearest")
        values.append(value)

    ax.plot(years, values)
    ax.set_ylabel("Slope (degrees)")
    ax.set_xlabel("Year")
    # ax.legend()
    ax.set_title(title)

def plot_point_aspect(gdf, ax, dems, years, title="Aspect time series @ point"):
    assert len(gdf.geometry) == 1, "only expecting 1 point"
    values = []
    for year in years:
        dem = dems[year]
        aspect = compute_aspect(dem)
        value = aspect.sel(x=gdf.geometry.x[0], y=gdf.geometry.y[0], method="nearest")
        values.append(value)

    ax.plot(years, values)
    ax.set_ylabel("Aspect (degrees)")
    ax.set_xlabel("Year")
    # ax.legend()
    ax.set_title(title)

# POLYGON

def plot_polygon_elevation(gdf=None,ax=None, dems=None, years=None, title=None):
    # TODO this should use rasterstats
    # from rasterstats import zonal_stats
    # value = zonal_stats(gdf.geometry, dem) # rasterstats broken

    values = []
    for year in years:
        dem = dems[year]
        region = dem.rio.clip(gdf.geometry)
        value = {
            "mean": region.mean(),
            "std": region.std()
        }
        values.append(value)

    means = np.array([v["mean"] for v in values])
    errors = np.array([v["std"] for v in values])
    ax.plot(years, means)#, color="blue")
    # ax.errorbar(years, means, yerr=errors)
    ax.fill_between(years, means-errors, means+errors, color="gray", alpha=0.1)

    ax.set_ylabel("Elevation (meters)")
    ax.set_xlabel("Year")
    # ax.legend()
    ax.set_title(title)
    
def plot_polygon_slope(gdf=None,ax=None, dems=None, years=None, title=None):
    values = []
    for year in years:
        dem = dems[year]
        slope = compute_slope(dem)
        region = slope.rio.clip(gdf.geometry)
        value = {
            "mean": region.mean(),
            "std": region.std()
        }
        values.append(value)

    means = np.array([v["mean"] for v in values])
    errors = np.array([v["std"] for v in values])
    ax.plot(years, means)
    # ax.errorbar(years, [v["mean"] for v in values], yerr=[v["std"] for v in values])
    ax.fill_between(years, means-errors, means+errors, color="gray", alpha=0.1)


    # ax.legend()
    ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel("Slope (degrees)")


def plot_polygon_aspect(gdf=None,ax=None, dems=None, years=None, title=None):
    values = []
    for year in years:
        dem = dems[year]
        aspect = compute_aspect(dem)
        region = aspect.rio.clip(gdf.geometry)
        value = {
            "mean": region.mean(),
            "std": region.std()
        }
        values.append(value)

        # st.write(region.shape)
        sns.kdeplot(region.data.reshape(-1), ax=ax, label=str(year))
    
    # ax.plot(years, [v["mean"] for v in values])
    # ax.errorbar(years, [v["mean"] for v in values], yerr=[v["std"] for v in values])

    ax.legend()
    ax.set_xlabel("Aspect (degrees)")
    ax.set_title(title)

# Reuse plotProfile_elev code
def get_points_from_gdf(gdf, num=100):
    num = 100
    sgeom = gdf.geometry.values[0]
    distances = np.linspace(0, gdf.geometry.length.values[0], num) 
    points = [sgeom.interpolate(x) for x in distances]
    xs = xr.DataArray([p.x for p in points], dims='distance', coords=[distances])
    ys = xr.DataArray([p.y for p in points], dims='distance', coords=[distances])
    return distances, xs, ys

def sample_from_raster(raster, xs, ys):
    """returns a ??? type array"""
    # df = dss.to_dataframe(name='elevation')
    return raster.sel(x=xs, y=ys, method='nearest')

# LINE
def get_profile(gdf, dem):
    """Get elevation along a given transect from this DEM"""
     #TODO this only supports  1 SEGMENT and 1 YEAR
     # TODO point query thing support NaNs uw-cryo raster sampling library
     # TODO interpolation of elevation profile
    distances, xs, ys = get_points_from_gdf(gdf, num=100)

    dss = sample_from_raster(dem, xs, ys)
    
    return distances, dss

def compute_slope(dem):
    # TODO check a3 tools
    # Write to a new TIFF so that we can use GDAL
    # TODO delete temporary rasters
    # TODO BUG weird stuff with writing multiple versions of same raster filename
    tmp_filename = f"tmp_slope_aspect_rasters/tmp{random.randint(1,10000)}.tif"
    dem.rio.to_raster(tmp_filename)
    tmp_out_filename = f"tmp_slope_aspect_rasters/tmp_out{random.randint(1,10000)}.tif"
    gdal.DEMProcessing(tmp_out_filename, tmp_filename, 'slope')
    return rioxarray.open_rasterio(tmp_out_filename, masked=True)


import random
def compute_aspect(dem):
    # TODO check a3 tools
    # Write to a new TIFF so that we can use GDAL
    # TODO delete temporary rasters
    tmp_filename = f"tmp_slope_aspect_rasters/tmp{random.randint(1,10000)}.tif"
    dem.rio.to_raster(tmp_filename)
    tmp_out_filename = f"tmp_slope_aspect_rasters/tmp_out{random.randint(1,10000)}.tif"
    gdal.DEMProcessing(tmp_out_filename, tmp_filename, 'aspect')
    return rioxarray.open_rasterio(tmp_out_filename, masked=True)

def get_slope(gdf, dem):
    distances, xs, ys = get_points_from_gdf(gdf, num=1000)
    slope = compute_slope(dem)
    dss = sample_from_raster(slope, xs, ys)
    dss = dss.rolling(distance=10, center=True).mean()

    return distances, dss

def get_aspect(gdf, dem):
    distances, xs, ys = get_points_from_gdf(gdf, num=100)
    aspect = compute_aspect(dem)
    dss = sample_from_raster(aspect, xs, ys)
    return distances, dss
    

def plot_line_elevation(gdf=None,ax=None, dems=None, years=None, title=None, color="blue"):
    for year in years:
        distances, dss = get_profile(gdf, dems[year])
        ax.plot(distances, dss.data.squeeze(), label=str(year))#, color=color)
        ax.legend()
        ax.set_xlim([0,distances.max()])

    ax.set_title(title)
    ax.set_ylabel("Elevation (meters)")
    ax.set_xlabel("Distance along transect (meters)")

def plot_line_slope(gdf=None,ax=None, dems=None, years=None, title=None, color="blue"):
    for year in years:
        distances, dss = get_slope(gdf, dems[year])
        ax.plot(distances, dss.data.squeeze(), label=str(year))#, color=color)
        ax.set_xlim([0,distances.max()])
        # ax.legend()
    ax.set_title(title)
    ax.set_xlabel("Distance along transect (meters)")
    ax.set_ylabel("Slope (degrees)")
    
def plot_line_aspect(gdf=None,ax=None, dems=None, years=None, title=None):
    for year in years:
        distances, dss = get_aspect(gdf, dems[year])
        sns.kdeplot(dss.data.squeeze(), ax=ax, label=str(year))
        # ax.legend()
    ax.set_title(title)
    ax.set_xlabel("Aspect (degrees)")
