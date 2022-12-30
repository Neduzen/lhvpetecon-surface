from TIFCreator import TIFCreator
from Aggregate2SHP import CSVCreator_SurfaceGroups
from Aggregate2SHP import CSVMerger_SurfaceGroups
from CoordinatesToSquareBuffer import CoordinatesToSquareBuffer

ListCountries = []
ListCountries.append('Guinea')
ListCountries.append('Togo')
ListCountries.append('Uganda')
ListCountries.append('Zimbabwe')

# GLOBALS
MAINDIR = "[INSERT PATH HERE]"
ORIG = MAINDIR+"/orig" #folder with original data files from external sources
GIS = MAINDIR+"/gis" #folder where to store outputs that do not enter SurfaceGroupsDB
SurfaceGroupsDB = MAINDIR+"/SurfaceGroups_Database" #folder where that contains GEE exports, merges, and aggregations; also aggregations of other satellite data
ORIG_GEE = SurfaceGroupsDB+"/nonCLC_countries/country_classifier/v1_0/GEE_export" #folder with GEE exports
GIS_GEE = SurfaceGroupsDB+"/nonCLC_countries/country_classifier/v1_0/ArcPy_merge" #folder where to store merged tif files
GIS_AGGR = SurfaceGroupsDB+"/nonCLC_countries/country_classifier/v1_0/ArcPy_aggregation" #folder where to store regional aggregations

# RUN TIF CREATOR
for region in ListCountries:
    TIFCreator(
        InPath=ORIG_GEE,
        OutPath=GIS_GEE,
        RegionUnit=region,
        StartYear=2009,
        EndYear=2016, #note that end year itself is excluded
        replace=False,
        DropboxUpload=False,
    )

# CREATE POLYGONS FOR DHS CLUSTERS (FROM YEH ET AL., 2020, DATA)
CLUSTER_PRED_YEH = ORIG+"/Yeh_etal_2020/africa_poverty/data/output/cluster_pred_dhs_indices_gadm2.csv" #provided by Yeh et al. (2020) as supplementary data to their article available at https://raw.githubusercontent.com/sustainlab-group/africa_poverty/master/data/output/cluster_pred_dhs_indices_gadm2.csv (accessed November 22, 2021)
OUT_CLUSTER_YEH = GIS+"/Yeh_etal_2020_clusters.shp" #folder where to store SHP file for aggregation
CoordinatesToSquareBuffer(
    InCoordTable=CLUSTER_PRED_YEH,
    InCoordX="lon", InCoordY="lat",
    OutSHP=OUT_CLUSTER_YEH,
    BufferDist="3360 Meters",
    replace=False
)

# RUN AGGREGATION
AggregationDict = {}
AggregationDict['Guinea_GADM2'] = [
    GIS_GEE+'/Guinea', #InPath
    GIS_AGGR+'/Guinea/Guinea_GADM2', #OutPath
    ORIG+'/GADM/gadm36_GIN_shp/gadm36_GIN_2.shp', #Shapefile available at https://gadm.org/download_country.html (accessed November 22, 2021)
    'GID_2' #ZoneField
]
AggregationDict['Guinea_DHSCluster'] = [
    GIS_GEE+'/Guinea', #InPath
    GIS_AGGR+'/Guinea/Guinea_DHSCluster', #OutPath
    OUT_CLUSTER_YEH, #Shapefile
    'ORIG_FID' #ZoneField
]
AggregationDict['Togo_GADM2'] = [
    GIS_GEE+'/Togo', #InPath
    GIS_AGGR'/Togo/Togo_GADM2', #OutPath
    ORIG+'/GADM/gadm36_TGO_shp/gadm36_TGO_2.shp', #Shapefile available at https://gadm.org/download_country.html (accessed November 22, 2021)
    'GID_2' #ZoneField
]
AggregationDict['Togo_DHSCluster'] = [
    GIS_GEE+'/Togo', #InPath
    GIS_AGGR+'/Togo/Togo_DHSCluster', #OutPath
    OUT_CLUSTER_YEH, #Shapefile
    'ORIG_FID' #ZoneField
]
AggregationDict['Uganda_GADM2'] = [
    GIS_GEE+'/Uganda', #InPath
    GIS_AGGR+'/Uganda/Uganda_GADM2', #OutPath
    ORIG+'/GADM/gadm36_UGA_shp/gadm36_UGA_2.shp', #Shapefile available at https://gadm.org/download_country.html (accessed November 22, 2021)
    'GID_2' #ZoneField
]
AggregationDict['Uganda_DHSCluster'] = [
    GIS_GEE+'/Uganda', #InPath
    GIS_AGGR+'/Uganda/Uganda_DHSCluster', #OutPath
    OUT_CLUSTER_YEH, #Shapefile
    'ORIG_FID' #ZoneField
]
AggregationDict['Zimbabwe_GADM2'] = [
    GIS_GEE+'/Zimbabwe', #InPath
    GIS_AGGR+'/Zimbabwe/Zimbabwe_GADM2', #OutPath
    ORIG+'/GADM/gadm36_ZWE_shp/gadm36_ZWE_2.shp', #Shapefile available at https://gadm.org/download_country.html (accessed November 22, 2021)
    'GID_2' #ZoneField
]
AggregationDict['Zimbabwe_DHSCluster'] = [
    GIS_GEE+'/Zimbabwe', #InPath
    GIS_AGGR+'/Zimbabwe/Zimbabwe_DHSCluster', #OutPath
    OUT_CLUSTER_YEH, #Shapefile
    'ORIG_FID' #ZoneField
]

for shp in ['Guinea_GADM2', 'Guinea_DHSCluster', 'Togo_GADM2', 'Togo_DHSCluster', 'Uganda_GADM2', 'Uganda_DHSCluster', 'Zimbabwe_GADM2', 'Zimbabwe_DHSCluster']:
    CSVCreator_SurfaceGroups(  # csv for every surface group
        InPath=AggregationDict[shp][0],
        OutPath=AggregationDict[shp][1] + '/SurfaceGroups',
        Shapefile=AggregationDict[shp][2],
        ZoneField=AggregationDict[shp][3],
        replace=False,
        DropboxUpload=False
    )
    CSVMerger_SurfaceGroups(  # merge csv of all surface groups
        InPath=AggregationDict[shp][1] + '/SurfaceGroups',
        OutPath=AggregationDict[shp][1] + '/SurfaceGroups',
        replace=False,
        DropboxUpload=False
    )
