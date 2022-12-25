********************************************************************************
* 306_regsamples.do                                                            *
********************************************************************************

/* This file merges the economic activity, surface groups, DMSP OLS night light 
intensity, VIIRS night light intensity, and GHSL built-up land cover for use in 
the regression analyses. */


* START LOG
***********

cap log close
log using "${LOG}\306_regsamples_${c_date}.log", replace


* MERGE COUNTY-LEVEL DATASETS
*****************************

local surface_px builtup_px crops_px forest_px grass_px noveg_px water_px

use "${DATA}\301_gdp.dta", clear
ren KRS AGS

merge 1:1 AGS year using "${DATA}\303_surface_Counties.dta"
assert mi(gdp) if _merge==1
drop _merge

merge 1:1 AGS year using "${DATA}\304_dmspols_Counties.dta", nogen

merge 1:1 AGS year using "${DATA}\305_viirs_Counties.dta", nogen

merge 1:1 AGS year using "${DATA}\315_ghs_Counties.dta", nogen

foreach x of varlist `surface_px' dmsp_int viirs_int built_* {
	gen ln_`x' = ln(`x'+1)
	order ln_`x', a(`x')
	}
gen ln_gdp = ln(gdp)

gen pct_cloud = cloud_px/total_px
order pct_cloud, a(cloud_px)

tostring AGS, gen(str_BULA)
replace str_BULA = "0"+str_BULA if strlen(str_BULA)==4
replace str_BULA = substr(str_BULA,1,2)
destring str_BULA, replace force
replace BULA = str_BULA
drop str_BULA

ren AGS KRS
compress
save "${DATA}\306_regsample_Counties.dta", replace


* MERGE MUNICIPALITY-LEVEL DATASETS
***********************************

use "${DATA}\303_surface_Municipalities.dta", clear

merge 1:1 AGS year using "${DATA}\304_dmspols_Municipalities.dta", nogen

merge 1:1 AGS year using "${DATA}\305_viirs_Municipalities.dta", nogen

merge 1:1 AGS year using "${DATA}\315_ghs_Municipalities.dta", nogen

foreach x of varlist `surface_px' dmsp_int viirs_int built_* {
	gen ln_`x' = ln(`x'+1)
	order ln_`x', a(`x')
	}
	
gen pct_cloud = cloud_px/total_px
order pct_cloud, a(cloud_px)

tostring AGS, gen(BULA)
replace BULA = "0"+BULA if strlen(BULA)==7
replace BULA = substr(BULA,1,2) // first two digits of municipality ID indicate federal state
destring BULA, replace force
L_BULA
la var BULA "federal state ID"

compress
save "${DATA}\306_regsample_Municipalities.dta", replace


* MERGE GRID-LEVEL DATASETS
***************************

use "${DATA}\302_hhi.dta", clear

merge 1:1 cell_id year using "${DATA}\303_surface_Grid.dta"
drop if _merge==1  // grid cells without surface group observation (e.g., GEE's Germany shape)
drop _merge

merge 1:1 cell_id year using "${DATA}\304_dmspols_Grid.dta", nogen

merge 1:1 cell_id year using "${DATA}\305_viirs_Grid.dta", nogen

merge 1:1 cell_id year using "${DATA}\315_ghs_Grid.dta", nogen

foreach x of varlist `surface_px' dmsp_int viirs_int built_* {
	gen ln_`x' = ln(`x'+1)
	order ln_`x', a(`x')
	}
gen ln_hhi = ln(hhi)
	
gen pct_cloud = cloud_px/total_px
order pct_cloud, a(cloud_px)

preserve
	tempfile gridadm
	import delim using "${GIS_SURFACE}\Germany\csv\Germany_Grid\grid_germany_etrs_laea_1k_in_VG250_LAN.csv", delim(",") varn(1) clear
	local N = _N
	save `gridadm'
restore
	
merge m:1 cell_id using `gridadm'
assert _merge!=2
keep if _merge==3 // master only: grid cells with centroid not in Germany 
drop _merge
ren rs BULA
L_BULA
la var BULA "federal state ID"

local minN = `N'
local maxN = 0
local ymin = max(${begsg},${beghhi},${begdmsp})
local ymax = min(${endsg}${endhhi},${enddmsp})
forval y = `ymin'(1)`ymax' {
    qui sum hhi if year==`y'
	if `r(N)'<`minN' local minN = `r(N)'
	if `r(N)'>`maxN' local maxN = `r(N)'
	}
* Statistics in supplementary material (section "Validation Data")
di "Germany comprises " `N' " grid cells, between " `minN' " and " `maxN' " of which (depending on the year) contain positive values of household income within our observation period."

compress
save "${DATA}\306_regsample_Grid.dta", replace


* CLOSE LOG
***********

cap log close
