********************************************************************************
* 301_prepgdp.do                                                               *
********************************************************************************

/* This file imports the administrative GDP data and creates a county-level
dataset to use for the validation analyses. */


* START LOG
***********

cap log close
log using "${LOG}\301_prepgdp_${c_date}.log", replace

	
* IMPORT AND LABEL DATA
***********************

import excel "${ORIG_GDP}", clear

gen year = A
replace year = "" if strlen(A)!=4
destring year, replace force
replace year = . if year < ${beggdp} | year > ${endgdp}
replace year = year[_n-1] if mi(year)
la var year "year"

replace A = "" if strlen(A)==4
	
gen KRS = A
replace KRS = "" if strlen(KRS)!=5
gen BULA = substr(KRS,1,2) // first two digits of county ID indicate federal state
destring BULA, replace force
L_BULA
la var BULA "federal state ID"
destring KRS, replace force
lab_regio KRS
la var KRS "county ID"

ren C gdp
destring gdp, replace force
replace gdp = gdp*1000
la var gdp "gross domestic product (EUR)"


* DEFLATION TO 2000 PRICES
**************************

preserve
	tempfile vpi
	import excel using "${ORIG_VPI}", clear
	drop C
	destring A, replace force
	destring B, replace force
	drop if mi(A)
	tempvar base
	gen `base' = B if A==2000
	egen base = mean(`base')
	gen defl = base/B
	ren A year
	keep year defl
	drop if year<$beggdp | year>$endgdp
	save `vpi'
restore

merge m:1 year using `vpi', nogen

replace gdp = gdp*defl


* SAVE DATA
***********

keep gdp year BULA KRS
drop if mi(KRS)
sort KRS year
order KRS BULA year gdp

compress
save "${DATA}\301_gdp.dta", replace
	
	
* CLOSE LOG
***********

cap log close
