# edash
Dashboard for interactive elevation data analysis.

### App

Click on icon below to launch app :rocket:

*If you get a 500 Internal Server Error, refresh the URL in your browser.*

[![badge](https://img.shields.io/static/v1.svg?logo=mybinder&label=Launch+App&message=mybinder&color=green)](https://mybinder.org/v2/gh/friedrichknuth/edash/binder?urlpath=/proxy/5009/dashboard) (potentially faster)

[![badge](https://img.shields.io/static/v1.svg?logo=mybinder&label=Launch+App&message=mybinder&color=green)](https://gesis.mybinder.org/v2/gh/friedrichknuth/edash/binder?urlpath=/proxy/5009/dashboard) (more memory)


### Team
Quinn Brencher  
Friedrich Knuth  
Seth Vanderwilt  

### A3 Writeup
Our team of three developed a terrain visualization dashboard designed to answer the question: “How do elevation, slope, and aspect vary over the complex surface of Mt. Rainier?”. Our dashboard is composed of a) a viewing window containing a hillshade of Mt. Rainier on which the viewer can click to draw transects, and b) a column containing three plots representing elevation, slope, and aspect along the length of the provided transect. The viewer is encouraged to pan and zoom over the surface of the hillshade, drawing transects across glaciers, valleys, and ridges, and hopefully learning more about the terrain they’re observing than by just looking at a digital elevation model (DEM).

#### Encoding choices    
We’ll begin by explaining our design choices on the DEM viewing window. We chose to make the window larger than the subplots to provide plenty of room for looking at the hillshade. We use a hillshade as opposed to another terrain or elevation representation technique because we found it to be the most legible in terms of distinguishing different types of terrain. The hillshade is produced with standard options for azimuth and zenith angle, ensuring that the terrain is lit predictably. The DEM is 10m resolution, which we chose to include plenty of detail, but not be so large as to take time to render or be challenging to host. The hillshade is surrounded by a box with tics indicating the projected coordinate system–while these coordinates may not be useful to a layperson, for our use case (scientists exploring digital elevation models) they are useful for orientation. They also distinguish the panel from the background and since they’re in meters, they provide a dynamic scale bar useful for comparison to the transect length. We used the UTM 10N projection, which is a compromise projection that is pretty accurate in our region. The title is in bold, sans serif font at the top to be legible and attract the attention of the viewer. It provides some instructions on how to use the dashboard, as the tool icons provided by Holoviews are small and not obvious. The transects are represented on the hillshade as two blue endpoints connected by a blue line. The shared color groups the plot elements and distinguishes them from the background hillshade. The hue and value are hopefully bright and heavy enough to make the transect stand out, with alpha=0.5 for the endpoints and the line such that the terrain underneath is not entirely blocked. The user can update the transect by clicking new points on the window or by dragging the existing points. When the transect is changed, the plots to the right automatically update to reflect the values along the transect. For A3 we considered letting the viewer plot more than two points (a transect with multiple vertices) but decided against it because there is no obvious way to clear a transect in order to start a new one, each point must be individually moved. 

We’ll now explain our design choices for the subplots. The subplots are vertically stacked and have the same dimensions, which helps keep the visualization clean and not distracting. The first subplot contains a line plot of elevation over the length of the transect. This plot is at the top because elevation is the most fundamental terrain variable. Elevation is plotted at each 50 m point along the line, which is a compromise involving the resolution of the underlying DEM, the dimensions of the underlying DEM (which influences what length transects will probably be drawn) and including as few points as possible for faster plotting while maintaining good detail. The y axis of the plot automatically adjusts to the transect, which is useful because there is a huge range of elevation across Mt. Rainier, and presumably the viewer would like a high level of detail from their transect, even if it’s short. 

The second plot shows slope over the length of the transect, which is another important variable in terrain analysis. This plot is also a line plot, and shares the 50 m sampling scheme with the plot above. The y axis is fixed on the slope plot, because slope is much more variable over the surface of the landscape than elevation, and apparent spikes in slope (which are frequent) are easier interpreted provided the context of the maximum and minimum slope values. 

The third plot is of aspect, a third important variable in terrain analysis, especially of snow, glaciers, and vegetation. Aspect is binned over the length of the transect to create a histogram with 20 bins. This is because aspect is a cyclical variable; plotting it as a line resulted in frequent jumps between the bottom and top of the graph on north-facing slopes. In addition, it’s usually more important to see which direction a given slope or set of slopes dominantly face, instead of interpreting minute changes in aspect over the surface of a feature, as might be more common with elevation and slope. We chose to use a lighter fill color for our aspect histogram, because there is significantly more colored area in this plot and we didn’t want it to distract from the other two plots.

#### Platform rationale
In our work (Seth, Friedrich and Quinn are all in the same research group) we find that we often have large DEMs or stacks of DEMs that we want to explore. We primarily use xarray in Python to load and manipulate those DEMs. For this assignment, we wanted to design a tool that could be used to explore large DEMs without downloading them to disk–a tool that could live and be launched from wherever the DEMs are stored, often in massive cloud archives (e.g. AWS). In order to maintain compatibility with xarray, we decided to make use of Holoviews and related plotting tools for this assignment. This early design choice created some limitations–the documents for plotting with Holoviews are not detailed, and some interaction functionality that we might have liked to incorporate does not appear to exist. In particular, we aren’t satisfied with the lag between moving a point, updating the transect, and refreshing the plots. The expected behavior of the Save and Reset buttons also require modifications, as saving should in theory save some representation of the user’s transect and the results of that query, and resetting should also clear any existing transect.

#### Development process
After initial conceptual discussions, Friedrich refined many of our brainstorming concepts and did research of other terrain analysis tools he had seen before. Friedrich contributed a library of tools for reading DEMs into xarray and computing auxiliary products. Friedrich also set up and organized the repository structure, provided helpful insight on design decisions and tools to check out, and made our notebooks deployable in a binder instance for submission. Quinn designed and implemented the dashboard layout and initial profile plotting tools, which are based on this tool created by Scott Henderson (eScience): https://github.com/scottyhq/measures-panel. Quinn also wrote a second draft of the writeup. Seth refined many elements of the initial tool, including switching the aspect from a line plot to bins and considering several alternative options for display choices. Seth also drafted and finished the writeup, and prepared our tool for submission as an interactive notebook accessible via the Binder webapp.

### Local installation
```
$ git clone https://github.com/friedrichknuth/edash.git
$ conda env create -f https://raw.githubusercontent.com/friedrichknuth/edash/binder/environment.yml
$ conda activate edash
```

### Notes
Link to [dev notes](https://docs.google.com/document/d/14OYs6NTI7OAu9h_cX67nwHXl1_z6M0h4gDMTb4vTL80/edit)


