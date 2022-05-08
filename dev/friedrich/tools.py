import gdown
import xdem
import rioxarray
import xarray as xr
from rasterio.enums import Resampling
import geoviews as gv
import cartopy
import holoviews as hv
from holoviews.operation.datashader import regrid
import panel as pn
import functools
import operator
import subprocess
from subprocess import Popen, PIPE, STDOUT
import pathlib
import datetime

def parse_dates(dem_files):
    dates = [datetime.datetime.strptime(pathlib.Path(file_name).stem[4:], '%Y-%m-%d') for file_name in dem_files]
    return dates

def xr_read_geotif(geotif_file_path, chunks='auto', masked=True):
    """
    Reads in single or multi-band GeoTIFF as dask array.
    Inputs
    ----------
    GeoTIFF_file_path : GeoTIFF file path
    Returns
    -------
    ds : xarray.Dataset
        Includes rioxarray extension to xarray.Dataset
    """

    da = rioxarray.open_rasterio(geotif_file_path, chunks=chunks, masked=True)

    # Extract bands and assign as variables in xr.Dataset()
    ds = xr.Dataset()
    for i, v in enumerate(da.band):
        da_tmp = da.sel(band=v)
        da_tmp.name = "band" + str(i + 1)

        ds[da_tmp.name] = da_tmp

    # Delete empty band coordinates.
    # Need to preserve spatial_ref coordinate, even though it appears empty.
    # See spatial_ref attributes under ds.coords.variables used by rioxarray extension.
    del ds.coords["band"]

    # Preserve top-level attributes and extract single value from value iterables e.g. (1,) --> 1
    ds.attrs = da.attrs
    for key, value in ds.attrs.items():
        try:
            if len(value) == 1:
                ds.attrs[key] = value[0]
        except TypeError:
            pass

    return ds


def xr_stack_geotifs(geotif_files_list, 
                     datetimes_list, 
                     reference_geotif_file, 
                     resampling="bilinear", 
                     save_to_nc=False):

    """
    Stack single or multi-band GeoTiFFs to reference_geotiff.
    Returns out-of-memory dask array, unless resampling occurs.
    
    Optionally, set save_to_nc true when resmapling is required to
    return an out-of-memory dask array.
    Inputs
    ----------
    geotif_files_list     : list of GeoTIFF file paths
    datetimes_list        : list of datetime objects for each GeoTIFF
    reference_geotif_file : GeoTIFF file path
    Returns
    -------
    ds : xr.Dataset()
    """

    ## Check each geotiff has a datetime associated with it.
    
    if len(datetimes_list) == len(geotif_files_list):
        pass
    else:
        print("length of datetimes does not match length of GeoTIFF list")
        print("datetimes:", len(datetimes_list))
        print("geotifs:", len(geotif_files_list))
        return None
    
    ## Choose resampling method. Defaults to bilinear.
    if isinstance(resampling, type(Resampling.bilinear)):
        resampling = resampling
    elif resampling == "bilinear":
        resampling = Resampling.bilinear
    elif resampling == "nearest":
        resampling = Resampling.nearest
    elif resampling == "cubic":
        resampling = Resampling.cubic
    else:
        resampling = Resampling.bilinear

    ## Get target object with desired crs, res, bounds, transform
    ## TODO: Parameterize crs, res, bounds, transform
    ref = xr_read_geotif(reference_geotif_file)

    ## Stack geotifs and dimension in time
    datasets = []
    nc_files = []
    out_dirs = []

    c = 0
    for index, file_name in enumerate(geotif_files_list):
        src = xr_read_geotif(file_name)
        
        if not check_xr_rio_ds_match(src, ref):
            src = src.rio.reproject_match(ref, resampling=resampling)
            c += 1
        src = src.assign_coords({"time": datetimes_list[index]})
        src = src.expand_dims("time")

        if save_to_nc:
            out_fn = str(pathlib.Path(file_name).with_suffix("")) + ".nc"
            pathlib.Path(out_fn).unlink(missing_ok=True) #force delete file if exists
            src.to_netcdf(out_fn)
            out_dir = str(pathlib.Path(geotif_files_list[index]).parents[0])
            nc_files.append(out_fn)
            out_dirs.append(out_dir)

        datasets.append(src)
    
    # check if anything was resampled
    if c != 0:
        print('Resampled', 
              c, 
              'of', 
              len(geotif_files_list), 
              'dems to match reference DEM spatial_ref, crs, transform, bounds, and resolution.')

        # Optionally ensure data are returned as dask array.
        if save_to_nc:
            print('Saved .nc files alongside input dem .tif files in')
            for i in list(set(out_dirs)):
                print(i)
            
            return xr.open_mfdataset(nc_files)
        
    ds = xr.concat(datasets, dim="time", combine_attrs="no_conflicts")
    return ds

def check_xr_rio_ds_match(ds1, ds2):
    """
    Checks if spatial attributes, crs, bounds, and transform match.
    Inputs
    ----------
    ds1 : xarray.Dataset with rioxarray extension
    ds2 : xarray.Dataset with rioxarray extension
    Returns
    -------
    bool
    """

    if (
        (ds1["spatial_ref"].attrs == ds2["spatial_ref"].attrs)
        & (ds1.rio.crs == ds2.rio.crs)
        & (ds1.rio.transform() == ds2.rio.transform())
        & (ds1.rio.bounds() == ds2.rio.bounds())
        & (ds1.rio.resolution() == ds2.rio.resolution())
    ):
        return True
    else:
        return False

def resample_dem(dem_file_name, 
                 res=1, 
                 verbose=True):
    """
    dem_file_name : path to dem file
    res : target resolution
    
    Assumes crs is in UTM
    """
    res = str(res)
    out_fn = '_'.join([str(pathlib.Path(dem_file_name).with_suffix("")),
                       res+'m.tif'])
    
    
    call = ['gdalwarp',
            '-r','cubic',
            '-tr', res, res,
            '-co','TILED=YES',
            '-co','COMPRESS=LZW',
            '-co','BIGTIFF=IF_SAFER',
            '-dstnodata', '-9999',
            dem_file_name,
            out_fn]
            
    run_command(call, verbose=verbose)
    return out_fn

def compute_terrain_attribute(dem_file_name, 
                              attribute='hillshade', 
                              verbose=True):
    """
    dem_file_name : path to dem file
    attribute : terrain attribute supported by gdaldem
    
    More options at https://gdal.org/programs/gdaldem.html
    """
    out_fn = '_'.join([str(pathlib.Path(dem_file_name).with_suffix("")),
                       attribute+'.tif'])
    
    call = ['gdaldem',
            attribute,
            dem_file_name,
            out_fn]
            
    run_command(call, verbose=verbose)
    return out_fn

def run_command(command, verbose=False):
    if verbose == True:
        print(*command)
    
    p = Popen(command,
              stdout=PIPE,
              stderr=STDOUT,
              shell=False)
    
    while p.poll() is None:
        line = (p.stdout.readline()).decode('ASCII').rstrip('\n')
        if verbose == True:
            print(line)