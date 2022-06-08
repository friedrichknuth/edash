import streamlit as st
import rioxarray
import matplotlib.pyplot as plt
import seaborn as sns

import numpy as np
import geopandas as gpd

from matplotlib_scalebar.scalebar import ScaleBar


import leafmap.foliumap as leafmap
import geojson

from demdash_functions import *


# TODO bug: will need to figure out something like this to make raster actually display if not running streamlit & browser locally!
#import os
#os.environ['LOCALTILESERVER_CLIENT_PREFIX'] = f'{os.environ['JUPYTERHUB_SERVICE_PREFIX'].lstrip('/')}/proxy/{{port}}'

st.set_page_config(layout="wide")
st.title("DEM Dashboard Tool")

years = [2015,2016,2017,2018,2019,2020,2021]

#years = [2014,2015,2016,2017,2018,2019,2020,2021]
dems = {}
dem_filenames = {}
for year in years:
    dem_filenames[year] = f"test_data_dir/{year}.tif"
    # TODO clean up
    dems[year] = rioxarray.open_rasterio(f"test_data_dir/{year}.tif", masked=True)


with st.sidebar:
    tool_choices = st.multiselect("Choose tool(s) to display:", ["DEM Difference", "DEM Explorer", "Timelapse"], default=["DEM Difference", "DEM Explorer", "Timelapse"])
    # st.write("Current tool:", add_radio)

# with col1:
if "DEM Difference" in tool_choices:
    st.header("Elevation difference map: choose start and end year using sliders")

    values = st.select_slider("Year", options=years, value=(years[0], years[-1]))

    fig,ax = plt.subplots(1,1, figsize=(8,5))
    diff = dems[values[1]] - dems[values[0]]
    absmax = max(abs(diff.min()), abs(diff.max()))
    plt.imshow(diff.transpose("y","x","band").to_numpy(), rasterized=True, cmap="RdBu", vmin=-absmax, vmax=absmax)
    plt.colorbar(label="End Z - Start Z (meters)")
    # diff.plot(ax=ax)
    scale = diff.rio.resolution()[0]
    ax.add_artist(ScaleBar(scale, fixed_value=100))
    plt.xlabel("X (meters)")
    plt.ylabel("Y (meters)")


    st.pyplot(fig)
    # st.write("Difference map goes here, turned off while working on other features")

