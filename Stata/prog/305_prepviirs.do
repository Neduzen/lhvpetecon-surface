********************************************************************************
* 305_prepviirs.do                                                             *
********************************************************************************

/* This file imports and aggregates the VIIRS night light intensity CSV files 
produced with ArcGIS (project arcy_SatDataAggregation). */


* START LOG
***********

cap log close
log using "${LOG}\305_prepviirs_${c_date}.log", replace

	
* IMPORT AND MERGE DATA
***********************

local start = ${begviirs}
local end = ${endviirs}

foreach r in Counties Grid Municipalities {
	
	clear
	
	local files : dir "${GIS_SURFACE}\Germany\csv\Germany_`r'" files "*VIIRS*.csv"
	
	foreach f in `files' {
		
		preserve
		
			tempfile tmp
			
			import delim using "${GIS_SURFACE}\Germany\csv\Germany_`r'\\`f'", clear
			
			foreach y of numlist `start'(1)`end' {
				if strpos("`f'","`y'")!=0 gen year = `y'
				}
			
			save `tmp'
			
		restore
		
		append using `tmp'
		
		}
		
	qui ds
	tokenize `r(varlist)'
	keep `2' year mean
	order `2' year mean
	drop if mi(year) // 2013 VIIRS data, which are not complete for Germany and cover a different time span
	
	replace mean = subinstr(mean,",",".",.)
	destring mean, replace force
	ren mean viirs_int
	
	
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
	save "${DATA}\305_viirs_`r'.dta", replace
	
	}

	
* CLOSE LOG
***********

cap log close
