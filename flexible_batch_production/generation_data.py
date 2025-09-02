#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 31 07:50:38 2024

@author: dafu_res, gom-lewil
"""

import requests
import pandas as pd
import windpowerlib as wpl
import numpy as np
import math

def calc_power_coef(wind_speed, 
               turn_on_speed=3,
               nominal_speed=10.5, 
               turn_off_speed=34):
    """
    Function returning Power Coefficient for Haliade Wind Turbine described by Hölling et al. 
    2021

    Arguments: 
        wind_speed: value of the current wind speed
        turn_on_speed: minimal wind speed required for generation
        nominal_speed: wind speed where maximum generation is reached
        turn_off_speed: maximum wind speed after which plant is turned off due to safety
    """
    if wind_speed < turn_on_speed or wind_speed > turn_off_speed:
        return 0
    elif wind_speed > nominal_speed:
        return 1
    else: 
        return (wind_speed/nominal_speed)**3


def load_haliade_x_12():
    """
    Load the wind turbine model for the GE Haliade X 12 in winpower lib
    """
    wind_speeds= [x/10 for x in range(0, 351, 5)]
    power_coef_curve = [calc_power_coef(speed) for speed in wind_speeds]

    coef_dict =  {'wind_speed': wind_speeds, 
                  'value': power_coef_curve} 
    power_dict =  {'wind_speed': wind_speeds, 
                   'value': [value*12000000 for value in power_coef_curve]} 
    return wpl.wind_turbine.WindTurbine(hub_height=150, 
                                        power_coefficient_curve=coef_dict,
                                        power_curve=power_dict,
                                        turbine_type='Haliade-X-12',
                                        rotor_diameter=220,
                                        nominal_power=12000000,)


def get_wind_farm_output(weather_data_path, P_inst=693, warning=True):
    """
    Calculates the output in MW 

    Arguments: 
        weather_data_path: file path to weather data csv as required for windpowerlib
        P_inst: Netto amount of installed megawatt wind park
        warning: Boolean value if warning about assumed nan values in weather data is shown 
    """
    turbine = load_haliade_x_12()
    wind_turbine_fleet = pd.DataFrame(
        {'wind_turbine': [turbine],  # as windpowerlib.WindTurbine
         'total_capacity': [P_inst]})

    weather_df = pd.read_csv(weather_data_path,
                            index_col=0,
                            header=[0, 1],
                            )
    for i, n in zip(weather_df.isna().sum().index, weather_df.isna().sum()):
        if (n > 0) and warning:
            print(f'Warning: Assumed {n} NaN values for {i[0]} measurement at height {i[1]}.') 
    weather_df = weather_df.bfill()

    example_farm = wpl.WindFarm(name='example_farm', wind_turbine_fleet=wind_turbine_fleet)
    mc_example_farm = wpl.TurbineClusterModelChain(example_farm).run_model(weather_df)
    power_output = mc_example_farm.power_output
    power_output_list = power_output.to_list()
    return power_output_list
