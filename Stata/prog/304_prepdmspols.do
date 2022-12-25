********************************************************************************
* 304_prepdmspols.do                                                           *
********************************************************************************

/* This file imports and aggregates the DMSP OLS night light intensity CSV files 
produced with ArcGIS (project arcy_SatDataAggregation). */


* START LOG
***********

cap log close
log using "${LOG}\304_prepdmspols_${c_date}.log", replace

	
* IMPORT AND MERGE DATA
***********************

local start = ${begdmsp}
local end = ${enddmsp}

foreach r in Counties Grid Municipalities {
	
	clear
	
	local files : dir "${GIS_SURFACE}\Germany\csv\Germany_`r'" files "*DMSPOLS*.csv"
	
	foreach f in `files' {
		
		preserve
		
			tempfile tmp
			
			import delim using "${GIS_SURFACE}\Germany\csv\Germany_`r'\\`f'", clear
			
			foreach y of numlist `start'(1)`end' {
				if strpos("`f'","`y'")!=0 {
					gen year = `y'
					gen satellite = substr("`f'",strpos("`f'","`y'")-3,3)
					}
				}
			
			save `tmp'
			
		restore
		
		append using `tmp'
		
		}
		
	ren count count_dmsp	
		
	qui ds
	tokenize `r(varlist)'
	keep `2' year mean satellite count_dmsp
	order `2' year mean satellite count_dmsp
	
	foreach x of varlist mean count_dmsp {
		replace `x' = subinstr(`x',",",".",.)
		destring `x', replace force
		}
	
	
* CALCULATE AVERAGE OF YEARS WITH MORE THAN ONE SATELLITE
*********************************************************

/* Analogous to Henderson et al. (2012). */

	by `2' year, sort: egen dmsp_int = mean(mean)
	by `2' year, sort: egen meansat_count = mean(count_dmsp)
	assert meansat_count == count_dmsp
	by `2', sort: egen meanreg_count = mean(count_dmsp)
	assert meanreg_count == count_dmsp
	drop mean satellite meanreg_count meansat_count
	duplicates drop
	
	
* MERGE ADMINISTRATIVE REGION INFO
**********************************

/* See merge_adm_reg.ado for a description of the procedure. */

	if "`r'"=="Counties" | "`r'"=="Municipalities" {
		merge_adm_reg `2', regionlevel(`"`r'"')
		}
		
		
* SAVE DATA
***********

	sort `2' year
	compress
	save "${DATA}\304_dmspols_`r'.dta", replace
	
	}

	
* CLOSE LOG
***********

cap log close
