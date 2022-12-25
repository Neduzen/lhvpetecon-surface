********************************************************************************
* 308_hhianalyses.do                                                           *
********************************************************************************

/* This file contains all county-level analyses of GDP. */


* START LOG
***********

cap log close
log using "${LOG}\308_hhianalyses_${c_date}.log", replace


* LOAD DATA
***********

use "${DATA}\306_regsample_Grid.dta", clear

local ln_surface_px c.ln_builtup_px c.ln_grass_px c.ln_crops_px c.ln_forest_px c.ln_noveg_px c.ln_water_px
local dec = 3


* OLS PREDICTION OF HOUSEHOLD INCOME USING SURFACE GROUPS AND USING DMSP OLS  
* NIGHT LIGHT INTENSITY (GRID LEVEL, 2009-2013)
****************************************************************************

local starty = max(${beghhi},${begdmsp})
local endy = min(${endhhi},${enddmsp})
 
reg ln_hhi `ln_surface_px' if year>=`starty' & year<=`endy', vce(r) 							// Table S10, column 1
	di "Adj. R2: " %4.`dec'fc e(r2_a)
reg ln_hhi `ln_surface_px' i.year i.BULA if year>=`starty' & year<=`endy', vce(r) 				// Table S10, column 2
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	predict res_ln_hhi_sg if e(sample), res
	testparm i.BULA
	testparm i.year
reg ln_hhi c.ln_dmsp_int if year>=`starty' & year<=`endy', vce(r)								// Table S10, column 3
	di "Adj. R2: " %4.`dec'fc e(r2_a)
reg ln_hhi c.ln_dmsp_int i.year i.BULA if year>=`starty' & year<=`endy', vce(r) 				// Table S10, column 4
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	predict res_ln_hhi_dmsp if e(sample), res
	testparm i.BULA
	testparm i.year
	
reg ln_hhi `ln_surface_px' c.pct_cloud if year>=`starty' & year<=`endy', vce(r) 				// Table S26, column 1
	di "Adj. R2: " %4.`dec'fc e(r2_a)
reg ln_hhi `ln_surface_px' c.pct_cloud  i.year i.BULA if year>=`starty' & year<=`endy', vce(r) 	// Table S26, column 2
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.BULA
	testparm i.year
	
// histogram (paper Figs. 2 C and 2 D)

foreach s in sg dmsp {
	
	histogram res_ln_hhi_`s', w(0.1) frac
		
	}
	
// spatial bias

/* R1_IDs have the following logic: eeee_nnnn 4213_2939
- n digits go south to north
- e digits go west to east */

tempfile start
keep if !mi(res_ln_hhi_sg)  // keep only observations in regression sample
foreach x in sg dmsp {
    gen `x'_up = res_ln_hhi_`x'>0
	gen `x'_down = res_ln_hhi_`x'<0
	}
save `start'

tempfile tmp_res
keep cell_id year *_up *_down
foreach x of varlist cell_id *_up *_down {
	ren `x' `x'_nbr
	}
save `tmp_res'

use `start', clear
tempfile tmp_nbr
keep cell_id
duplicates drop
gen eeee = substr(cell_id,1,4)
gen nnnn = substr(cell_id,6,4)
destring eeee, replace force
destring nnnn, replace force
gen eeee_1 = eeee-1
gen eeee_2 = eeee-1
gen eeee_3 = eeee-1
gen eeee_4 = eeee
gen eeee_5 = eeee
gen eeee_6 = eeee+1
gen eeee_7 = eeee+1
gen eeee_8 = eeee+1
gen nnnn_1 = nnnn+1
gen nnnn_2 = nnnn
gen nnnn_3 = nnnn-1
gen nnnn_4 = nnnn+1
gen nnnn_5 = nnnn-1
gen nnnn_6 = nnnn+1
gen nnnn_7 = nnnn
gen nnnn_8 = nnnn-1
forval j = 1(1)8 {
	tostring eeee_`j', replace force
	tostring nnnn_`j', replace force
	gen cell_id_nbr`j' = eeee_`j'+"_"+nnnn_`j'
	}
