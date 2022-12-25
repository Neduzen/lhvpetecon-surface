********************************************************************************
* 303_prepsurface.do                                                           *
********************************************************************************

/* This file imports and aggregates the surface groups CSV files produced with
ArcGIS (arcy_SatDataAggregation scripts). */


* START LOG
***********

cap log close
log using "${LOG}\303_prepsurface_${c_date}.log", replace

	
* IMPORT AND MERGE DATA
***********************

foreach r in Counties Grid Municipalities {
	
	clear
	
	local start = ${begsg}
	local end = ${endsg}
		
	forval y = `start'(1)`end' {
		
		preserve
			tempfile tmp
			local files : dir "${GIS_SURFACE}\Germany\csv\Germany_`r'" files "*`y'.csv"
			tokenize `files'
			import delim using "${GIS_SURFACE}\Germany\csv\Germany_`r'\\`1'", clear
			drop *_area
			save `tmp'
		restore
		
		append using `tmp'
		
		}
		
	qui ds
	tokenize `r(varlist)'
	
	
* GENERATE VARIABLE WITH TOTAL NUMBER OF PIXELS PER REGION
**********************************************************

	gen total_px = builtup_px+grass_px+forest_px+crops_px+noveg_px+water_px+cloud_px
	
	
* MERGE AREA SIZE (COUNTIES ONLY)
*********************************

	if "`r'"=="Counties" {
		preserve
			tempfile area
			import delimited using "${GIS_SURFACE}\Germany\csv\Germany_`r'\VG250_KRS_Area.csv", clear
			keep `1' area_km2
			save `area'
		restore
		merge m:1 `1' using `area'
		keep if _merge==3
		drop _merge
		}
	
	
* MERGE ADMINISTRATIVE REGION INFO
**********************************

/* See merge_adm_reg.ado for a description of the procedure. */

	if "`r'"=="Counties" | "`r'"=="Municipalities" {
		merge_adm_reg `1', regionlevel(`"`r'"')
		}
		
		
* SAVE DATA
***********

	order `1' year
	compress
	save "${DATA}\303_surface_`r'.dta", replace
	
	}
	

* CALCULATE DESCRIPTIVES ON PIXELS PER SURFACE GROUP
****************************************************

// paper section "Features of Surface Groups"

use "${DATA}\303_surface_Counties.dta", clear

foreach x of varlist *_px {
	by year, sort: egen double total_`x' = total(`x')
	}
	
duplicates drop year, force
keep year total_*_px
	
/* Not all counties have an observation for few years in the 1980s due to 
missings in Landsat. Therefore, set total_total_px to max(total_total_px) and 
add difference to total_cloud_px in each year. */
	
qui sum total_total_px
local max = `r(max)'
qui levelsof year, local(yearlev)
foreach y of numlist `yearlev' {
	qui sum total_total_px if year==`y'
	local diff = `max'-`r(mean)'
	replace total_cloud_px = total_cloud_px+`diff' if year==`y'
	replace total_total_px = total_total_px+`diff' if year==`y'
	}

qui sum total_total_px
di "One year comprises " %11.0fc `r(mean)' " Landsat pixels."

foreach x of varlist total_* {
	egen double totalall_`x' = total(`x')
	}
	
keep totalall*
duplicates drop

qui sum totalall_total_total_px
local totalmean = `r(mean)'
di "The output data contains " %14.0fc `totalmean' " Landsat pixels."

foreach x in builtup grass crops forest noveg water cloud {
	qui sum totalall_total_`x'_px
	local pct = (`r(mean)'/`totalmean')*100
	di `pct'
	di "Of all observations, " %2.1fc `pct' " are classified as `x'."
	}
	
// papers "Materials and Methods", numbers on outlier removal

use "${DATA}\303_surface_Counties.dta", clear
local N_orig = _N
gen pct_cloud = cloud_px/total_px
by AGS, sort: egen median_builtup_px = median(builtup_px)
drop if (builtup_px>2*median_builtup_px | pct_cloud>0.1) & year<=1990
local N_drop = _N
local pct_drop = ((`N_orig'-`N_drop')/`N_orig')*100
di "At county level, `pct_drop' percent of observations removed as outliers."

use "${DATA}\303_surface_Municipalities.dta", clear
local N_orig = _N
gen pct_cloud = cloud_px/total_px
by AGS, sort: egen median_builtup_px = median(builtup_px)
drop if (builtup_px>2*median_builtup_px | pct_cloud>0.1) & year<=1990
local N_drop = _N
local pct_drop = ((`N_orig'-`N_drop')/`N_orig')*100
di "At municipality level, `pct_drop' percent of observations removed as outliers."
	
	
* CLOSE LOG
***********

cap log close
