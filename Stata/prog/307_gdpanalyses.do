********************************************************************************
* 307_dgpanalyses.do                                                           *
********************************************************************************

/* This file contains all county-level analyses of GDP. */


* START LOG
***********

cap log close
log using "${LOG}\307_gdpanalyses_${c_date}.log", replace


* LOAD DATA
***********

use "${DATA}\306_regsample_Counties.dta", clear

local ln_surface_px c.ln_builtup_px c.ln_grass_px c.ln_crops_px c.ln_forest_px c.ln_noveg_px c.ln_water_px
local dec = 3


* OLS PREDICTION OF GDP USING SURFACE GROUPS AND USING DMSP OLS NIGHT LIGHT 
* INTENSITY (COUNTY-LEVEL, 2000-2013)
***************************************************************************

// regressions

local starty = max(${beggdp},${begdmsp})
local endy = min(${endgdp},${enddmsp})
 
reg ln_gdp `ln_surface_px' if year>=`starty' & year<=`endy', vce(r) 				// Table S9, column 1
	di "Adj. R2: " %4.`dec'fc e(r2_a)
reg ln_gdp `ln_surface_px' i.year i.BULA if year>=`starty' & year<=`endy', vce(r) 	// Table S9, column 2
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	predict res_ln_gdp_sg if e(sample), res
	testparm i.BULA
	testparm i.year
reg ln_gdp c.ln_dmsp_int if year>=`starty' & year<=`endy', vce(r)					// Table S9, column 3
	di "Adj. R2: " %4.`dec'fc e(r2_a)
reg ln_gdp c.ln_dmsp_int i.year i.BULA if year>=`starty' & year<=`endy', vce(r) 	// Table S9, column 4
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	predict res_ln_gdp_dmsp if e(sample), res
	testparm i.BULA
	testparm i.year
	
reg ln_gdp `ln_surface_px' c.pct_cloud if year>=`starty' & year<=`endy', vce(r) 				// Table S25, column 1
	di "Adj. R2: " %4.`dec'fc e(r2_a)
reg ln_gdp `ln_surface_px' c.pct_cloud  i.year i.BULA if year>=`starty' & year<=`endy', vce(r) 	// Table S25, column 2
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.BULA
	testparm i.year
	
// histograms (paper Figs. 2 A and 2 B)

foreach s in sg dmsp {
	
	histogram res_ln_gdp_`s', w(0.05) frac
	
	}

// spatial bias

tempfile start
keep if !mi(res_ln_gdp_sg)  // keep only observations in regression sample
foreach x in sg dmsp {
    gen `x'_up = res_ln_gdp_`x'>0
	gen `x'_down = res_ln_gdp_`x'<0
	}
save `start'

tempfile tmp_res
keep KRS year *_up *_down
foreach x of varlist KRS *_up *_down {
	ren `x' `x'_nbr
	}
save `tmp_res'
	
tempfile tmp_nbr
import delimited using "${GIS_SURFACE}\Germany\csv\Germany_Counties\VG250_KRS_Neighbors.csv", clear delim(";")
foreach x in src nbr {
	merge_adm_reg `x'_debkg_id, regionlevel("Counties")
	ren AGS KRS_`x'
	}
drop if KRS_src==KRS_nbr
keep KRS_src KRS_nbr
save `tmp_nbr'

