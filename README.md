# Optimisation of Demand Response Green Steel Production
## Introduction
In order to analyse Demand Response potential of load shifting and capacity utilisation in future steel production practice, this model formulates an optimisation framework for dispatching energy in batch production processes. Different hydrogen based direct reduced iron (H2-DRI) plants and their flexibility potentials can be modeled. This includes the scheduling and flexibility behaviour of water electrolysis, steel making and finishing production facilities, with a focus on electric loads and required material quanties.

## How To use
### Installation and Environment creation
- Create a new environment with conda from the given 'environment.yml' file via `conda env create --file environment.yml -n flex_batch_prod`

- now you can open the example notbooks by starting `jupyter notebook`

### Examples
The file 'run_a_model.ipynb' shows how a model is instatiated and solved. This can be used to develop own models by changing input data in the '0_input_data' folder, or having a deeper look into the model structure in the 'flexible_batch_production/construct.py' file of the model as this is where the model is created. 

The file 'visualise_results.ipynb' shows the results of the optimisation with annual time range. Additionally analysis methods are shown.

### Documentation
In the Documentation file you can find an overview of all required inputs parameter and their names in the model. In the future variables are also added to the documentation.   

# Licenses
## Software:

Copyright 2025 [DLR e.V./Leonard Willen]

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


## Used Input Data

### Electricity Price Data (not included in repository, no license available)
-	German Electricity Prices 2012 - 2024
-	Katharina Hartz, Fabian Hein, Hauke Hermann (Öko-Institut), Mara Marthe Kleiner, Thorsten Lenck, Philipp Litz, Dr. Alice Sakhel, Fahimeh Beigi, Charlotte Bodenmüller, Jia Loy, Saeed Sayadi, Yu-Chi Chang, Paulina Lange, Hai Long Nguyen
-	Current, historical and modelled local and future representations of the situation in the electricity system with generation, consumption and prices.
-	2025
-	[Link to Data](https://www.agora-energiewende.de/daten-tools/agorameter)

### Weather Data
#### FINO1 Plattform Data (not included in repository, no license available)
-	FINO1 Offshore Weather Data 2012 - 2024
-	Wind speed, temperature and air pressure data from FINO1 offshore platform in the years 2012 - 2024
-   2025
-	[Link to Data](https://login.bsh.de/fachverfahren/)


#### Weather Validation Data - ERA5
-	ERA5 Weather Data
-	Licence 
    -	Licence for Copernicus Products
    -	[Link to Licence](0_input_data/weather/weather_source_data/LICENSE)
    -	Attribution Statement: Generated using Copernicus Climate Change Service information 2012 till 2024
-   ERA5 provides hourly estimates for a large number of atmospheric, ocean-wave and land-surface quantities.   
-   2018
-	[Link to Data](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview)

### Plant Input Data (not included in repository, no license available)
-   Green Steel Plant Scenario Data 
-   Marc Hölling, Hans Schäfers, Sebastian Gellert, Martin Grasenack, Lucas Jürgens, Nicholas Tedjosantoso, Samuel Schüttler
-   Data from report "Windstahl aus Norddeutschland"  
-   2021
-	[Link to Data](http://dx.doi.org/10.13140/RG.2.2.12721.10084)