********************************************************************************
* 309_predictgdp.do                                                            *
********************************************************************************

/* This file predicts GDP at the county and at the municipality level. */


* START LOG
***********

cap log close
log using "${LOG}\309_predictgdp_${c_date}.log", replace


* COUNTY-LEVEL STRAIGHT-FORWARD PREDICTION
******************************************

use "${DATA}\306_regsample_Counties.dta", clear

foreach span in fr lg {
	
	if "`span'"=="fr" {
		local ifyears if year>=max(${beggdp},${begdmsp},${begsg}) & year<=min(${endgdp},${enddmsp},${endsg})
		local cloudopt
		}
	else if "`span'"=="lg" {
		local ifyears
		local cloudopt c.pct_cloud
		}
		
	foreach predv in sg dmsp {
		
		if "`predv'"=="sg" local indepv c.ln_builtup_px c.ln_crops_px c.ln_grass_px c.ln_forest_px c.ln_noveg_px c.ln_water_px
		else if "`predv'"=="dmsp" local indepv c.ln_dmsp_int
	
		qui reg ln_gdp `indepv' `pct_cloud' i.BULA i.year `ifyears', vce(r)
		predict pr`predv'_`span'_ln_gdp
		gen pr`predv'_`span'_gdp = exp(pr`predv'_`span'_ln_gdp)
		
		}
	
	}

compress
save "${DATA}\309_predictgdp_Counties.dta", replace


* STANDARDIZED PREDICTION
*************************

* Option 1 (meth): Demeaning (dem) or standardizing (std)
local meths dem std
* Option 2 (smpl): over entire sample (all) or by FE variables federal state and year (byfe)
local smpls all byfe
* Option 3 (type): original absolute values (abs) or logged values (ln)
local types abs ln
* Option 4 (span): restricted time span (fr) or longest possible time span incl. cloud cover (lg)
local spans fr lg
* Option 5 (infe): include federal state and year FE in prediction regression (wfe) or not (nofe)
local infes wfe nofe

*** CHOSEN SPECIFICATION IN SUPPLEMENTARY MATERIAL S2.4 (within-region predictive power) CORRESPONDS TO: std all ln fr wfe (see predictions in 310_withinregion.do)


// STANDARDIZE VARIABLES

local surface_px builtup_px crops_px forest_px grass_px noveg_px water_px

foreach reg in Counties Municipalities {
	
	tempfile tmp_`reg'
	
	use "${DATA}\306_regsample_`reg'.dta", clear

	foreach meth in `meths' {
	
		if "`meth'"=="dem" local c_opt
		else if "`meth'"=="std" local c_opt standardize
	
		foreach smpl in `smpls' {
		
			if "`smpl'"=="byfe" local byopt by BULA year, sort:
			else if "`smpl'"=="all" local byopt
	
			foreach x in `surface_px' pct_cloud dmsp_int gdp {
				
				if "`reg'"=="Municipalities" & "`x'"=="gdp" continue
		
				foreach type in `types' {
				
					if "`x'"=="pct_cloud" & "`type'"=="ln" continue
					else if "`type'"=="ln" local xv `type'_`x'
					else local xv `x'
				
					if "`x'"=="pct_cloud" & "`type'"=="abs" local typename
					else local typename _`type'
				
					`byopt' center `xv', generate(`meth'_`smpl'`typename'_`x') `c_opt'
				
					if "`smpl'"=="byfe" & "`meth'"=="std" {
						replace std_byfe`typename'_`x' = 0 if mi(std_byfe`typename'_`x') & !mi(std_all`typename'_`x') // if no variation within FE sample (e.g., no cloud cover within year and federal state)
						}
				
					}
			
				}
	
			}
	
		}
		
	save `tmp_`reg''
	
	}
	
	
// TRANSFER TO MUNICIPALITY LEVEL

use `tmp_Counties', clear
append using `tmp_Municipalities'
		
foreach meth in `meths' {
		
	foreach type in `types' {
			
		foreach smpl in `smpls' {
				
			foreach predv in sg dmsp {
					
				foreach infe in `infes' {
		
					if "`infe'"=="wfe" local feopt i.BULA i.year
					else if "`infe'"=="nofe" local feopt
						
					foreach span in `spans' {
	
						if "`span'"=="fr" local ifyears if year>=max(${beggdp},${begdmsp},${begsg}) & year<=min(${endgdp},${enddmsp},${endsg})
						else local ifyears
							
						if "`span'"=="lg" & "`predv'"=="sg" local cloudopt c.pct_cloud
						else local cloudopt
					
						if "`predv'"=="sg" {
							local indepv
							foreach x in `surface_px' {
								local indepv `indepv' c.`meth'_`smpl'_`type'_`x'
								}
							}
						else if "`predv'"=="dmsp" local indepv c.ln_dmsp_int
						
						qui reg `meth'_`smpl'_`type'_gdp `indepv' `cloudopt' `feopt' `ifyears', vce(r)
						local predvar pr`predv'_`span'_`meth'_`smpl'_`infe'_`type'_gdp
						gen `predvar' = 0
						foreach c in `indepv' `cloudopt' {
							local v = subinstr("`c'","c.","",1)
							local coef = _b[`v']
							replace `predvar' = `predvar'+(`coef'*`v') // so that FE not included if used in prediction regression
							replace `predvar' = . if mi(`v') // prediction for observation not possible because of missing input variable
							}
						
						}
				
					}
			
				}
		
			}
	
		}
	
	}
	
	
// SAVE COUNTY-LEVEL PREDICTION

preserve
	keep if mi(AGS)
	merge 1:1 KRS year using "${DATA}\309_predictgdp_Counties.dta"
	assert _merge==3
	drop _merge
	drop debkg_id AGS dem_* std_*
	compress
	save "${DATA}\309_predictgdp_Counties.dta", replace
restore

// SAVE MUNICIPALITY-LEVEL PREDICTION

keep if mi(KRS)
drop KRS gdp ln_gdp dem_* std_*
order AGS debkg_id, b(BULA)

compress
save "${DATA}\309_predictgdp_Municipalities.dta", replace


* CLOSE LOG
***********

cap log close
