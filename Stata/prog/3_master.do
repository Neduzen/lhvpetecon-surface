********************************************************************************
*         PROXYING ECONOMIC ACTIVITY WITH DAYTIME SATELLITE IMAGERY:           *
*                   FILLING DATA GAPS ACROSS TIME AND SPACE                    * 
********************************************************************************
*        P. Lehnert, M. Niederberger, U. Backes-Gellner, & E. Bettinger        *
********************************************************************************
* 3_master.do                                                                  *
********************************************************************************

/* All files were run with Stata/MP 16.1 on Windows 11 */

version 16.1
set more off, perm
cap log close
clear all
set linesize 255
set maxvar 120000
set matsize 11000       
set excelxlsxlargefile on       


* DIRECTORIES AND DATA FILES
****************************

global MAINDIR 				"[INSERT PATH HERE]"
							/* Set working directory where all files are stored */"
global ORIG    				"${MAINDIR}\orig"
							/* Folder with original data files from external sources */
global ORIG_CROSSVAL		"${ORIG}\GEE\Germany-CrossValidation"
							/* Folder containing five-fold cross-validition CSV files exported from Google Earth Engine. */
global ORIG_GDP				"${ORIG}\Regionalstatistik\82111-01-05-4.xlsx" 
							/* Data table 82111-01-05-4 "Bruttoinlandsprodukt/Bruttowertschöpfung nach Wirtschaftsbereichen - Jahressumme - regionale Tiefe: Kreise und krfr. Städte".
							Available at https://www.regionalstatistik.de/genesis/online?operation=previous&levelindex=1&step=1&titel=Tabellenaufbau&levelid=1626691580813&acceptscookies=false#abreadcrumb (accessed June 29, 2021).
							Free user account required for access. */
global ORIG_VPI				"${ORIG}\Destatis\61111-0001.xlsx"
							/* Data table 61111-0001 "Verbraucherpreisindex (inkl. Veränderungsrasten): Deutschland, Jahre".
							Available at https://www-genesis.destatis.de/genesis/online?sequenz=tabelleErgebnis&selectionname=61111-0001&startjahr=1991#abreadcrumb (accessed November 4, 2021). */
global ORIG_ADMREG			"${ORIG}\GeoBasis-DE\vg250_0101.utm32s.shape.ebenen\vg250_ebenen\struktur_und_attribute_vg250.xls"
							/* This excel file is part of the shapefile distribution provided by the BKG. It indicates administrative information (e.g., administrative region identifier, region name) for each polygon in the shapefile.
							Available at https://daten.gdz.bkg.bund.de/produkte/vg/vg250_ebenen_0101/2017/vg250_01-01.utm32s.shape.ebenen.zip (accessed November 3, 2021). */
global ORIG_RWI				"${ORIG}\RWI\GEO-GRID_v8\microm_panelSUF.dta"
							/* Proprietary dataset RWI-GEO-GRID (see Breidenbach & Eilers, 2018). */
global ORIG_YEH_DHSCluster	"${ORIG}\Yeh_etal_2020\africa_poverty\data\output\cluster_pred_dhs_indices_gadm2.csv"
							/* Data used for Fig. 2 a and c (village level) in Yeh et al. (2020). 
							Provided by Yeh et al. (2020) as supplementary data to their article at https://raw.githubusercontent.com/sustainlab-group/africa_poverty/master/data/output/cluster_pred_dhs_indices_gadm2.csv (accessed November 22, 2021). */
global ORIG_YEH_GADM2		"${ORIG}\Yeh_etal_2020\africa_poverty\data\output\geolevel2_dhs_indices_gadm2.csv"
							/* Data used for Fig. 2 b and d (district level) in Yeh et al. (2020). 
							Provided by Yeh et al. (2020) as supplementary data to their article at https://raw.githubusercontent.com/sustainlab-group/africa_poverty/master/data/output/geolevel2_dhs_indices_gadm2.csv (accessed November 22, 2021). */
