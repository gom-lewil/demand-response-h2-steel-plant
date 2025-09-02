# How to obtain weather data

Weather data source is a combination of two sources as the primary source has some time frames with data holes. 

Primary: https://login.bsh.de/fachverfahren/index
Backup: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=download

As no license for distribution for the primary data was provided I explain how the data can be downloaded: 

1. Login into insitu plattform and select the "Insitu" tab
2. Select for FINO1 Platform: ATMP at height 92m, WSPD at height 102m and DRYT at height 101 for the respective time frame in which you are interested.
3. Select the download button "request data" and load the downloaded file into this folder with the name scheme of '{year}_FINO1_weather_data.csv' into the weather_source_data folder. 
4. Before you fill the data wholes with the script in 'weather_data_processing.py' ypu need to change the air pressure values to Pascal by multiplying with 100 and bring the data into the required format for windpowerlib as shown in the example data here: https://windpowerlib.readthedocs.io/en/stable/modelchain_example_notebook.html#Import-weather-data