forval y = `starty'(1)`endy' {
    tempfile tmp_`y'
	use `tmp_nbr', clear
	gen year = `y'
	merge m:1 KRS_nbr year using `tmp_res'
	keep if _merge==3
	drop _merge
	by KRS_src, sort: gen N = _N
	foreach x of varlist *_up_nbr *_down_nbr {
		by KRS_src, sort: egen total_`x' = total(`x')
		}
	foreach s in sg dmsp {
		foreach d in up down {
			gen `s'_all`d' = N == total_`s'_`d'_nbr
			}
		}
	duplicates drop KRS_src, force
	keep KRS_src year *_all*
	save `tmp_`y''
	}

clear
tempfile end
forval y = `starty'(1)`endy' {
	append using `tmp_`y''
	}
ren KRS_src KRS
save `end'

use `start', clear
merge 1:1 KRS year using `end'
drop if _merge==2
drop _merge

preserve
	tempfile tmp
	use `tmp_nbr', clear
	by KRS_src, sort: gen Nneighbors = _N
	keep KRS_src Nneighbors
	ren KRS_src KRS
	duplicates drop
	save `tmp'
restore
merge m:1 KRS using `tmp'
drop if _merge==2
drop _merge

foreach x in sg dmsp {
	foreach i in up down {
		gen `x'_all`i'same = `x'_`i' == `x'_all`i' & `x'_all`i'==1
		}
	gen `x'_allsame = (`x'_up == `x'_allup & `x'_allup==1) | (`x'_down == `x'_alldown & `x'_alldown==1)
	}
	
// temporal bias

foreach x of varlist sg_up dmsp_up sg_down dmsp_down {
	by KRS, sort: egen total_`x' = total(`x')
	}

// spatial bias over time (combined bias)

foreach x of varlist *allsame *allupsame *alldownsame {
	by KRS, sort: egen total_`x' = total(`x')
	}
	
// display numbers for spatial and temporal bias

foreach s in sg dmsp {
	local N = _N
	count if `s'_allsame==1
	local `s'_spatial_abs : di %12.0fc `r(N)'
	local `s'_spatial_abs = trim("``s'_spatial_abs'")
	local `s'_spatial_rel : di %2.1fc (`r(N)'/`N')*100
	preserve
		duplicates drop KRS, force
		local N = _N
		qui sum total_`s'_up
		count if total_`s'_up==`r(min)'
		local Nmin = `r(N)'
		qui sum total_`s'_up
		count if total_`s'_up==`r(max)'
		local Nmax = `r(N)'
		local `s'_temporal_abs : di %12.0fc `Nmin'+`Nmax'
		local `s'_temporal_abs = trim("``s'_temporal_abs'")
		local `s'_temporal_rel : di %2.1fc ((`Nmin'+`Nmax')/`N')*100
		qui sum total_`s'_allsame
		count if total_`s'_allsame==`r(max)'
		local `s'_combined_abs : di %12.0fc `r(N)'
		local `s'_combined_abs = trim("``s'_combined_abs'")
		local `s'_combined_rel : di %2.1fc (`r(N)'/`N')*100
	restore
	}
	
* These are the data underlying Figs. S3 and S4.

di "For surface groups, `sg_temporal_abs' counties (`sg_temporal_rel'%) have the same color over the entire observation period."
di "For DMSP OLS night light intensity, `dmsp_temporal_abs' counties (`dmsp_temporal_rel'%) have the same color over the entire observation period."
di "For surface groups, `sg_spatial_abs' observations (`sg_spatial_rel'%) have the same color as all their geographically neighboring observations."
di "For DMSP OLS night light intensity, `dmsp_spatial_abs' observations (`dmsp_spatial_rel'%) have the same color as all their geographically neighboring observations."
di "For surface groups, `sg_combined_abs' counties (`sg_combined_rel'%) have the same color as all their neigboring observations and the same color throughout all observation years."
di "For DMSP OLS night light intensity, `dmsp_combined_abs' counties (`dmsp_combined_rel'%) have the same color as all their neigboring observations and the same color throughout all observation years."

// by area size quintile

preserve
	tempfile tmp
	drop if mi(res_ln_gdp_sg) // only observation in original regression sample
	keep if year==2013
	xtile xt5_area = area, nq(5)
	keep KRS xt5_area
	save `tmp'
restore

preserve

	drop if mi(res_ln_gdp_sg) // only observation in original regression sample
	merge m:1 KRS using `tmp', nogen

	gen avg_area_xt5 = .
	gen AR2_xt5_sg = .
	gen AR2_xt5_dmsp = .
	qui levelsof xt5_area, local(xt5lev)
	foreach j of numlist `xt5lev' {
		qui sum area if xt5_area==`j'
		replace avg_area_xt5 = `r(mean)' if xt5_area==`j'
		qui reg ln_gdp `ln_surface_px' i.year if xt5_area==`j', vce(r)
		replace AR2_xt5_sg = `e(r2_a)' if xt5_area==`j'
		qui reg ln_gdp c.ln_dmsp_int i.year if xt5_area==`j', vce(r)
		replace AR2_xt5_dmsp = `e(r2_a)' if xt5_area==`j'
		}
		
	keep xt5_area avg_area_xt5 AR2_xt5_*
	duplicates drop
	sum avg_area
	sort avg_area_xt5
	* These are the data underlying Fig. S5 A.
	
restore

// estimations by federal state