if "DEM Explorer" in tool_choices:
    ### TRANSECT TOOL DISPLAY
    st.header("Transect tool: pick a point, draw a line, or sketch a polygon. Export then drag GeoJSON onto uploader to see elevation/slope/aspect statistics")
    st.markdown("Demo workaround: hillshades/color images aren't rendering in the gray box when viewing remotely, clue=[Github](https://github.com/streamlit/streamlit/pull/4677)")
    uploaded_geojson_file = st.file_uploader("Upload GeoJSON")

    col1, col2 = st.columns([10,6])


    m = leafmap.Map(google_map="HYBRID", draw_export=True)#latlon_control=True, draw_export=True)#, zoom=13)#, crs="EPSG:32610")
    # m.add_cog_layer("/mnt/1.0_TB_VOLUME/sethv/cse512/a3/edash/dem_raster_stack/2021_cog.tif")
    # m.add_local_tile("/mnt/1.0_TB_VOLUME/sethv/cse512/a3/edash/dem_raster_stack/2021.tif", layer_name="dem2021")
    # diff.rio.to_raster("diff.tif")
    # for year in years:
    #     #TODO just showing this is possible, don't ACTUALLy want qgis style
    #     m.add_local_tile(dem_filenames[year], layer_name=f"{year}")

    # m.add_local_tile("diff.tif", layer_name="diff_from_above", cmap="RdBu")
    # m.split_map(left_layer="OpenTopoMap", right_layer="OpenTopoMap")

    # TODO trying to figure out how to get the TIFFs to show up when viewing from other machines
    # https://github.com/streamlit/streamlit/pull/4677

    # url = 'https://opendata.digitalglobe.com/events/california-fire-2020/pre-event/2018-02-16/pine-gulch-fire20/1030010076004E00.tif'
    # url = "http://localhost:39881/2021_hs_cog.tif"
    # m.add_cog_layer("http://localhost:40000")#, name="2021_hs_cog.tif")
    # m.add_local_tile("test_data_dir/resampled_sethv1_easton_20210924_without_gcps_transparent_mosaic_group1.tif") #  http://127.0.0.1:39189 is where it looked for tile
    m.add_local_tile("test_data_dir/2021_hs.tif", layer_name="hs2021")#, colormap="terrain")#, debug=True)
    # m.add_local_tile("/mnt/1.0_TB_VOLUME/sethv/cse512/a3/edash/dem_raster_stack/2021_hs.tif", layer_name="hs2021")#, colormap="terrain")#, debug=True)

    # m.add_raster("/mnt/1.0_TB_VOLUME/sethv/2022_easton_wip_make_repo/dem_raster_stack/2021.tif", colormap="terrain", layer_name='DEM') #'terrain


    # Illustrate how this is done with an example preloaded transect
    gj_ex_filename = "test_data_dir/example_easton_transect.geojson"
    with open(gj_ex_filename) as gj_ex_file:
        gj_ex = geojson.load(gj_ex_file)
        
        gdf_epsg4326_ex = gpd.read_file(gj_ex_filename)
        gdf_ex = gdf_epsg4326_ex.to_crs("epsg:32610")

    if uploaded_geojson_file is not None:
        geojson_file = uploaded_geojson_file
        gj = geojson.loads(geojson_file.getvalue())
    else:
        # use example geojson to show how to use the tool
        geojson_file = gj_ex_filename
        with open(geojson_file) as f:
            gj = geojson.load(f)#s(geojson_file.getvalue())

    # load the geojson ONCE and figure out which kind of geometry we are dealing with

    gdf_epsg4326 = gpd.read_file(geojson_file)
    gdf = gdf_epsg4326.to_crs("epsg:32610")
    assert len(gdf.geometry) == 1, "We only support GeoJSONs with exactly 1 polygon/line/point"


    with col2:

        # Make 3 subplots of elevation, slope, aspect regardless of user's GeoJSON type
        fig,ax = plt.subplots(3,1,figsize=(6,9))
        
        feature_type = gdf.geometry.type[0]
        if feature_type == "LineString":
            # TODO where should this sort of color scheme setting happen?
            sns.set_palette(sns.color_palette("tab10"))

            sns.set_palette("Blues", n_colors=10)
            # fig.suptitle("profile of user uploaded transect")
            plot_line_elevation(gdf=gdf, ax=ax[0], dems=dems, years=years, title="Elevation profile along transect")
            plot_line_slope(gdf=gdf, ax=ax[1], dems=dems, years=years, title="Slopes along transect")
            plot_line_aspect(gdf=gdf, ax=ax[2], dems=dems, years=years, title="Distribution of aspects along transect")
            plt.tight_layout()

        elif feature_type == "Point":
            # sns.set_palette(sns.color_palette("Blues", as_cmap=True).reversed(), n_colors=1)
            # fig.suptitle("Time series at this point")
            plot_point_elevation(gdf=gdf, ax=ax[0], dems=dems, years=years, title="Elevation time series @ point")
            plot_point_slope(gdf=gdf, ax=ax[1], dems=dems, years=years, title="Slope time series @ point")
            plot_point_aspect(gdf=gdf, ax=ax[2], dems=dems, years=years, title="Aspect time series @ point")
            plt.tight_layout()

        elif feature_type == "Polygon":
            # sns.set_palette("Blues", n_colors=1)
            fig.suptitle("elevation/slope/aspect stats for this polygon")
            plot_polygon_elevation(gdf=gdf, ax=ax[0], dems=dems, years=years, title="Elevation within polygon")
            plot_polygon_slope(gdf=gdf, ax=ax[1], dems=dems, years=years, title="Slope within polygon")
            plot_polygon_aspect(gdf=gdf, ax=ax[2], dems=dems, years=years, title="Aspect within polygon")
            plt.tight_layout()
        
        else:
            raise NotImplementedError("Unsupported GeoJSON type")

        st.pyplot(fig)

    # Draw the user's transect/point/polygon on the map
    m.add_geojson(gj, layer_name="JSON profile uploaded by user", style={"color":"red", "fillColor":"red"})

    # TODO quick hack for demo to work around invisible rasters...
    # Since rasters are not rendering on remote machines accessing the app,
    # instead just rely on the basemap and draw a box around the DEM extent
    # Generated raster extent with gdaltindex in EPSG:4326
    with open("test_data_dir/dems_box_epsg4326.geojson") as f:
        gj_raster_extent = geojson.load(f)

    # Would have to Reproject to EPSG 4326 if not done in gdaltindex
    m.add_geojson(gj_raster_extent, layer_name="Extent of study area DEMs", style={"color":"gray", "fillColor":"none"})

    with col1:
        # The map goes in the first column
        m.to_streamlit()

