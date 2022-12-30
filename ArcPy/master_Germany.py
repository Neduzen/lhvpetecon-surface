from TIFCreator import TIFCreator
from Aggregate2SHP import CSVCreator_SurfaceGroups
from Aggregate2SHP import CSVMerger_SurfaceGroups
from Aggregate2SHP import CSVCreator_NightLightIntensity
from Aggregate2SHP import CSVCreator_GHSL
from SHPInSHP import ShapeSplitter
from SHPInSHP import SmallShapeInLargeShape
from SHPInSHP import CSVAppender
from arcpy.analysis import PolygonNeighbors
from arcpy.management import CalculateGeometryAttributes
from arcpy.management import AddField
from arcpy.conversion import TableToTable
import os

# GLOBALS
MAINDIR = "[INSERT PATH HERE]"
ORIG = MAINDIR+"/orig" #folder with original data files from external sources
SurfaceGroupsDB = MAINDIR+"/SurfaceGroups_Database" #folder where that contains GEE exports, merges, and aggregations; also aggregations of other satellite data
ORIG_GEE = SurfaceGroupsDB+"/CLC_countries/v1_0/GEE_export" #folder with GEE exports
GIS_GEE = SurfaceGroupsDB+"/CLC_countries/v1_0/ArcPy_merge" #folder where to store merged tif files
GIS_AGGR = SurfaceGroupsDB+"/CLC_countries/v1_0/ArcPy_aggregation" #folder where to store regional aggregations
InPath_DMSP = ORIG+'/NOAA/DMSP OLS V4 - Average Visible, Stable Lights, and Cloud Free Coverage' #folder with Version 4 DMSP-OLS Nighttime Lights Time Series data available at https://ngdc.noaa.gov/eog/dmsp/downloadV4composites.html#AVSLCFC (accessed October 25, 2021)
InPath_VIIRS = ORIG+'/EOG/EOG Nighttime Light/VIIRS NL V2' #folder with annual VIIRS night lights composites version 2 available at https://eogdata.mines.edu/nighttime light/annual/v20/ (accessed October 27, 2021)
InPath_GHSL = ORIG+'/European_Commission/GHSL' #folder with with GHSL data available at https://ghsl.jrc.ec.europe.eu/download.php?ds=bu (BUILT-S, accessed December 7, 2022) and https://ghsl.jrc.ec.europa.eu/download.php?ds=builtV (BUILT-V, accessed December 7, 2022)

# RUN COUNTRY TIF CREATOR
TIFCreator(
    InPath=ORIG_GEE,
    OutPath=GIS_GEE,
    RegionUnit='Germany',
    StartYear=1984,
    EndYear=2021, #note that end year itself is excluded
    replace=False,
    DropboxUpload=False
)

# RUN AGGREGATION
AggregationDict = {}
AggregationDict['Germany_Municipalities'] = [
    GIS_GEE+'/Germany', #InPath SurfaceGroups
    GIS_AGGR+'Germany/Germany_Municipalities', #OutPath
    ORIG+'/GeoBasis-DE/vg250_0101.utm32s.shape.ebenen/vg250_ebenen/VG250_GEM.shp', #Shapefile available at https://daten.gdz.bkg.bund.de/produkte/vg/vg250 ebenen 0101/ (accessed November 3, 2021)
    'DEBKG_ID', #ZoneField
]
AggregationDict['Germany_Counties'] = [
    GIS_GEE+'/Germany', #InPath SurfaceGroups
    GIS_AGGR+'Germany/Germany_Counties', #OutPath
    ORIG+'/GeoBasis-DE/vg250_0101.utm32s.shape.ebenen/vg250_ebenen/VG250_KRS.shp', #Shapefile available at https://daten.gdz.bkg.bund.de/produkte/vg/vg250 ebenen 0101/ (accessed November 3, 2021)
    'DEBKG_ID',  #ZoneField
]
AggregationDict['Germany_Grid'] = [
    GIS_GEE+'/Germany', #InPath SurfaceGroups
    GIS_AGGR+'Germany/Germany_Grid', #OutPath
    ORIG+'/ESDAC/grid_germany_etrs_laea_1k/grid_germany_etrs_laea_1k.shp', #Shapefile available at https://esdac.jrc.ec.europa.eu/content/european-reference-grids (accessed August 13, 2019)
    'cell_id',  #ZoneField
]

