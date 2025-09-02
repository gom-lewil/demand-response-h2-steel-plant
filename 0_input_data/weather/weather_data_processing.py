import marimo

__generated_with = "0.11.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import flexible_batch_production as fbp
    import numpy as np
    import matplotlib.pyplot as plt
    import math
    import pandas as pd
    import xarray as xr
    return fbp, math, mo, np, pd, plt, xr


@app.cell(hide_code=True)
def _(mo):
    mo.md("""# Calculating weather years - fast""")
    return


@app.cell(hide_code=True)
def _(mo, np):
    switch = mo.ui.switch(label="Re-Run weather data calculation")

    # weather_data.info() # in case of adding new years good to inspect data and count of nans
    specify_data_to_use = {
        2012: {
            'tcol_variable_name': '#Time',
            'col_wind_speed': ' WSPD_CUP_MC.Cup Anemometer.102.0 [m/s]',
            'col_temperature': ' DRYT.Thermometer.101.0 [degC]',
            'col_pressure': ' ATMP.Barometer.21.0 [hPa]',
            'first_row': ['height', 102, 101, 21, 0],
        },
        2013: {
            'tcol_variable_name': '#Time',
            'col_wind_speed': ' WSPD_CUP_MC.Cup Anemometer.102.0 [m/s]',
            'col_temperature': ' DRYT.Thermometer.101.0 [degC]',
            'col_pressure': ' ATMP.Barometer.21.0 [hPa]',
            'first_row': ['height', 102, 101, 21, 0],
        },
        2014: {
            'tcol_variable_name': '#Time',
            'col_wind_speed': ' WSPD_CUP_MC.Cup Anemometer.102.0 [m/s]',
            'col_temperature': ' DRYT.Thermometer.42.0 [degC]',
            'col_pressure': ' ATMP.Barometer.21.0 [hPa]',
            'first_row': ['height', 102, 42, 21, 0],
        },
        2015: {
                'tcol_variable_name': '#Time',
                'col_wind_speed': ' WSPD_CUP_MC.Cup Anemometer.102.0 [m/s]',
                'col_temperature': ' DRYT.Thermometer.42.0 [degC]',
                'col_pressure': ' ATMP.Barometer.92.0 [hPa]',
                'first_row': ['height', 102, 42, 92, 0],
        },
        2016: {
                'tcol_variable_name': '#Time',
                'col_wind_speed': ' WSPD_CUP_MC.Cup Anemometer.102.0 [m/s]',
                'col_temperature': ' DRYT.Thermometer.52.0 [degC]',
                'col_pressure': ' ATMP.Barometer.92.0 [hPa]',
                'first_row': ['height', 102, 52, 92, 0],
        },
        2017: {
                'tcol_variable_name': '#Time',
                'col_wind_speed': ' WSPD_CUP_MC.Cup Anemometer.102.0 [m/s]',
                'col_temperature': ' DRYT.Thermometer.101.0 [degC]',
                'col_pressure': ' ATMP.Barometer.92.0 [hPa]',
                'first_row': ['height', 102, 101, 92, 0],
        },
        2018: {
                'tcol_variable_name': '#Time',
                'col_wind_speed': ' WSPD_CUP.Cup Anemometer.102.0 [m/s]',
                'col_temperature': ' DRYT.Thermometer.52.0 [degC]',
                'col_pressure': ' ATMP.Barometer.92.0 [hPa]',
                'first_row': ['height', 102, 52, 92, 0],
        },
        2019: {
            'tcol_variable_name': '#Time',
            'col_wind_speed': ' WSPD_CUP.Cup Anemometer.102.0 [m/s]',
            'col_temperature': ' DRYT.Thermometer.101.0 [degC]',
            'col_pressure': ' ATMP.Barometer.92.0 [hPa]',
            'first_row': ['height', 102, 101, 92, 0],
        },
        2020: {
            'tcol_variable_name': '#Time',
            'col_wind_speed': ' WSPD_CUP_MC.Cup Anemometer.102.0 [m/s]',
            'col_temperature': ' DRYT.Thermometer.101.0 [degC]',
            'col_pressure': ' ATMP.Barometer.92.0 [hPa]',
            'first_row': ['height', 102, 101, 92, 0],
        },
        2021: {
            'tcol_variable_name': '#Time',
            'col_wind_speed': ' WSPD_CUP_MC.Cup Anemometer.102.0 [m/s]',
            'col_temperature': ' DRYT.Thermometer.101.0 [degC]',
            'col_pressure': ' ATMP.Barometer.92.0 [hPa]',
            'first_row': ['height', 102, 101, 92, 0],
        },
        2022: {
            'tcol_variable_name': '#Time',
            'col_wind_speed': ' WSPD_CUP_MC.Cup Anemometer.102.0 [m/s]',
            'col_temperature': ' DRYT.Thermometer.101.0 [degC]',
            'col_pressure': ' ATMP.Barometer.21.0 [hPa]',
            'first_row': ['height', 102, 101, 21, 0],
        },
        2023: {
            'tcol_variable_name': '#Time',
            'col_wind_speed': ' WSPD_CUP_MC.Cup Anemometer.102.0 [m/s]',
            'col_temperature': ' DRYT.Thermometer.101.0 [degC]',
            'col_pressure': ' ATMP.Barometer.92.0 [hPa]',
            'first_row': ['height', 102, 101, 92, 0],
        },
        2024: {
            'tcol_variable_name': '#Time',
            'col_wind_speed': ' WSPD_CUP_MC.Cup Anemometer.102.0 [m/s]',
            'col_temperature': ' DRYT.Thermometer.101.0 [degC]',
            'col_pressure': ' ATMP.Barometer.92.0 [hPa]',
            'first_row': ['height', 102, 101, 92, 0],
        },
    }


    def replace_data_gaps(data, time_steps, required_step):
        larger_step_bool = [time_steps[i] > required_step for i in range(len(time_steps))]
        dummy_data = data.tolist()

        for i, step in enumerate(larger_step_bool):
            if step:
                # for each jumped step add nan value in list which needs to be flattened later
                dummy_data[i] = [np.nan for _ in range(time_steps[i]//required_step)] 
                # for each jumped step add time step value in list which needs to be flattened later
                # time_dummy[i] = [time_dummy[i-1]*required_step*(i_gap_length+1) for i_gap_length in range(time_steps[i]//np.timedelta64(10, 'm'))] 
        return(flatten(dummy_data))


    def replace_time_gaps(time_series, time_steps, required_step):
        larger_step_bool = [time_steps[i] > required_step for i in range(len(time_steps))]
        time_dummy = [np.datetime64(_, 'm') for _ in time_series]

        for i, step in enumerate(larger_step_bool):
            if step:
                time_dummy[i] = [
                    time_dummy[i-1] + required_step * (i_gap_length+1) # time stamp before * size of gap
                    for i_gap_length in range(time_steps[i]//np.timedelta64(10, 'm'))
                ] 
        return flatten(time_dummy)


    def flatten(a):
        """Recursive function to flatten list  """
        res = []  
        for x in a:  
            if isinstance(x, list):  
                res.extend(flatten(x))  # Recursively flatten nested lists  
            else:  
                res.append(x)  # Append individual elements  
        return res 


    def identify_nan_chunks(is_nan_list, replacement_threshold=6):
        """
        is_nan_list: A list of boolean values if at this index there is a nan value or not
        replacement_threshold: length of chunk to be replaced 

        Output:
            nan_chunks: A list of the length of the nan chunk at that index
        """
        # amount of steps for nan values to be replaced by ERA5 data
        nan_chunks = is_nan_list.astype(int)

        i_pointer = 0
        while i_pointer < len(is_nan_list):
            if is_nan_list[i_pointer]: # if there is a nan value
                i_nan_chunk_start = i_pointer # safe index as start of possible nan chunk
                i_nan_chunk_end = i_pointer # declare index pointer to search for end of nan chunk
                while is_nan_list[i_nan_chunk_end] != 0: # search for end of nan chunk
                    i_nan_chunk_end += 1
                nan_chunk_length = len(is_nan_list[i_nan_chunk_start:i_nan_chunk_end]) # 
                if nan_chunk_length >= replacement_threshold:
                    for i_nan_chunk in range(i_nan_chunk_start, i_nan_chunk_end+1):
                        nan_chunks[i_nan_chunk] = nan_chunk_length
                i_pointer = i_nan_chunk_end + 1
            else: # if there is not a nan value
                i_pointer += 1 # wind_speed value at that index available, continue looking for nan chunks
        return nan_chunks
    return (
        flatten,
        identify_nan_chunks,
        replace_data_gaps,
        replace_time_gaps,
        specify_data_to_use,
        switch,
    )


@app.cell
def _(mo, switch):
    mo.hstack([switch, mo.md(f"Has value: {switch.value}")])
    return


@app.cell
def _(
    identify_nan_chunks,
    math,
    np,
    pd,
    replace_data_gaps,
    replace_time_gaps,
    specify_data_to_use,
    switch,
    xr,
):
    if switch.value:
        nan_values_in_chunks={}
        
        for year in range(2012,2025):  
            weather_data = pd.read_csv(f'0_input_data/weather/weather_source_data/{year}_FINO1_weather_data.csv', sep=';')
            weather_data.replace(['nan', ' nan', '_', ' _'], np.nan, inplace=True)
            weather_data.loc[:, weather_data.columns != '#Time'] = weather_data.loc[:, weather_data.columns != '#Time'].map(lambda x: float(x))
        
            ds = xr.load_dataset("0_input_data/weather/weather_source_data/{year}weather_validation/data.grib", engine="cfgrib")
            ds_north_sea = ds.sel(latitude=54, longitude=6.25)
            era_wind_speed = [math.sqrt(u**2 + v**2) for u,v in zip(ds_north_sea['u100'].values, ds_north_sea['v100'].values)]
            era_wind_speed_10min = [ten_minutely for hourly in era_wind_speed for ten_minutely in [hourly]*6]
        
            data = {}
            required_time_step = np.timedelta64(10, 'm')
            time_series = weather_data['#Time'].map(lambda x: np.datetime64(x, 'm')).values
            time_steps = [np.timedelta64(time_series[i+1] - time_series[i], 'm') for i in range(len(time_series)-1)]
            time_steps.insert(0, np.timedelta64(0, 'm'))
        
        
            for key, value in specify_data_to_use[year].items():
                if key[:5] == 'tcol_':
                    data[key[5:]] = replace_time_gaps(time_series, time_steps, required_time_step)
                elif key[:4] == 'col_':
                    data[key[4:]] = replace_data_gaps(weather_data[value].values, time_steps, required_time_step)
        
            is_nan_list = np.isnan(data['wind_speed'])
            nan_chunks = identify_nan_chunks(is_nan_list)
        
            nan_values_in_chunks[year] = 0 
            for i, _ in enumerate(data['wind_speed']):
                if nan_chunks[i] > 6:
                    data['wind_speed'][i] = era_wind_speed_10min[i]
                    nan_values_in_chunks[year] += 1
            data['roughness_length'] = [0.15 for _ in range(len(data['variable_name']))]
            weather_df_for_model = pd.DataFrame.from_dict(data)
            weather_df_for_model['temperature'] = weather_df_for_model['temperature'].map(lambda x: x + 273.15) # Celsius to Kelvin
            weather_df_for_model['pressure'] = weather_df_for_model['pressure'].map(lambda x: x * 100) # hPa to Pa
            weather_df_for_model.loc[-1] = specify_data_to_use[year]['first_row'] # add heights at position 1
            weather_df_for_model.index = weather_df_for_model.index + 1  # shifting index
            weather_df_for_model.sort_index(inplace=True) 
            weather_df_for_model.to_csv(f'0_input_data/weather/{year}_FINO1_processed_weather_data.csv', index=False) # safe to csv file
    return (
        data,
        ds,
        ds_north_sea,
        era_wind_speed,
        era_wind_speed_10min,
        i,
        is_nan_list,
        key,
        nan_chunks,
        nan_values_in_chunks,
        required_time_step,
        time_series,
        time_steps,
        value,
        weather_data,
        weather_df_for_model,
        year,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""# Inspecting weather years""")
    return


@app.cell
def _(fbp):
    years = range(2012, 2025)

    wind_data = {
        year: fbp.generation_data.get_wind_farm_output(
            f"0_input_data/weather/{year}_FINO1_processed_weather_data.csv", 
            693, 
            True) 
        for year in years
    }
    return wind_data, years


@app.cell
def _(nan_values_in_chunks, plt, wind_data, years):
    capacity_factors = [sum(wind_data[year])/(max(wind_data[year])*len(wind_data[year])) for year in years]
    nan_values_percentage = [nan_values_in_chunks[year]/52560 for year in years]
    f = plt.figure()
    ax = plt.gca()
    p = ax.bar(years, capacity_factors, label='Capacity factor \nof measured data')
    ax.bar_label(p, label_type='center', color='white', fmt="{:.0%}")
    ax.set_ylabel('Capacity Factor')
    ax.set_xlabel('Year')

    share_nan_values = ax.bar(years, nan_values_percentage, label='Percentage of nan \nvalues in FINO1 \nwind speed data')
    ax.axhline(y=0.628, label='Given capacity factor \nin Hölling et al. (2021)', c='r')
    ax.legend(loc=(1.01, 0.5))
    ax.set_title('Wind Capacity Factor of Weather Years at FINO1 Station')
    return (
        ax,
        capacity_factors,
        f,
        nan_values_percentage,
        p,
        share_nan_values,
    )


@app.cell
def _(plt, wind_data):
    plt.plot(wind_data[2012][:10000])
    return


@app.cell
def _():
    energy_per_ton = {"v_60%": 3.85, "v_80%": 3.63, "v_100%": 3.53}
    month_names = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    return energy_per_ton, month_names


@app.cell(hide_code=True)
def _(mo, years):
    year_slider =  mo.ui.slider(steps=years)
    return (year_slider,)


@app.cell
def _(mo, year_slider):
    mo.hstack([year_slider, mo.md(f"Has value: {year_slider.value}")])
    return


@app.cell(hide_code=True)
def _(energy_per_ton, month_names, pd, wind_data, year_slider):
    production_sums = {
        f"max_{key}": [
            sum(wind_data[year_slider.value][i * 4380 : (i + 1) * 4380])
            * (1 / 6)
            / energy_per_ton[key]
            for i in range(12)
        ]
        for key in energy_per_ton.keys()
    }
    production_sums["planned"] = [
        1000000 *
        (sum(wind_data[year_slider.value][i * 4380 : (i + 1) * 4380]) 
         / sum(wind_data[year_slider.value])
        ) 
        for i in range(12)
    ]

    df = pd.DataFrame.from_dict(
        production_sums, orient="index", columns=month_names
    )
    df_trans = df.transpose()
    return df, df_trans, production_sums


@app.cell(hide_code=True)
def _(df_trans, year_slider):
    df_trans.plot(
        kind='bar', 
        stacked=False, 
        title=f'Montly Steel Production Goals for {year_slider.value}')
    return


@app.cell(hide_code=True)
def _(energy_per_ton, pd, wind_data, years):
    total_production = {key: [sum(wind_data[year])*(1/6)/energy_per_ton[key] for year in years] for key in energy_per_ton.keys()}
    total_production['1 Mt'] = [1000000 for _ in years]
    df_years = pd.DataFrame.from_dict(
        total_production, orient="index", columns=years
    )
    df_years_trans = df_years.transpose()
    df_years_trans.plot(
        kind='bar', 
        stacked=False, 
        title=f'Yearly Steel Production Goals')
    return df_years, df_years_trans, total_production


if __name__ == "__main__":
    app.run()