preserve
	
	drop if mi(res_ln_gdp_sg) // only observation in original regression sample
	
	qui levelsof BULA, local(BULAlev)
	gen avg_area_BULA = .
	gen AR2_BULA_sg = .
	gen AR2_BULA_dmsp = .
	
	foreach j of numlist `BULAlev' {
		qui sum area_km2 if BULA==`j'
		di "BULA: `j'"
		replace avg_area_BULA = `r(mean)' if BULA==`j'
		qui reg ln_gdp `ln_surface_px' i.year if BULA==`j', vce(r)
		replace AR2_BULA_sg = `e(r2_a)' if BULA==`j'
		qui reg ln_gdp c.ln_dmsp_int i.year if BULA==`j', vce(r)
		replace AR2_BULA_dmsp = `e(r2_a)' if BULA==`j'
		}

	keep BULA avg_area_BULA AR2_BULA_*
	duplicates drop
	drop if BULA==4 // Bremen, only 2 counties
	sort avg_area_BULA
	* These are the data underlying Fig. S5 B.
	
restore


* OLS PREDICTION OF GDP USING SURFACE GROUPS AND USING VIIRS NIGHT LIGHT 
* INTENSITY (COUNTY-LEVEL, 2014-2018)
************************************************************************

use "${DATA}\306_regsample_Counties.dta", clear */

local starty = max(${beggdp},${begviirs})
local endy = min(${endgdp},${endviirs})

reg ln_gdp `ln_surface_px' if year>=`starty' & year<=`endy', vce(r) 				// Table S11, column 1
	di "Adj. R2: " %4.`dec'fc e(r2_a)
reg ln_gdp `ln_surface_px' i.year i.BULA if year>=`starty' & year<=`endy', vce(r) 	// Table S11, column 2
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.BULA
	testparm i.year
reg ln_gdp c.ln_viirs_int if year>=`starty' & year<=`endy', vce(r)					// Table S11, column 3
	di "Adj. R2: " %4.`dec'fc e(r2_a)
reg ln_gdp c.ln_viirs_int i.year i.BULA if year>=`starty' & year<=`endy', vce(r) 	// Table S11, column 4
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.BULA
	testparm i.year
	
	
* FE PREDICTION OF GDP USING SURFACE GROUPS AND USING DMSP OLS NIGHT LIGHT 
* INTENSITY (COUNTY-LEVEL, 2000-2013)
**************************************************************************

local starty = max(${beggdp},${begdmsp})
local endy = min(${endgdp},${enddmsp})
local dec = 3

xtset KRS year
areg ln_gdp i.year if year>=`starty' & year<=`endy', absorb(KRS) vce(r)					// Table S15, column 1
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.year
xtreg ln_gdp i.year if year>=`starty' & year<=`endy', vce(r) fe							// Table S15, column 4
	di "Adj. R2: " %4.`dec'fc e(r2_w)
	testparm i.year
areg ln_gdp `ln_surface_px' i.year if year>=`starty' & year<=`endy', absorb(KRS) vce(r)	// Table S15, column 2
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.year
xtreg ln_gdp `ln_surface_px' i.year if year>=`starty' & year<=`endy', vce(r) fe			// Table S15, column 5
	di "Adj. R2: " %4.`dec'fc e(r2_w)
	testparm i.year
areg ln_gdp c.ln_dmsp_int i.year if year>=`starty' & year<=`endy', absorb(KRS) vce(r)	// Table S15, column 3
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.year
xtreg ln_gdp c.ln_dmsp_int i.year if year>=`starty' & year<=`endy', vce(r) fe			// Table S15, column 6
	di "Adj. R2: " %4.`dec'fc e(r2_w)
	testparm i.year
	
	
* COMPARISON TO GHSL DATA
*************************

reg ln_gdp `ln_surface_px' i.year i.BULA if !mi(ln_built_s_sum), vce(r) 		// Table S13, column 1
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.BULA
	testparm i.year

reg ln_gdp c.ln_built_s_sum i.year i.BULA, vce(r) 								// Table S13, column 2
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.BULA
	testparm i.year
	
reg ln_gdp c.ln_built_v_sum i.year i.BULA, vce(r) 								// Table S13, column 3
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.BULA
	testparm i.year

reg ln_gdp `ln_surface_px' c.ln_built_v_sum c.pct_cloud i.year i.BULA, vce(r)	// Table S23 	
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.BULA
	testparm i.year


* CLOSE LOG
***********

cap log close
