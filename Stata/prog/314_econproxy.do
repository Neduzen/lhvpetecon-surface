********************************************************************************
* 314_econproxy.do                                                             *
********************************************************************************

/* This file produces the results in section "Surface Groups Economic Proxy". */


* START LOG
***********

cap log close
log using "${LOG}\314_econproxy_${c_date}.log", replace


* LOAD DATA
***********

use KRS year ln_gdp prsg_lg_ln_gdp builtup_px pct_cloud using "${DATA}\309_predictgdp_Counties.dta", clear


* POTENTIAL UNDETECTED CLOUD COVER CORRECTION
*********************************************

by KRS, sort: egen median_builtup_px = median(builtup_px)
replace prsg_lg_ln_gdp = . if builtup_px>2*median_builtup_px | pct_cloud>0.1
gen miss_prsg = (builtup_px>2*median_builtup_px) | pct_cloud>0.1


* CALCULATE MOVING AVERAGES
***************************
	
sort KRS year
gen Ngdp = 3-miss_prsg[_n-1]-miss_prsg[_n]-miss_prsg[_n+1] if KRS==KRS[_n-1] & KRS==KRS[_n+1]
replace prsg_lg_ln_gdp = 0 if mi(prsg_lg_ln_gdp) & year>=${begsg} & year<=${endsg}
gen prsg_lg_ln_gdp_ma = (prsg_lg_ln_gdp+prsg_lg_ln_gdp[_n-1]+prsg_lg_ln_gdp[_n+1])/Ngdp if KRS==KRS[_n-1] & KRS==KRS[_n+1] // 3-year moving average
gen ln_gdp_ma = (ln_gdp+ln_gdp[_n-1]+ln_gdp[_n+1])/3 if KRS==KRS[_n-1] & KRS==KRS[_n+1]
	
	
* KEEP COUNTIES IN PAPER FIG. 3
*******************************
	
keep if KRS==6433 | KRS==9262 | KRS==13003 | KRS==15083  // Gross-Gerau | Passau | Rostock | Börde

* These are the data underlying Fig. 3


* LEFT-OUT SAMPLE PREDICTIONS GDP
*********************************

set seed 8732823

use "${DATA}\306_regsample_Counties.dta", clear

local ln_surface_px c.ln_builtup_px c.ln_grass_px c.ln_crops_px c.ln_forest_px c.ln_noveg_px c.ln_water_px
local dec = 3

local minyear = max(${beggdp},${begdmsp},${begsg}) 
local maxyear = min(${endgdp},${enddmsp},${endsg})
drop if year<`minyear' | year>`maxyear'
drop if mi(ln_gdp)

*** COMPLETELY RANDOM SPLIT IN HALFS (USED IN LH WP AND IZA DP VERSION OF THE MANUSCRIPT)
gen srandom = round(runiform(),1)

// surface groups

reg ln_gdp `ln_surface_px' i.year i.BULA if srandom==1, vce(r)
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.year
	testparm i.BULA
	predict xb_s_sg
reg ln_gdp c.xb_s_sg i.year i.BULA if srandom==0, vce(r)
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.year
	testparm i.BULA
	
// night light intensity
	
reg ln_gdp c.ln_dmsp_int i.year i.BULA if srandom==1, vce(r)
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.year
	testparm i.BULA
	predict xb_s_dmsp
reg ln_gdp c.xb_s_dmsp i.year i.BULA if srandom==0, vce(r)
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.year
	testparm i.BULA
	
*** RANDOM SAMPLE OF REGIONS (USED IN PNAS NEXUS VERSION)
preserve
	tempfile tmp
	keep KRS
	duplicates drop
	gen regrandom = runiform()*100
	keep KRS regrandom
	save `tmp'
