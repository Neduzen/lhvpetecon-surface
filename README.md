<div id="top"></div>

<!-- PROJECT SHIELDS -->

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <h1 align="center">Proxying Economic Activity with Daytime Satellite Imagery: Filling Data Gaps Across Time and Space</h1>
</div>
<br />

<!-- LICENSE -->
## Data and license

<div>
Code and data in this repository are published under a Creative Commons Attribution-NonCommercial-NoDerivs licence (https://creativecommons.org/licenses/by-nc-nd/4.0/) license according to the journal publication. </br>
Citation of code and data in this repository: 
</div>
<hr>
<div>
Lehnert, P., Niederberger, M., Backes-Gellner, U., & Bettinger, E., "Proxying economic activity with daytime satellite imagery: Filling data gaps across time and space", PNAS Nexus, 2(4). https://doi.org/10.1093/pnasnexus/pgad099</div>
<hr>


Global surface groups are available via SWISSUbase (project number 20253, https://www.swissubase.ch/de/catalogue/studies/20253/18714/overview). For an overview of download links by country and region, see https://plehnert.github.io/surfacegroups/.<br />
 </br>



<!-- ABOUT THE PROJECT -->
## About The Project

* Satellite image classification is done by using the Google Earth Engine Python API in python. The underlying code can be found in the "LandcoverClassification-EarthEngine" folder.<br />
* Data aggregation for the analyses in our PNAS Nexus publication was conducted with ArcGIS Python scripts. The underlying code can be found in the "ArcPy" folder.<br />
* Data analysis for our PNAS Nexus publication was performed with Stata scripts. The underlying code can be found in the "Stata" folder.
* The TIF and CSV files needed for replicating our analyses in the PNAS Nexus publication are available in the "Replication_Files" folder.<br />


## Instructions for Satellite Image Classification


<!-- GETTING STARTED -->
### Prerequisites
To reproduce the data processing the following things are necessary:
* Create a Google Earth Engine Account
* MongoDB installation
* Python Installation
* Stata Installation
* ArcGIS Installation


<!-- USAGE -->
### Program Specifications

Satellite image analysis: 
Python program with 3 different main.py specifications:
- Europe: Classifies European countries that participate in the CORINE Land Cover (CLC) program. Training data are produced for each country separately. Data are exported at the country level.
- USA: Classifies U.S. states. Training data are produced for each state from CLC countries in similar climate zones. Data are exported at the state level. Use and adapt this code if you wish to perform classification at a sub-country regional level.
- World: Classifies any country in the world. Training data are produced for each country from CLC countries in similar climate zones. Data are exported at the country level. This code version can also be used to classify rectangular regions based on latitude/longitude coordinates, with training data produced for the selected region.

For more information see our paper and its supplementary material https://doi.org/10.1093/pnasnexus/pgad099


<!-- USAGE EXAMPLES -->
### Setup
After installing python and setting up a GEE account, the python needs the authorization of using GEE and Google Drive.
Also MongoDB needs to be installed and set up with three databases according to the three different program specifications (see above): 
- 'landcover', host='localhost', port=27017 for Europe data
- 'landcover-USA', host='localhost', port=27017 for USA data
- 'landcover-World', host='localhost', port=27017 for world data

<br />
Setup countries to execute:<br />
Run the function 'addNewCountry()' in the specific main.py (EU, USA, World) with a country name and priority.<br />
Example:<br />
'''
    addNewCountry("Chad", 0)
'''
<br />
The python program will create a GEE asset folder and create a MongoDB entry for the country containing all required information for the automatic execution.<br />
Whenever the country name is equals to the country's feature name in GEE feature collection ('USDOS/LSIB_SIMPLE/2017'), no additional input is necessary.<br />
For countries with special names, the correct GEE feature name has to be assigned to the MongoDB entry at the variable shapefile="...", which has to match the country feature value in the property 'country_na' of the GEE featurecollection ('USDOS/LSIB_SIMPLE/2017').<br /><br />

Execution of main.py:<br />
main.py will load all countries or states saved in the MongoDB.<br />
The specific executer.py is a launch which goes through all country/state objects and identfies the next one to run (lowest priority number and not yet fully executed).<br /><br />
Each country will be launched with the following sequence:<br />
- See whether all tasks on GEE are finished, if no sleep for 20 minutes and repeat
- Create training data
- Create (lat/lon) grid cells
- Classify and export all grid cells (takes up to weeks for large countries)
- Validation (for EU countries)
- Mark country as finished


### Versioning
The folder "LandcoverClassification-EarthEngine_v1.1.0" contains the most recent version of the classification code (1.1.0). The folder "LandcoverClassification-EarthEngine_CodeArchive" contains all previous versions, including version 1.0.0 used to produce the data in the PNAS Nexus publication.

Update 1.1.0 includes two changes:
- After the discontuination of Landsat Collection 1 and its removal from the GEE Data Catalog, the new code uses the new Landsat Collection 2.
- Classification at the sub-country level (i.e., similar to "USA" specification), can now also be implemented in the "World" specification. To do so, a shapefile with sub-country boundaries has to be uploaded to GEE as an asset. See MainWorld.py for further instructions.
- The files in the "Europe" and "USA" specification subfolders remained unchanged.



<!-- CONTACT -->
## Contact

Patrick Lehnert - patrick.lehnert@business.uzh.ch

Michael Niederberger - michael.niederberger@geo.uzh.ch

Project Link: [https://github.com/Neduzen/lhvpetecon-surface](https://github.com/Neduzen/lhvpetecon-surface)

<p align="right">(<a href="#top">back to top</a>)</p>