for shp in ['Germany_Counties', 'Germany_Municipalities', 'Germany_Grid']:
    CSVCreator_SurfaceGroups( #csv for every surface group
        InPath=AggregationDict[shp][0],
        OutPath=AggregationDict[shp][1]+'/SurfaceGroups',
        Shapefile=AggregationDict[shp][2],
        ZoneField=AggregationDict[shp][3],
        replace=False,
        DropboxUpload=False
    )
    CSVMerger_SurfaceGroups( #merge csv of all surface groups
        InPath=AggregationDict[shp][1]+'/SurfaceGroups',
        OutPath=AggregationDict[shp][1]+'/SurfaceGroups',
        replace=False,
        DropboxUpload=False
    )
    CSVCreator_NightLightIntensity( #csv with dmsp ols night light intensity
        InPath=InPath_DMSP,
        OutPath=AggregationDict[shp][1]+'/DMSPOLS',
        Shapefile=AggregationDict[shp][2],
        ZoneField=AggregationDict[shp][3],
        nl_type='DMSP',
        replace=False
    )
    CSVCreator_NightLightIntensity( #csv with viirs night light intensity
        InPath=InPath_VIIRS,
        OutPath=AggregationDict[shp][1]+'/VIIRS',
        Shapefile=AggregationDict[shp][2],
        ZoneField=AggregationDict[shp][3],
        nl_type='VIIRS',
        replace=False
    )
    for ghs in ['BUILT_S', 'BUILT_V']:
        CSVCreator_GHSL(
            InPath=InPath_GHSL,
            OutPath=AggregationDict[shp][1]+'/GHSL',
            Shapefile=AggregationDict[shp][2],
            ZoneField=AggregationDict[shp][3],
            ghs_type=ghs,
            replace=False
        )

# FIND FEDERAL STATE THAT GRID CELL BELONGS TO
# for merging administrative regional information to grid cells
FederalStateSHP = ORIG+'/GeoBasis-DE/vg250_0101.utm32s.shape.ebenen/vg250_ebenen/VG250_LAN.shp' #Shapefile available at https://daten.gdz.bkg.bund.de/produkte/vg/vg250 ebenen 0101/ (accessed November 3, 2021)
FederalStateZoneField = 'RS'
ShapeSplitter(AggregationDict['Germany_Grid'][2], 5000, AggregationDict['Germany_Grid'][1], replace=False) #necessary to not exceed system limits
GridSHPName = AggregationDict['Germany_Grid'][2][::-1][:AggregationDict['Germany_Grid'][2][::-1].find("/")][::-1][:AggregationDict['Germany_Grid'][2][::-1][:AggregationDict['Germany_Grid'][2][::-1].find("/")][::-1].find(".shp")]
FederalStateSHPName = FederalStateSHP[::-1][:FederalStateSHP[::-1].find("/")][::-1][:FederalStateSHP[::-1][:FederalStateSHP[::-1].find("/")][::-1].find(".shp")]
SplitPath = AggregationDict['Germany_Grid'][1]+"/"+GridSHPName+"_splits"
for file in os.listdir(SplitPath):
    if file.endswith('.shp'):
        pathfile = SplitPath+"/"+file
        SmallShapeInLargeShape(
            pathfile,
            AggregationDict['Germany_Grid'][3],
            FederalStateSHP,
            FederalStateZoneField,
            AggregationDict['Germany_Grid'][1],
            replace=True
        )
CSVAppender(
    AggregationDict['Germany_Grid'][1],
    AggregationDict['Germany_Grid'][1],
    GridSHPName,
    FederalStateSHPName,
    DeleteOrig=True,
    replace=False
)

# NEIGHBORS OF GERMAN COUNTIES
# for spatial/temporal bias analyses
PolygonNeighbors(
    AggregationDict['Germany_Counties'][2],  #in_features
    AggregationDict['Germany_Counties'][1]++"/VG250_KRS_Neighbors.csv",  #out_table
    AggregationDict['Germany_Counties'][3],  #in_fields
    "AREA_OVERLAP",
    "BOTH_SIDES",
)

# AREA SIZE OF GERMAN COUNTIES
# for estimations by county size
AddField(AggregationDict['Germany_Counties'][2], "AREA_KM2", "DOUBLE")
CalculateGeometryAttributes(
    AggregationDict['Germany_Counties'][2],
    geometry_property=[["AREA_KM2", "AREA"]],
    area_unit="SQUARE_KILOMETERS"
)
TableToTable(AggregationDict['Germany_Counties'][2], AggregationDict['Germany_Counties'][1], "VG250_KRS_Area.csv")