restore
merge m:1 KRS using `tmp', nogen

* choose which percentages of the sample to be used as training sample (0<pct<=50)
local pct 25

foreach p of numlist `pct' {
	
	local pname = subinstr("`p'",".","_",.)
	
	di "`p'% sample surface groups"
	
	reg ln_gdp `ln_surface_px' i.year i.BULA if regrandom<=`p', vce(r)		// Table S20, column 1
		di "Adj. R2: " %4.`dec'fc e(r2_a)
		testparm i.year
		testparm i.BULA
		predict xb_r`pname'_sg
	reg ln_gdp c.xb_r`pname'_sg i.year i.BULA if regrandom>50, vce(r)		// Table S20, column 2
		di "Adj. R2: " %4.`dec'fc e(r2_a)
		testparm i.year
		testparm i.BULA
	
	di "`p'% sample night light intensity"
	
	reg ln_gdp c.ln_dmsp_int i.year i.BULA if regrandom<=`p', vce(r)		// Table S20, column 3
		di "Adj. R2: " %4.`dec'fc e(r2_a)
		testparm i.year
		testparm i.BULA
		predict xb_r`pname'_dmsp
	reg ln_gdp c.xb_r`pname'_dmsp i.year i.BULA if regrandom>50, vce(r)		// Table S20, column 4
		di "Adj. R2: " %4.`dec'fc e(r2_a)
		testparm i.year
		testparm i.BULA
	
	}
	
	
* FULL-SAMPLE GDP PREDICTION
****************************

use "${DATA}\306_regsample_Counties.dta", clear

local ln_surface_px c.ln_builtup_px c.ln_grass_px c.ln_crops_px c.ln_forest_px c.ln_noveg_px c.ln_water_px
local dec = 3

reg ln_gdp `ln_surface_px' c.pct_cloud i.year i.BULA, vce(r)	// Table S22
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.year
	testparm i.BULA
	
	
* LEFT-OUT SAMPLE PREDICTIONS HOUSEHOLD INCOME
**********************************************

set seed 3943249

use "${DATA}\306_regsample_Grid.dta", clear

local ln_surface_px c.ln_builtup_px c.ln_grass_px c.ln_crops_px c.ln_forest_px c.ln_noveg_px c.ln_water_px
local dec = 3

local minyear = max(${beghhi},${begdmsp},${begsg}) 
local maxyear = min(${endhhi},${enddmsp},${endsg})
drop if year<`minyear' | year>`maxyear'
drop if mi(ln_hhi)

*** COMPLETELY RANDOM SPLIT IN HALFS (USED IN LH WP AND IZA DP VERSION OF THE MANUSCRIPT)
gen srandom = round(runiform(),1)

// surface groups

reg ln_hhi `ln_surface_px' i.year i.BULA if srandom==1, vce(r)
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.year
	testparm i.BULA
	predict xb_s_sg
reg ln_hhi c.xb_s_sg i.year i.BULA if srandom==0, vce(r)
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.year
	testparm i.BULA
	
// night light intensity
	
reg ln_hhi c.ln_dmsp_int i.year i.BULA if srandom==1, vce(r)
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.year
	testparm i.BULA
	predict xb_s_dmsp
reg ln_hhi c.xb_s_dmsp i.year i.BULA if srandom==0, vce(r)
	di "Adj. R2: " %4.`dec'fc e(r2_a)
	testparm i.year
	testparm i.BULA
	
*** RANDOM SAMPLE OF REGIONS (USED IN PNAS NEXUS VERSION)
preserve
	tempfile tmp
	keep cell_id
	duplicates drop
	gen regrandom = runiform()*100
	keep cell_id regrandom
	save `tmp'
restore
merge m:1 cell_id using `tmp', nogen

* choose which percentages of the sample to be used as training sample (0<pct<=50)
local pct 25

foreach p of numlist `pct' {
	
	local pname = subinstr("`p'",".","_",.)
	
	di "`p'% sample surface groups"
	
	reg ln_hhi `ln_surface_px' i.year i.BULA if regrandom<=`p', vce(r)		// Table S21, column 1
		di "Adj. R2: " %4.`dec'fc e(r2_a)
		testparm i.year
		testparm i.BULA
		predict xb_r`pname'_sg
	reg ln_hhi c.xb_r`pname'_sg i.year i.BULA if regrandom>50, vce(r)		// Table S21, column 2
		di "Adj. R2: " %4.`dec'fc e(r2_a)
		testparm i.year
		testparm i.BULA
	
	di "`p'% sample night light intensity"
	
	reg ln_hhi c.ln_dmsp_int i.year i.BULA if regrandom<=`p', vce(r)		// Table S21, column 3
		di "Adj. R2: " %4.`dec'fc e(r2_a)
		testparm i.year
		testparm i.BULA
		predict xb_r`pname'_dmsp
	reg ln_hhi c.xb_r`pname'_dmsp i.year i.BULA if regrandom>50, vce(r)		// Table S21, column 4
		di "Adj. R2: " %4.`dec'fc e(r2_a)
		testparm i.year
		testparm i.BULA
	
	}


* CLOSE LOG
***********

cap log close