global ORIG_YEH_CENSUS		"${ORIG}\Yeh_etal_2020\africa_poverty\data\output\geolevel2_ipums_dhs_indices_ipums.csv"
							/* Data used for Fig. 2 e (census-based) in Yeh et al. (2020).
							Provided by Yeh et al. (2020) as supplementary data to their article at https://raw.githubusercontent.com/sustainlab-group/africa_poverty/master/data/output/geolevel2_ipums_dhs_indices_ipums.csv (accessed December 31, 2021). */
global ORIG_HEI				"${ORIG}\Lehnert_etal_2022\UAS_patents_PNAS.dta"
							/* Data provided by Lehnert et al. (2022). */
global DATA    				"${MAINDIR}\data"
							/* Folder for data output from Stata */
global LOG	   				"${MAINDIR}\log"
							/* Folder for saving log files */
global PROG    				"${MAINDIR}\prog"
							/* Folder where do files are stored */
global ADO	   				"${MAINDIR}\ado"
							/* Folder where ado files are stored */
global TEX	   				"${MAINDIR}\tex"
							/* Folder where tex files will be stored */
global FIG	   				"${MAINDIR}\fig"
							/* Folder which figures will be exported to */
global EXCEL   				"${MAINDIR}\excel"
							/* Folder which excel files will be exported to */
global GIS	   				"${MAINDIR}\gis"
							/* Folder where output from arcpy_SatDataAggregation scripts is stored */
global GIS_SURFACE			"${GIS}\surface_germany"
							/* Folder containing CSV files with aggregated surface groups, DMSP OLS night light intensity, GHSL night light intensity, and GHSL metrics produced with ArcGIS for Germany. */
global GIS_AFRICA			"${GIS}\surface_africa"
							/* Folder containing CSV files with aggregated surface groups produced with ArcGIS for African countries. */

cd "${MAINDIR}"


* INSTALL ADO FILES
*******************

*cap ssc install geodist
*cap ssc install geoinpoly
*cap ssc install shp2dta
*cap ssc install texdoc
cap ssc install psmatch2
cap ssc install pscore
cap ssc install group1d
cap net install _gstd01
cap ssc install xtistest
cap ssc install cdfplot
cap ssc install unique
cap ssc install center
*/

adopath + "${ADO}"


* GLOBALS FOR CALCULATIONS
**************************

// begin and end year of administrative GDP data
global beggdp = 2000
global endgdp = 2018

// begin and end year of (consecutive) RWI-GEO-GRID data
global beghhi = 2009
global endhhi = 2016

// begin and end year of Landsat data for Europe (surface groups proxy)
global begsg = 1984
global endsg = 2020

// begin and end year of DMSP OLS night light intensity data
global begdmsp = 1992
global enddmsp = 2013

// begin and end year of (consistent) VIIRS night light intensity data
global begviirs = 2014
global endviirs = 2020

// begin and end year of GHS data
global begghs = 1975
global endghs = 2020


* LOG FILE DATE
***************

global c_date %td_CYND date("$S_DATE", "DMY")
local c_date : di $c_date
global c_date = trim("`c_date'")


* DO
****

do "${PROG}\301_prepgdp.do"
do "${PROG}\302_prephhi.do"
do "${PROG}\303_prepsurface.do"
do "${PROG}\313_crossval.do"
do "${PROG}\304_prepdmspols.do"
do "${PROG}\305_prepviirs.do"
do "${PROG}\315_prepghs.do"
do "${PROG}\306_regsamples.do"
do "${PROG}\307_gdpanalyses.do"
do "${PROG}\308_hhianalyses.do"
do "${PROG}\309_predictgdp.do"
do "${PROG}\310_withinregion.do"
do "${PROG}\311_africa.do"
do "${PROG}\312_heiapplication.do"
do "${PROG}\314_econproxy.do"
