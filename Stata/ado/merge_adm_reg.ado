/* Some administrative regions (counties, municipalities) comprise more than one
polygon. The polygons are uniquely identified by DEBKG_ID in the original
shapefiles, but a few administrative regions comprise more than one polygon.
Those regions are situated in the coastal regions and have separate polygons for 
land and water areas. For these administrative regions, we consider only the 
land areas. The file ${ORIG_ADMREG} contains information only on the main
polygon of a region. Therefore, matching this file to the data allows us to (a)
match the administrative identifier and (b) drop polygons that comprise only
water areas. */

cap program drop merge_adm_reg
program def merge_adm_reg

	version 16.1
	
	syntax varname, regionlevel(string) [nodrop]
	
qui {
    
	if "`regionlevel'"!="Counties" & "`regionlevel'"!="Municipalities" {
		di as error `"Option regionlevel has to be either "Counties" or "Municipalities""'
		error
		}
    
	preserve
		tempfile tmp
		import excel using "${ORIG_ADMREG}", sh("VG250") first clear
		if "`regionlevel'"=="Counties" {
			keep if strlen(RS)==5
			}
		else if "`regionlevel'"=="Municipalities" {
			keep if strlen(AGS)==8
			drop if AGS=="00000000" | AGS=="--------"
			}
		destring AGS, replace force
		ren DEBKG_ID `varlist'
		keep `varlist' AGS
		save `tmp'
	restore
		
	merge m:1 `varlist' using `tmp'
	if "`regionlevel'"=="Counties" {
		assert _merge!=2
		}
	/* This assertion is not done for municipalities, because some of them are
	too small to have a match in the satellite data. For surface groups, the 
	municipality of Helgoland (a very small island outside GEE's internal 
	polygon indicating the German borders) does not have any data. For DMSP OLS 
	night light intensity, six municipalities do not have any data. These six 
	municipalities are too small for ArcGIS to assign a DMSP OLS pixel to them. 
	For VIIRS night light intensity, the municipality of Insel Lütje Horn (a 
	very small island in the North Sea) does not have any data. */
	
	if "`drop'"=="" keep if _merge==3
	drop _merge
	order AGS, a(`varlist')
    
	}
	
end
