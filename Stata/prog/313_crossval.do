********************************************************************************
* 313_crossval.do                                                              *
********************************************************************************

/* This file calculates the five-fold cross-validation indicators. */


* START LOG
***********

cap log close
log using "${LOG}\313_crossval_${c_date}.log", replace


* IMPORT DATA
*************

/* class values:
0 builtup
1 grass
2 crops
3 forest
4 noveg
5 water

e.g., c23 indicates pixels that are crops in CLC, but classified as forest
*/

clear
set obs 25
gen year = 2018
replace year = 2012 if _n<=20
replace year = 2006 if _n<=15
replace year = 2000 if _n<=10
replace year = 1990 if _n<=5
by year, sort: gen subset = _n

gen kappa = .
forval i = 0(1)5 {
	forval j = 0(1)5 {
		gen c`j'`i' = .
		la var c`j'`i' "CLC class `j', classified as `i'"
		}
	}

foreach y of numlist 1990 2000 2006 2012 2018 {

	forval k = 1(1)5 {
	
		preserve
	
			import delim using "${ORIG_CROSSVAL}\\crossVal`y'-subset`k'.csv", clear 
			
			local kappa = kappa
		
			local matrix = subinstr(matrix,"[","",.)
			local matrix = subinstr("`matrix'","]","",.)
			local matrix = subinstr("`matrix'",",","",.)
		
		restore
		
		replace kappa = `kappa' if year==`y' & subset==`k'
		
		tokenize `matrix'
		
		local it = 0
		forval i = 0(1)5 {
			forval j = 0(1)5 {
				local it = `it'+1
				replace c`j'`i' = ``it'' if year==`y' & subset==`k'
				}
			}
	
		}

	}

	
* CALCULATE ACCURACIES AND OTHER INDICATORS
*******************************************

egen pixsum = rowtotal(c*)
la var pixsum "total number of pixels"

forval c = 0(1)5 {
	local otherc = subinstr("0 1 2 3 4 5","`c'","",.)
	gen true_`c' = c`c'`c'
	la var true_`c' "truly classified wrt class `c'"
	foreach i of numlist `otherc' {
		foreach j of numlist `otherc' {
			replace true_`c' = true_`c'+c`j'`i'
			}
		}
	gen oa_`c' = true_`c'/pixsum
	la var oa_`c' "overall accuracy wrt class `c'"
	tempvar allclc
	egen `allclc' = rowtotal(c`c'*)
	gen tpr_`c' = c`c'`c'/`allclc'
	la var tpr_`c' "true-positive rate wrt class `c'"
	gen tnr_`c' = (true_`c'-c`c'`c')/(pixsum-`allclc')
	la var tnr_`c' "true-negative rate wrt class `c'"
	gen ba_`c' = (tnr_`c'+tpr_`c')/2
	la var ba_`c' "balanced accuracy wrt class `c'"
	tempvar allclass
	egen `allclass' = rowtotal(c*`c')
	gen ua_`c' = c`c'`c'/`allclass'
	la var ua_`c' "users' accuracy wrt class `c'"
	}

foreach x of varlist oa_* tpr_* tnr_* ba_* ua_* {
	by year, sort: egen `x'_y = mean(`x')
	egen `x'_tot = mean(`x')
	}
	
	
* VALUES IN MANUSCRTIP TABLE 1
******************************

tokenize builtup grass crops forest noveg water
forval j = 1(1)6 {
    local sg = `j'-1
	foreach x in true oa tpr tnr ba ua {
	    ren `x'_`sg' `x'_``j''
		if "`x'"!="true" {
			ren `x'_`sg'_* `x'_``j''_*
			qui sum `x'_``j''_tot
			di "`x' ``j'': " %4.3fc `r(mean)'
			}
		}
	di ""
	}
	
	
* VALUES IN SI APPENDIX TABLES S2-S7
************************************

qui levelsof year, local(yearlev)
forval j = 1(1)6 {
	local sg = `j'-1
	foreach x in oa tpr tnr ba ua {
		foreach y of numlist `yearlev' {
			qui sum `x'_``j''_y if year==`y'
		    di "`x' ``j'' `y': " %4.3fc `r(mean)'
			}
		qui sum `x'_``j''_tot
		di "`x' ``j'' average: " %4.3fc `r(mean)'
		di ""
		}
	di ""
	}

	
* SAVE DATA
***********

compress
save "${DATA}\313_crossval.dta", replace


* CLOSE LOG
***********

cap log close
