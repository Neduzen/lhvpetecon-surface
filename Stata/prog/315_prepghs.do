********************************************************************************
* 315_prepghs.do                                                               *
********************************************************************************

/* This file imports and aggregates the GHS CSV files produced with ArcGIS 
(project arcy_SatDataAggregation). */


* START LOG
***********

cap log close
log using "${LOG}\315_prepghs_${c_date}.log", replace

	
* IMPORT AND MERGE DATA
***********************

local start = ${begghs}
local end = ${endghs}

local models BUILT_S BUILT_V

foreach r in Counties Grid Municipalities {
	
	foreach b in `models' {
		
		tempfile tmp_`b'
	
		clear
	
		local files : dir "${GIS_SURFACE}\Germany\csv\Germany_`r'" files "*`b'*.csv"
	
		foreach f in `files' {
		
			preserve
		
				tempfile tmp
			
				import delim using "${GIS_SURFACE}\Germany\csv\Germany_`r'\\`f'", clear
			
				foreach y of numlist `start'(5)`end' {
					if strpos("`f'","`y'")!=0 gen year = `y'
					}
			
				save `tmp'
			
			restore
		
			append using `tmp'
		
			}
		
		local varn = strlower("`b'")+"_sum"
		ren sum `varn'
		
		qui ds
		tokenize `r(varlist)'
		keep `2' year `varn'
		order `2' year `varn'
	
		replace `varn' = subinstr(`varn',",",".",.)
		destring `varn', replace force
		
		save `tmp_`b''
		
		}
		
	clear
	use `tmp_BUILT_S'
	merge 1:1 `2' year using `tmp_BUILT_V'
	assert _merge==3
	drop _merge
	
		
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
	save "${DATA}\315_ghs_`r'.dta", replace
	
	}

	
* CLOSE LOG
***********

cap log close
