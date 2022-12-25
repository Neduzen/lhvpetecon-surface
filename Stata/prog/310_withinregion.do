********************************************************************************
* 310_withinregion.do                                                          *
********************************************************************************

/* This file contains the analyses on within-region predictive power. */


* START LOG
***********

cap log close
log using "${LOG}\310_withinregion_${c_date}.log", replace


* STANDARDIZATION
*****************

use "${DATA}\306_regsample_Municipalities.dta", clear
foreach x of varlist *_px *_int {
	center `x', gen(std_`x') standardize
	}
	
preserve
	tempfile std_Counties
	use "${DATA}\306_regsample_Counties.dta", clear
	foreach x of varlist *gdp *_px *_int {
		center `x', gen(std_`x') standardize
		}
	save `std_Counties'
restore


* MUNICIPALITY-LEVEL PREDICTION
*******************************

append using `std_Counties', gen(_append)

local std_ln_surface_px c.std_ln_builtup_px c.std_ln_grass_px c.std_ln_crops_px c.std_ln_forest_px c.std_ln_noveg_px c.std_ln_water_px
local dec = 3
local starty = max(${beggdp},${begdmsp})
local endy = min(${endgdp},${enddmsp})
 
reg std_ln_gdp `std_ln_surface_px' if year>=`starty' & year<=`endy' & _append==1, vce(r) 				// Table S17, column 1
	di "Adj. R2: " %4.`dec'fc e(r2_a)
reg std_ln_gdp `std_ln_surface_px' i.year i.BULA if year>=`starty' & year<=`endy' & _append==1, vce(r) 	// Table S17, column 2
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.BULA
	testparm i.year
	predict prsg_std_ln_gdp
reg std_ln_gdp c.std_ln_dmsp_int if year>=`starty' & year<=`endy' & _append==1, vce(r)					// Table S17, column 3
	di "Adj. R2: " %4.`dec'fc e(r2_a)
reg std_ln_gdp c.std_ln_dmsp_int i.year i.BULA if year>=`starty' & year<=`endy' & _append==1, vce(r) 	// Table S17, column 4
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.BULA
	testparm i.year
	predict prdmsp_std_ln_gdp
	
drop if _append==1


* CALCULATE 2000 - 2013 DIFFERENCES
***********************************

// Municipality level

local t0 = max(${beggdp},${begsg},${begdmsp})
local t1 = min(${endgdp},${endsg},${enddmsp})

drop if year<`t0' | year>`t1'

keep AGS year pr*
reshape wide pr*, i(AGS) j(year)

keep AGS *`t0' *`t1'

foreach x in prsg_std_ln_gdp prdmsp_std_ln_gdp {
	gen tchange_`x'_AGS = `x'`t1'-`x'`t0'
	}

// County level

preserve
	tempfile tmp
	use `std_Counties', clear
	drop if year<`t0' | year>`t1'
	keep KRS year std_ln_gdp
	reshape wide std_ln_gdp, i(KRS) j(year)
	keep KRS std_ln_gdp`t0' std_ln_gdp`t1'
	gen tchange_std_ln_gdp_KRS = std_ln_gdp`t0'-std_ln_gdp`t1'
	keep KRS tchange_std_ln_gdp_KRS
	save `tmp'
restore

// Merge county to municipality level

tostring AGS, gen(KRS)
replace KRS = "0"+KRS if strlen(KRS)==7
replace KRS = substr(KRS,1,5)
destring KRS, replace force

merge m:1 KRS using `tmp', nogen
foreach x of varlist tchange* {
	drop if mi(`x') // for fair comparison; drops e.g. counties of Thuringia which do not have 2000 observations
	}


* CALCULATE MUNICIPALITY-COUNTY DEVIATION
*****************************************

// Calculation

foreach x in sg dmsp {
	gen dev_`x' = tchange_pr`x'_std_ln_gdp_AGS-tchange_std_ln_gdp_KRS
	*qui sum dev_`x'
	*gen c_dev_`x' = dev_`x'-`r(mean)'
	kdensity dev_`x', kernel(epanechnikov) bwidth(0.025) n(300) generate(kden_dev_`x'_x kden_dev_`x'_y)
	}
	
* These are the data underlying Fig. S8
	
	
* DATA FOR WUNSIEDEL COUNTY
***************************

keep if KRS==9479
drop *KRS
tostring AGS, replace force
replace AGS = "0"+AGS if strlen(AGS)==7

* These are the data underlying Fig. S9


* CLOSE LOG
***********

cap log close