if "Timelapse" in tool_choices:
    st.header("Timelapse tool (apps will go on separate pages eventually)")
    st.markdown("Work in progress porting \"Create Timelapse\" tool from streamlit.geemap.org") 
    st.markdown("Want to produce animations like [this one of hillshades and color orthoimages changing over the years](https://www.ce.washington.edu/files/images/news/easton_hillshade_ortho_timeseries_animation_2014-2021_lidar_web.gif) or [this animation of the glacier surface elevation decreasing over time](https://static.us.edusercontent.com/files/Mbfc9qhDCn6EhSU0Nx9uWkea) with more control over configuration, which data included, etc.")

# # https://matplotlib.org/stable/gallery/animation/dynamic_image.html
# # https://matplotlib.org/stable/api/_as_gen/matplotlib.animation.FuncAnimation.html
# import matplotlib.animation as animation
# from matplotlib_scalebar.scalebar import ScaleBar
# # import matplotlib.pyplot as plt
# # fig,ax=plt.subplots()

# # def func(frame, *args):
# #     print(args)
# #     assert 1==0

# # animation.FuncAnimation(fig, func, frames=[1,2,3,4])
# # ani = animation.ArtistAnimation(fig, ims, interval=50, blit=True,
# #                                 repeat_delay=1000)

# # https://stackoverflow.com/questions/34975972/how-can-i-make-a-video-from-array-of-images-in-matplotlib
# # img = [] # some array of images
# frames = [] # for storing the generated images
# fig,ax = plt.subplots(ncols=2, figsize=[20,10])
# # plt.suptitle("Easton Glacier Surface Elevation (Hillshade)", fontsize=48)
# ax[0].set_xticks([])
# ax[0].set_yticks([])
# ax[1].set_xticks([])
# ax[1].set_yticks([])
# titles = {
#     2014: "2014 UAV SfM",
#     2015: "2015 Lidar",
#     2016: "2016 UAV SfM",
#     2017: "2017 UAV SfM",
#     2018: "2018 UAV SfM",
#     2019: "2019 UAV SfM",
#     2020: "2020 UAV SfM",
#     2021: "2021 UAV SfM"
# }
# plt.rcParams['animation.embed_limit'] = 30000000 # 20971520.0 limit

# for year in range(2015,2022):
#     # year = 2014+i # TODO hacky
    
#     # orthos[3]
    
#     scale = 0.5
#     frames.append([
#         ax[0].set_title("Easton Glacier Surface Elevation (Hillshade)", fontsize=24),
        
#         ax[0].imshow(dems[year].squeeze(), cmap="gray", 
#             # clim=pltlib.get_clim(hs),
#             rasterized=True, animated=True),
#         # ax[0].imshow(dems[i], alpha=0.6, clim=[1550,1850], rasterized=True, animated=True),
#         ax[0].text(250, 100, f"{titles[year]}", ha='center', va='center', fontsize=24, backgroundcolor="White", color="Black"),
        
#         # ax[1].set_title("Easton Glacier Orthoimage", fontsize=24),
        
#         # # Gross but have to do an exceptional plot of 2015 lidar intensity
#         # ax[1].imshow(orthos[i].transpose("y","x","band"), rasterized=True, animated=True) if orthos[i].shape[0] > 1 else \
#         #     ax[1].imshow(orthos[i].squeeze(), cmap="binary", vmin=0, vmax=20000, rasterized=True, animated=True),
        
        
#         # ax[1].add_artist(ScaleBar(scale, fixed_value=100)),
#         # ax[1].text(250, 100, f"{titles[year]}", ha='center', va='center', fontsize=24, backgroundcolor="White", color="Black")

#     ])
        
# ani = animation.ArtistAnimation(fig, frames, interval=50, blit=True,
#                                 repeat_delay=1000)

# from IPython.display import HTML
# animation = HTML(ani.to_jshtml())
# # ani.save('movie.mp4')
# # plt.show()
# # https://github.com/egagli/sar_snow_melt_timing/blob/main/backscatter_visualization_and_gifs.ipynb
# hillshade_timseries_animation_fn = "easton_hillshade_ortho_timeseries_animation_2014-2021.gif"
# ani.save(hillshade_timseries_animation_fn, writer="pillow", fps=1)
# # ani.save("movie.mp4") # no ffmpeg access via jupyter
# # st.write(ani.to_html5_video())
# st.markdown(ani.to_jshtml(), unsafe_allow_html=True)
# st.image(hillshade_timseries_animation_fn, output_format="GIF")
# st.pyplot(ani) # didn't work
# animation

## OTHER PREVIOUSLY USEFUL CODE BELOW THIS LINE





# from ipyleaflet import 

