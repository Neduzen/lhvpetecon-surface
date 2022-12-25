********************************************************************************
* 311_africa.do                                                                *
********************************************************************************

/* This files prepares the data and produces the analyses for the comparison to
Yeh et al.'s (2020) asset-wealth index for African countries. */


* START LOG
***********

cap log close
log using "${LOG}\311_africa_${c_date}.log", replace


* PREPARE SURFACE GROUPS DATA
*****************************

// import and merge data

local surface_px builtup_px crops_px forest_px grass_px noveg_px water_px

foreach r in DHSCluster GADM2 {
    
	local clist Guinea Togo Uganda Zimbabwe
	local strclist = `""'
    
	foreach c in `clist' {
		
		local strclist = `"`strclist', "`c'""'
	    
		tempfile `c'
	
		clear
	
		local start = ${begsg}
		local end = ${endsg}
		
		forval y = `start'(1)`end' {
		
			preserve
				tempfile tmp
				local files : dir "${GIS_AFRICA}\\`c'\csv\\`c'_`r'" files "*`y'.csv"
				tokenize `files'
				if "`1'"=="" {
				    restore
					continue
					}
				else {
					import delim using "${GIS_AFRICA}\\`c'\csv\\`c'_`r'\\`1'", clear
					drop *_area
					save `tmp'
					}
			restore
		
			append using `tmp'
		
			}
		
		qui ds
		tokenize `r(varlist)'
		
// generate variables

		gen total_px = builtup_px+grass_px+forest_px+crops_px+noveg_px+water_px+cloud_px
		gen pct_cloud = cloud_px/total_px
		foreach x of varlist `surface_px' {
			gen ln_`x' = ln(`x'+1)
			order ln_`x', a(`x')
			}
		
// append countries and save data

		order `1' year
		gen country = "`c'"
		
		save ``c''
		
		}
		
	clear
	foreach c in `clist' {
	    append using ``c''
		}
		
	sort `1' year
	compress
	save "${DATA}\311_surface_`r'.dta", replace
	
	
* PREPARE YEH ET AL. (2020) DATA
********************************
	
	import delim using "${ORIG_YEH_`r'}", varn(1) clear
	gen year = substr(svyid,3,.)
	destring year, replace force
	ren geolev gid_2
	
	replace country = "Cote d Ivoire" if substr(svyid,1,2)=="CI"
	replace country = subinstr(trim(country)," ","",.)
	
	if "`r'"=="DHSCluster" {
		gen orig_fid = _n  // Works for merging later, because sorting has never been changed. Merging on lat/lon does not work due to rounding errors.
		}
		
	keep if inlist(country `strclist')
	
	compress
	save "${DATA}\311_yehetal_`r'.dta", replace
	
	}
	
	
* COMPARISON OF SURFACE GROUPS AND YEH ET AL. (2020) 
****************************************************

local ln_surface_px c.ln_builtup_px c.ln_grass_px c.ln_crops_px c.ln_forest_px c.ln_noveg_px c.ln_water_px
local clist Guinea Togo Uganda Zimbabwe

// DHS cluster level

* merge data

use "${DATA}\311_surface_DHSCluster.dta", clear
merge 1:1 orig_fid year using "${DATA}\311_yehetal_DHSCluster.dta", keepus(survey index gid_2)
assert _merge!=2
drop _merge

* run prediction from surface groups

gen pred_sg = .
foreach c in `clist' {
	di as res "`c'"
	reg survey `ln_surface_px' c.pct_cloud i.year if country=="`c'", vce(r)	// Table S18
	qui levelsof year if e(sample), local(Ny)
	if wordcount("`Ny'")>1 testparm i.year
	predict prediction if e(sample)
	replace pred_sg = prediction if mi(pred_sg)
	drop prediction
	}

* calculate indicators corresponding to Yeh et al.'s (2020) Figs. 2a and 2c

qui corr survey index
di "Yeh et al. (2020) r2 over all observations (corresponds to Yeh et al.'s, 2020, fig. 2a red indicator): " `r(rho)'^2

qui corr survey pred_sg
di "Surface groups r2 over all observations (corresponds to Yeh et al.'s, 2020, fig. 2a red indicator): " `r(rho)'^2

