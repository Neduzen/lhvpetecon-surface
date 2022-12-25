********************************************************************************
* 302_prephhi.do                                                               *
********************************************************************************

/* This file prepares the RWI-GEO-GRID data. */


* START LOG
***********

cap log close
log using "${LOG}\302_prephhi_${c_date}.log", replace


* IMPORT DATA
*************

use r1_id r1_kkr_w_summe year using "${ORIG_RWI}", clear


* ADJUST MISSINGS
*****************

replace r1_kkr_w_summe = . if r1_kkr_w_summe<=0
drop if mi(r1_kkr_w_summe)


* RENAME VARIABLES
******************

ren r1_id cell_id
ren r1_kkr_w_summe hhi


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

merge m:1 year using `vpi'
assert _merge!=1
keep if _merge==3
drop _merge

replace hhi = hhi*defl
drop defl


* SAVE DATA
***********

order year, a(cell_id)
sort cell_id year
compress
save "${DATA}\302_hhi.dta", replace


* CLOSE LOG
***********

cap log close