drop eeee* nnnn*
expand 8
by cell_id, sort: gen n = _n
gen cell_id_nbr = ""
forval j = 1(1)8 {
	replace cell_id_nbr = cell_id_nbr`j' if n==`j'
	drop cell_id_nbr`j'
	}
drop n
ren cell_id cell_id_src
save `tmp_nbr'

forval y = `starty'(1)`endy' {
    tempfile tmp_`y'
	use `tmp_nbr', clear
	gen year = `y'
	merge m:1 cell_id_nbr year using `tmp_res'
	keep if _merge==3
	drop _merge
	by cell_id_src, sort: gen N = _N
	foreach x of varlist *_up_nbr *_down_nbr {
		by cell_id_src, sort: egen total_`x' = total(`x')
		}
	foreach s in sg dmsp {
		foreach d in up down {
			gen `s'_all`d' = N == total_`s'_`d'_nbr
			}
		}
	duplicates drop cell_id_src, force
	keep cell_id_src year *_all*
	save `tmp_`y''
	}

clear
tempfile end
forval y = `starty'(1)`endy' {
	append using `tmp_`y''
	}
ren cell_id_src cell_id
save `end'

use `start', clear
merge 1:1 cell_id year using `end'
drop if _merge==2
drop _merge

preserve
	tempfile tmp
	use `tmp_nbr', clear
	by cell_id_src, sort: gen Nneighbors = _N
	keep cell_id_src Nneighbors
	ren cell_id_src cell_id
	duplicates drop
	save `tmp'
restore
merge m:1 cell_id using `tmp'
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
	by cell_id, sort: egen total_`x' = total(`x')
	}

// spatial bias over time (combined bias)

foreach x of varlist *allsame *allupsame *alldownsame {
	by cell_id, sort: egen total_`x' = total(`x')
	}
	
// display numbers

foreach s in sg dmsp {
	local N = _N
	count if `s'_allsame==1
	local `s'_spatial_abs : di %12.0fc `r(N)'
	local `s'_spatial_abs = trim("``s'_spatial_abs'")
	local `s'_spatial_rel : di %2.1fc (`r(N)'/`N')*100
	preserve
		duplicates drop cell_id, force
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
	
* These are the data underlying Figs. S6 and S7

di "For surface groups, `sg_temporal_abs' grid cells (`sg_temporal_rel'%) have the same color over the entire observation period."
di "For DMSP OLS night light intensity, `dmsp_temporal_abs' grid cells (`dmsp_temporal_rel'%) have the same color over the entire observation period."
di "For surface groups, `sg_spatial_abs' observations (`sg_spatial_rel'%) have the same color as all their geographically neighboring observations."
di "For DMSP OLS night light intensity, `dmsp_spatial_abs' observations (`dmsp_spatial_rel'%) have the same color as all their geographically neighboring observations."
di "For surface groups, `sg_combined_abs' grid cells (`sg_combined_rel'%) have the same color as all their neigboring observations and the same color throughout all observation years."
di "For DMSP OLS night light intensity, `dmsp_combined_abs' grid cells (`dmsp_combined_rel'%) have the same color as all their neigboring observations and the same color throughout all observation years."


* OLS PREDICTION OF HOUSEHOLD INCOME USING SURFACE GROUPS AND USING VIIRS NIGHT  
* LIGHT INTENSITY (GRID LEVEL, 2014-2016)
*******************************************************************************

use "${DATA}\306_regsample_Grid.dta", clear */

local starty = max(${beghhi},${begviirs})
local endy = min(${endhhi},${endviirs})

reg ln_hhi `ln_surface_px' if year>=`starty' & year<=`endy', vce(r) 							// Table S12, column 1
	di "Adj. R2: " %4.`dec'fc e(r2_a)
reg ln_hhi `ln_surface_px' i.year i.BULA if year>=`starty' & year<=`endy', vce(r) 				// Table S12, column 2
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.BULA
	testparm i.year
reg ln_hhi c.ln_viirs_int if year>=`starty' & year<=`endy', vce(r)								// Table S12, column 3
	di "Adj. R2: " %4.`dec'fc e(r2_a)
reg ln_hhi c.ln_viirs_int i.year i.BULA if year>=`starty' & year<=`endy', vce(r) 				// Table S12, column 4
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.BULA
	testparm i.year
	
	
* FE PREDICTION OF HOUSEHOLD INCOME USING SURFACE GROUPS AND USING DMSP OLS  
* NIGHT LIGHT INTENSITY (GRID LEVEL, 2009-2013)
***************************************************************************

local starty = max(${beghhi},${begdmsp})
local endy = min(${endhhi},${enddmsp})

egen cell_id_g = group(cell_id)
xtset cell_id_g year
areg ln_hhi i.year if year>=`starty' & year<=`endy', absorb(cell_id_g) vce(r)					// Table S16, column 1
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.year
xtreg ln_hhi i.year if year>=`starty' & year<=`endy', vce(r) fe									// Table S16, column 4
	di "Adj. R2: " %4.`dec'fc e(r2_w)
	testparm i.year
areg ln_hhi `ln_surface_px' i.year if year>=`starty' & year<=`endy', absorb(cell_id_g) vce(r)	// Table S16, column 2
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.year
xtreg ln_hhi `ln_surface_px' i.year if year>=`starty' & year<=`endy', vce(r) fe					// Table S16, column 5
	di "Adj. R2: " %4.`dec'fc e(r2_w)
	testparm i.year
areg ln_hhi c.ln_dmsp_int i.year if year>=`starty' & year<=`endy', absorb(cell_id_g) vce(r)		// Table S16, column 3
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.year
xtreg ln_hhi c.ln_dmsp_int i.year if year>=`starty' & year<=`endy', vce(r) fe					// Table S16, column 6
	di "Adj. R2: " %4.`dec'fc e(r2_w)
	testparm i.year
	
	
* COMPARISON TO GHSL DATA
*************************

reg ln_hhi `ln_surface_px' i.year i.BULA if !mi(ln_built_s_sum), vce(r) 		// Table S14, column 1
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.BULA
	testparm i.year

reg ln_hhi c.ln_built_s_sum i.year i.BULA, vce(r) 								// Table S14, column 2
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.BULA
	testparm i.year
	
reg ln_hhi c.ln_built_v_sum i.year i.BULA, vce(r) 								// Table S14, column 3
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.BULA
	testparm i.year

reg ln_hhi `ln_surface_px' c.ln_built_v_sum c.pct_cloud i.year i.BULA, vce(r) 	// Table S24	
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.BULA
	testparm i.year


* CLOSE LOG
***********

cap log close