# control = SplitMapControl(left_layer=left_layer, right_layer=right_layer)
# Map.add_control(control)
# Map.add_control(LayersControl(position='topright'))
# Map.add_control(FullScreenControl())

# Map


# def print_features():
#     # m.user_roi to get the last draw feature
#     # m.user_rois to get all draw features as a GeoJSON
#     # m.draw_features
#     print(hasattr(m, "user_roi"))
#     print(hasattr(m, "user_rois"))
#     print(hasattr(m, "user_draw_features"))
#     st.write(m.user_roi)
#     st.write(m.user_rois)
#     st.write(m.draw_features)
    
# st.button("see draw_features, user_roi, user_rois", on_click=print_features)

# # import geemap
# from ipywidgets import Label
# from ipyleaflet import Marker

# Map = leafmap.Map(center=(40, -100), zoom=4)

# label = Label()
# # display(label)

# coordinates = []


# def handle_interaction(**kwargs):
#     latlon = kwargs.get('coordinates')
#     if kwargs.get('type') == 'mousemove':
#         label.value = str(latlon)
#     elif kwargs.get('type') == 'click':
#         coordinates.append(latlon)
#         Map.add_layer(Marker(location=latlon))


# Map.on_interaction(handle_interaction)

# # Map
# Map.to_streamlit()


# Tried this, did not work with earthengine-api authentication

# import geemap

# Map = geemap.Map()
# Map.split_map(left_layer='HYBRID', right_layer='ESRI')
# Map.to_streamlit()
# print("shouuld show split map")
# AttributeError: module 'collections' has no attribute 'Callable'

# st.snow()




# import palettable

# @st.cache
# def get_palettes():
#     palettes = dir(palettable.matplotlib)[:-16]
#     return ["matplotlib." + p for p in palettes]

# def app():

#     st.title("Visualize Raster Datasets")
#     st.markdown(
#         """
#     An interactive web app for visualizing local raster datasets and Cloud Optimized GeoTIFF ([COG](https://www.cogeo.org)). The app was built using [streamlit](https://streamlit.io), [leafmap](https://leafmap.org), and [localtileserver](https://github.com/banesullivan/localtileserver).


#     """
#     )

#     row1_col1, row1_col2 = st.columns([2, 1])

#     with row1_col1:
#         cog_list = load_cog_list()
#         cog = st.selectbox("Select a sample Cloud Opitmized GeoTIFF (COG)", cog_list)

#     with row1_col2:
#         empty = st.empty()

#         url = empty.text_input(
#             "Enter a HTTP URL to a Cloud Optimized GeoTIFF (COG)",
#             cog,
#         )

#         data = st.file_uploader("Upload a raster dataset", type=["tif", "img"])

#         if data:
#             url = empty.text_input(
#                 "Enter a URL to a Cloud Optimized GeoTIFF (COG)",
#                 "",
#             )

#         add_palette = st.checkbox("Add a color palette")
#         if add_palette:
#             palette = st.selectbox("Select a color palette", get_palettes())
#         else:
#             palette = None

#         submit = st.button("Submit")

#     m = leafmap.Map(latlon_control=False)

#     if submit:
#         if data or url:
#             try:
#                 if data:
#                     file_path = leafmap.save_data(data)
#                     m.add_local_tile(file_path, palette=palette, debug=True)
#                 elif url:
#                     m.add_remote_tile(url, palette=palette, debug=True)
#             except Exception as e:
#                 with row1_col2:
#                     st.error("Work in progress. Try it again later.")

#     with row1_col1:
#         m.to_streamlit()

# app()

#   import folium
#   from streamlit_folium import st_folium

#   # centery,centerx=48,123
#   # m= folium.Map(location=[centery, centerx], width=1000,height=1000, zoom_start=20, min_zoom=17,max_zoom=30, tiles='Stamen Terrain')
#   # st_data_ = st_folium(m, width = 725)


#   m = folium.Map(location=[48.735772, -121.839559], zoom_start=15)

#   import matplotlib



#   lon_min, lat_min, lon_max, lat_max = (-121.841843541272, 48.73394823057196, -121.83226592690929, 48.74025683883483) # from rioxarray.rio.bounds on epsg:4326
#   folium.raster_layers.ImageOverlay(
#       "/mnt/1.0_TB_VOLUME/sethv/cse512/a3/edash/dem_raster_stack/2021_epsg4326.tif",
#       bounds=[[lat_min, lon_min], [lat_max, lon_max]],
#       colormap=matplotlib.cm.inferno
#   ).add_to(m)

#   map_data = st_folium(m, key="fig1", width=700, height=700)

####

