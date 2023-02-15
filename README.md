<div id="top"></div>

<!-- PROJECT SHIELDS -->

<!-- PROJECT LOGO -->
<br />
<div align="center">

<h3 align="center">Proxying Economic Activity with Daytime Satellite Imagery: Filling Data Gaps Across Time and Space</h3>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#Setup">Setup</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

Satellite image analysis is done with the Google Earth Engine Python API.<br />
Data aggregation is conducted with ArcGIS Python scripts.<br />
Data analysis is performed with Stata scripts.<br />


<!-- GETTING STARTED -->
### Prerequisites
To reproduce the data processing the following things are necessary:
* Create a Google Earth Engine Account
* MongoDB installation
* Python Installation
* Stata Installation
* ArcGIS Installation


<!-- USAGE EXAMPLES -->
## Setup
After installing python and setting up a GEE account, the computer where python is running needs the authorization of using GEE with the created account.
Further python authorization for a Google Drive accounts needs to be made.
Also MongoDB needs to be installed and setup with three databases: 
      'landcover', host='localhost', port=27017 for EU data
      'landcover-USA', host='localhost', port=27017 for US data
      'landcover-World', host='localhost', port=27017 for world data
After preparing all the setup and installing all needed python packages, the Satellite 


<!-- USAGE -->
## Usage

Satellite image analysis: 
Python programm with 3 different main.py programms.
- One classifies European countries (country wise export). Trainingsdata produced from its own country.
- One classifies US (State wise export). Trainingsdata produced based on EU countries with similar climate conditions.
- One classifies all other countries (country wise export). Trainingsdata produced based on EU countries with similar climate conditions.

Setup countries to execute:
Run the function 'addNewCountry()' in the specific main.py (EU, USA, World) with a country name and priority.<br />
Example:<br />
  addNewCountry("Chad", 0)<br />
The python program will create a GEE asset folder and create a MongoDB entry for the country containing all needed information for the automatic execution.<br />
Whenever the country name is equals to the the countrys' feature in GEE featurecollection ('USDOS/LSIB_SIMPLE/2017'), no additional input needs to be done.<br />
For countries with special names, the correct name has to be assigned to the MongoDB entry of shapefile="..." matching the country feature value in the property 'country_na' of the GEE featurecollection ('USDOS/LSIB_SIMPLE/2017').<br />

Execution of main.py:
main.py will load all Country or States saved in the MongoDB.<br />
The specific executer.py is launch which goes through all country/states objects and identfies the next one to run (lowest priority number and not yet fully executed).<br />
Each country will be launched with the following sequence:
- See whether all tasks on GEE are finished, if no sleep for 20 minutes and repeat
- Create trainingsdata
- Create (lat/long) grid cells
- Classify and export all grid cells (takes up to weeks for large countries)
- Validation (for EU countries)
- Mark country as finished


<!-- LICENSE -->
## License



<!-- CONTACT -->
## Contact

Patrick Lehnert - patrick.lehnert@business.uzh.ch

Michael Niederberger - michael.niederberger@uzh.ch

Project Link: [https://github.com/Neduzen/lhvpetecon-surface](https://github.com/Neduzen/lhvpetecon-surface)

<p align="right">(<a href="#top">back to top</a>)</p>


