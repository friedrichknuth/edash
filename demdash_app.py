import streamlit as st
import rioxarray
import matplotlib.pyplot as plt

import numpy as np
import geopandas as gpd
import xarray as xr


import leafmap.foliumap as leafmap
import geojson


# TODO bug: will need to figure out something like this to make raster actually display if not running streamlit & browser locally!
#import os
#os.environ['LOCALTILESERVER_CLIENT_PREFIX'] = f'{os.environ['JUPYTERHUB_SERVICE_PREFIX'].lstrip('/')}/proxy/{{port}}'

st.title("DEM Dashboard Tool")
st.header("Difference map tool")
st.text("Adjust the sliders to choose which start and end year to compute elevation difference map")
years = [2014,2015,2016,2017,2018,2019,2020,2021]
dems = {}

for year in years:
    dems[year] = rioxarray.open_rasterio(f"test_data_dir/{year}.tif", masked=True)

values = st.select_slider("Year", options=years, value=(years[0], years[-1]))
print(values)


fig,ax = plt.subplots(1,1)
diff = dems[values[1]] - dems[values[0]]
diff.plot(ax=ax)

st.pyplot(fig)


st.header("Transect tool")




m = leafmap.Map(latlon_control=False, draw_export=True)#, crs="EPSG:32610")
# m.add_cog_layer("/mnt/1.0_TB_VOLUME/sethv/cse512/a3/edash/dem_raster_stack/2021_cog.tif")
# m.add_local_tile("/mnt/1.0_TB_VOLUME/sethv/cse512/a3/edash/dem_raster_stack/2021.tif", layer_name="dem2021")
m.add_local_tile("test_data_dir/2021_hs.tif", layer_name="hs2021")#, colormap="terrain")#, debug=True)
# m.add_local_tile("/mnt/1.0_TB_VOLUME/sethv/cse512/a3/edash/dem_raster_stack/2021_hs.tif", layer_name="hs2021")#, colormap="terrain")#, debug=True)

# m.add_raster("/mnt/1.0_TB_VOLUME/sethv/2022_easton_wip_make_repo/dem_raster_stack/2021.tif", colormap="terrain", layer_name='DEM') #'terrain

def get_profile(geojson_filename):

    # Reuse plotProfile_elev code
    num = 100
    gf_epsg4326 = gpd.read_file(geojson_filename)
    gf = gf_epsg4326.to_crs("epsg:32610")
    
    sgeom = gf.geometry.values[0]
    print(sgeom)
    print(gf.geometry.length.values)
    
    distances = np.linspace(0, gf.geometry.length.values[0], num) 
    print(distances)
    points = [sgeom.interpolate(x) for x in distances]
    xs = xr.DataArray([p.x for p in points], dims='distance', coords=[distances])
    ys = xr.DataArray([p.y for p in points], dims='distance', coords=[distances])
    
    # sample elevation
    dss = dems[2021].sel(x=xs, y=ys, method='nearest')
    print(dss.shape)
    # dss = ds['elevation'].sel(x=xs, y=ys, method='nearest')
    df = dss.to_dataframe(name='elevation')
    # print(dss)
    
    print(distances)
    print(dss.data)
    return distances, dss

def plot_profile(geojson_filename,ax,name="name of transect goes here", color="blue"):
    distances, dss = get_profile(geojson_filename)
    ax.plot(distances, dss.data.squeeze(), label=name, color=color)
    plt.legend()

geojson_file = st.file_uploader("Upload GeoJSON")

# Illustrate how this is done with an example preloaded transect
gj_ex_filename = "test_data_dir/example_easton_transect.geojson"
with open(gj_ex_filename) as gj_ex_file:
    gj_ex = geojson.load(gj_ex_file)
m.add_geojson(gj_ex, layer_name="Example GeoJSON transect used to make plots", style={"color":"blue", "fillColor":"blue"})


fig,ax = plt.subplots(1,1,figsize=(6,3))
plot_profile(gj_ex_filename,ax,"example transect profile", color="blue")
st.pyplot(fig)


fig,ax = plt.subplots(1,1,figsize=(6,3))
dss = get_profile(gj_ex_filename)[1]
ax.hist(dss.data.squeeze(), color="blue")
ax.set_title("histogram of elevation values")
st.pyplot(fig)

if geojson_file is not None:
        
    fig,ax = plt.subplots(1,1,figsize=(6,3))
    print(geojson_file.name)
    # st.write(geojson_file)

    plot_profile(geojson_file,ax,name="user uploaded geojson transect profile", color="red")
    st.pyplot(fig)

    gj = geojson.loads(geojson_file.getvalue())

    m.add_geojson(gj, layer_name="JSON profile uploaded by user, could be 1 of n ?", style={"color":"red", "fillColor":"red"})
    # st.text(f"Plot of profile w/ '{geojson_file.name}' goes here, this is printed when the geojson file is loaded")
    # st.write("Not actually going to print the GEOJSON just want to see coordinates below before doing profile extraction")
    # st.write(gj)

    
    
    # Sample from the DEM raster

    
    
 
    # Instead of df try dss.hvplot???
#     profile = dss.plot.line(ax=ax,
#                                    # x="distance",
#                                    y="band",
#                                                  # title='elevation',
#                                                  # xlabel='Distance (m)',
#                                                  # ylabel='Elevation (m)',
#                                                  # width=300, height=150, 
#                                                  # shared_axes=False
#                           )

    
    #df = get_profile(point_stream, num=10)
#     profile = df.hvplot.line(y='elevation').opts(ax=ax,
#                                                  title='elevation',
#                                                  xlabel='Distance (m)',
#                                                  ylabel='Elevation (m)',
#                                                  width=300, height=150, 
#                                                  shared_axes=False)
    
    
    # Show the actual values along the transect
    
    
    # This should be a histogram of aspect but not going to compute that yet
    # dems[2021].plot.hist(ax=ax)

    
    

    
st.header("Transect tool: for now draw a line between any two points")   
st.text("Export as GeoJSON, drag file onto uploader, our code will sample the points along your line and plot the elevation profile")
m.to_streamlit()



st.header("Timelapse tool (apps will go on separate pages eventually)")
st.text("Work in progress porting \"Create Timelapse\" tool from streamlit.geemap.org") 






## OTHER USEFUL CODE BELOW THIS LINE





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