local r2_yeh = 0
local r2_sg = 0
local n = 0
foreach c in `clist' {
    
    qui corr survey index if country=="`c'"
	local r2_yeh = `r2_yeh'+(`r(rho)'^2)
	di "Yeh et al. (2020) r2 for `c' (corresponds to Yeh et al.'s, 2020, fig. 2c country r2): " `r(rho)'^2
	
	qui corr survey pred_sg if country=="`c'"
	local r2_sg = `r2_sg'+(`r(rho)'^2)
	di "Surface groups r2 for `c' (corresponds to Yeh et al.'s, 2020, fig. 2c country r2): " `r(rho)'^2
	
	local n = `n'+1
	
	}

di "Yeh et al. (2020) r2 country average (corresponds to Yeh et al.'s, 2020, fig. 2a black indicator): " `r2_yeh'/`n'
di "Surface groups r2 country average (corresponds to Yeh et al.'s, 2020, fig. 2a black indicator): " `r2_sg'/`n'

// GADM2 (district) level

* merge data

use "${DATA}\311_surface_GADM2.dta", clear
merge 1:1 gid_2 year using "${DATA}\311_yehetal_GADM2.dta"
assert _merge!=2
drop _merge

* run prediction from surface groups

gen pred_sg = .
foreach c in `clist' {
	di as res "`c'"
	reg dhs `ln_surface_px' c.pct_cloud i.year if country=="`c'", vce(r)	// Table S19
	qui levelsof year if e(sample), local(Ny)
	if wordcount("`Ny'")>1 testparm i.year
	predict prediction if e(sample)
	replace pred_sg = prediction if mi(pred_sg)
	drop prediction
	}
	
* calculate indicators corresponding to Yeh et al.'s (2020) Figs. 2b and 2d

qui corr dhs predictions
di "Yeh et al. (2020) unweighted r2 over all observations (corresponds to Yeh et al.'s, 2020, fig. 2b red indicator unweighted): " `r(rho)'^2

qui corr dhs pred_sg
di "Surface groups unweighted r2 over all observations (corresponds to Yeh et al.'s, 2020, fig. 2b red indicator unweighted): " `r(rho)'^2

qui corr dhs predictions [fw=nx]
di "Yeh et al. (2020) weighted r2 over all observations (corresponds to Yeh et al.'s, 2020, fig. 2b red indicator weighted): " `r(rho)'^2

qui corr dhs pred_sg [fw=nx]
di "Surface groups weighted r2 over all observations (corresponds to Yeh et al.'s, 2020, fig. 2b red indicator weighted): " `r(rho)'^2

local r2_yeh_nw = 0
local r2_yeh_fw = 0
local r2_sg_nw = 0
local r2_sg_fw = 0
local n = 0
foreach c in `clist' {
    
    qui corr dhs predictions if country=="`c'"
	local r2_yeh_nw = `r2_yeh_nw'+(`r(rho)'^2)
	di "Yeh et al. (2020) unweighted r2 for `c' (corresponds to Yeh et al.'s, 2020, fig. 2d unweighted country r2): " `r(rho)'^2
	
	qui corr dhs pred_sg if country=="`c'"
	local r2_sg_nw = `r2_sg_nw'+(`r(rho)'^2)
	di "Surface groups unweighted r2 for `c' (corresponds to Yeh et al.'s, 2020, fig. 2c unweighted country r2): " `r(rho)'^2
	
	qui corr dhs predictions if country=="`c'" [fw=nx]
	local r2_yeh_fw = `r2_yeh_fw'+(`r(rho)'^2)
	di "Yeh et al. (2020) weighted r2 for `c': " `r(rho)'^2
	
	qui corr dhs pred_sg if country=="`c'" [fw=nx]
	local r2_sg_fw = `r2_sg_fw'+(`r(rho)'^2)
	di "Surface groups weighted r2 for `c': " `r(rho)'^2
	
	local n = `n'+1
	
	}
	
di "Yeh et al. (2020) unweighted r2 country average (corresponds to Yeh et al.'s, 2020, fig. 2b black indicator unweighted): " `r2_yeh_nw'/`n'
di "Surface groups unweighted r2 country average (corresponds to Yeh et al.'s, 2020, fig. 2b black indicator unweighted): " `r2_sg_nw'/`n'
di "Yeh et al. (2020) weighted r2 country average (corresponds to Yeh et al.'s, 2020, fig. 2b black indicator weighted): " `r2_yeh_fw'/`n'
di "Surface groups weighted r2 country average (corresponds to Yeh et al.'s, 2020, fig. 2b black indicator weighted): " `r2_sg_fw'/`n'


* CLOSE LOG
***********

cap log close
