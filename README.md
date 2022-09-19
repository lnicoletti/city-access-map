# CITYACCESSMAP 

Hello, this is where the analysis behind [CITYACCESSMAP](www.cityaccessmap.com) lives. CITYACCESSMAP is a web application for global scale urban accessibility insights. Please explore the app [here](cityaccessmap.com) for more information. 

To download the processed data for any city that the application covers, please go [here](https://github.com/lnicoletti/access-world/tree/master/public/data). To reproduce the data collection and analysis behind this data please go [here](https://github.com/lnicoletti/access-world/tree/master/public/dataPreparation). Global-scale raw amenities data is collected from OpenStreetMap using [OsmPoisPbf](https://github.com/MorbZ/OsmPoisPbf/) and the ```uac_filter.txt``` query. Accessibility calculation are computed using the ```1_calculateAccess.py``` script. Population grids for functional urban areas are extracted from the [Global Human Settlement Layer](https://ghsl.jrc.ec.europa.eu/ghs_pop2022.php) and pre-processed using the ```2_extractUA_QGIS.py``` script, to be run in [QGIS](https://www.qgis.org/hu/site/). Accessibility per grid cell (the data used for the visuals in the app) for urban areas globally is computed using the ```3_calculatedGridAccess.py``` script.

The scientific research behind this project is published [here](https://arxiv.org/abs/2203.13784).

If you would like to contribute to this project, or if you have any questions about it, please contact [Leonardo Nicoletti](https://www.leonardonicoletti.com/).

