********************************************************************************
* 312_heiapplication.do                                                        *
********************************************************************************

/* This file contains the social-science application of surface groups to the
establishment of higher education institutions. */


* START LOG
***********

cap log close
log using "${LOG}\312_heiapplication_${c_date}.log", replace

local surface_px builtup_px grass_px forest_px crops_px noveg_px water_px
local ln_surface_px ln_builtup_px ln_grass_px ln_forest_px ln_crops_px ln_noveg_px ln_water_px


* PREPARE DATA
**************

use "${ORIG_HEI}", clear
	
merge 1:1 AGS year using "${DATA}\306_regsample_Municipalities.dta"
drop if _merge==2
drop if year<${begsg}
drop if year>2015  // to account for 3-year patent citation lag
drop if BULA==11  // Berlin
drop *dmsp* *viirs* _merge BULA

by AGS, sort: egen mean_total_px = mean(total_px)
foreach x of varlist cloud_px total_px {
	replace `x' = mean_total_px if mi(total_px)
	}
drop mean_total_px
replace pct_cloud = 1 if mi(pct_cloud) & total_px==cloud_px
foreach x in `surface_px' {
	replace `x' = 0 if !mi(total_px) & mi(`x')  // municipality-year observations completely covered by clouds and thus not in regsample data but in ORIG_HEI
	replace ln_`x' = 0 if !mi(total_px) & mi(ln_`x')
	}
drop if mi(total_px)  // one municipality not included in satellite data

gen east = AGS>=12000000  


* EXPORT DATA FOR GRAPH
***********************

preserve

	foreach x of varlist pquan pqual {
		by year east, sort: egen mean_`x' = mean(`x')
		}
	keep east year mean_*
	duplicates drop
	reshape wide mean_*, i(year) j(east)
	foreach x in pquan pqual {
		gen diff_`x' = mean_`x'0 - mean_`x'1
		drop if mi(diff_`x')
		}
	drop mean_*
	
	* These are the data underlying Fig. S10
		
restore 


* UNDETECTED CLOUD COVER ADJUSTMENT
***********************************

by AGS, sort: egen median_builtup_px = median(builtup_px)
drop if (builtup_px>2*median_builtup_px | pct_cloud>0.1) & year<=1990 & east==1
drop if (builtup_px>2*median_builtup_px | pct_cloud>0.1) & year<=1990 & east==0
	
	
* DEVELOPMENT BEFORE REUNIFICATION
**********************************

foreach x of varlist `ln_surface_px' pct_cloud {
	sort AGS year
	gen D_`x' = `x'-`x'[_n-1] if AGS==AGS[_n-1] & year>=${begsg} & year<=1990
	by AGS, sort: egen mD_`x' = mean(D_`x')
	}

	
* SHAPE TO 3-YEAR INTERVALS
***************************

gen year3 = .
forval y = 1993(3)2014 {
	replace year3 = `y' if year<=`y' & year>`y'-3
	}

by AGS year3, sort: egen mean_pquan = mean(pquan) if !mi(year3)
replace mean_pquan = 0 if mi(mean_pquan) & !mi(year3)
by AGS year3, sort: egen mean_pqual = mean(pqual) if !mi(year3)
replace mean_pqual = 0 if mi(mean_pqual) & !mi(year3)
replace pqual = 0 if pquan==0
by AGS year3, sort: egen uas3 = total(uas) if !mi(year3)
replace uas3 = uas3==3 if !mi(uas3)
	
keep AGS year3 uas3 mD* east mean_pquan mean_pqual
drop if mi(year3)
duplicates drop

reshape wide mean_pquan mean_pqual uas3, i(AGS) j(year3)


* PROPENSITY-SCORE MATCHING RESULTS
***********************************

forval y = 1996(3)2014 {
	
	*logit east mD* if uas3`y'==1  // first stage
	
	foreach x in /*total_pquan*/ mean_pquan mean_pqual {
	    
		di ""
		di as res "Year: `y', dep. var.: `x'"
		di ""
		
		gen D_`x'`y' = `x'`y'-`x'1993
		psmatch2 east mD* if uas3`y'==1, outcome(D_`x'`y') ate logit	// Table S27
		pstest mD*, both
		
		drop _*
		
		}
	
	}


* CLOSE LOG
***********

cap log close
