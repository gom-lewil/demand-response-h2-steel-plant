import pandas as pd
import flexible_batch_production as fbp
import numpy as np

def load_model(run_id):
    """Load model results from save files and output folder into a dictionary for further 
    analysis
    
    argument: 
        run_id: string of id of the model run which should be loaded, folder name in which model
                safe files are taken from
    """
    model = pd.read_csv(f'1_output/{run_id}/model_results.csv', sep=',', names=['index', 'value']) 

    model_loaded = {}

    # model_loaded['T'] = model.loc[model['index' == 'T']]['value']
    # model_loaded['U'] = model.loc[model['index' == 'E']]['value']
    # model_loaded['V'] = model.loc[model['index' == 'V']]['value']

    model_loaded['minutes_per_step'] = float(model.loc[model['index'] == 'minutes_per_step']['value'].iloc[0])
    model_loaded['renewable_generation'] = [float(i) for i in model.loc[model['index'].str.contains('renewable_generation')]['value'].to_list()]
    model_loaded['fuel_cell_generation'] = [float(i) for i in model.loc[model['index'].str.contains('fc_generation')]['value'].to_list()]
    model_loaded['electrolyser_load'] = [float(i) for i in model.loc[model['index'].str.contains('electricity_consumption_electrolysers')]['value'].to_list()]
    model_loaded['steelmaking_load'] = [float(i) for i in model.loc[model['index'].str.contains('equipment_load_profile')]['value'].to_list()]
    model_loaded['rolling_load'] = [float(i) for i in model.loc[model['index'].str.contains('rolling_load')]['value'].to_list()]
    model_loaded['power_exchange'] = [float(i) for i in model.loc[model['index'] == 'power_exchange']['value'].to_list()]
    model_loaded['load_jump'] = [float(i) for i in model.loc[model['index'].str.contains('load_jump')]['value'].to_list()]
    model_loaded['power_from_grid'] = [float(i) for i in model.loc[model['index'].str.contains('power_from_grid')]['value'].to_list()]
    model_loaded['power_to_grid'] = [float(i) for i in model.loc[model['index'].str.contains('power_to_grid')]['value'].to_list()]


    model_loaded['turnon'] = {
        'v_60%' : [float(i) for i in model.loc[model['index'].str.contains("'equipment_decision_turnon', 'e_EAF', 'v_60%'")]['value'].to_list()],
        'v_80%' : [float(i) for i in model.loc[model['index'].str.contains("'equipment_decision_turnon', 'e_EAF', 'v_80%'")]['value'].to_list()],
        'v_100%': [float(i) for i in model.loc[model['index'].str.contains("'equipment_decision_turnon', 'e_EAF', 'v_100%'")]['value'].to_list()],
    }
    model_loaded['electrolyser_running'] = [float(i) for i in model.loc[model['index'].str.contains('electrolysers_decision_turnon')]['value'].to_list()]
    #
    model_loaded['mass_production'] = {
        'v_60%' : [float(i) for i in model.loc[model['index'].str.contains("'mass_production', 'e_EAF', 'v_60%'")]['value'].to_list()],
        'v_80%' : [float(i) for i in model.loc[model['index'].str.contains("'mass_production', 'e_EAF', 'v_80%'")]['value'].to_list()],
        'v_100%': [float(i) for i in model.loc[model['index'].str.contains("'mass_production', 'e_EAF', 'v_100%'")]['value'].to_list()]
    }
    
    model_loaded['tank_hydrogen_content'] = [float(i) for i in model.loc[model['index'] == 'h2_storage_content']['value'].to_list()]
    model_loaded['DRI_storage_content'] = [float(i) for i in model.loc[model['index'] == 'DRI_storage_content']['value'].to_list()]
    model_loaded['slabs_billets_storage'] = {
        'v_60%' : [float(i) for i in model.loc[model['index'].str.contains("'slabs_and_billets_storage', 'e_EAF', 'v_60%'")]['value'].to_list()],
        'v_80%' : [float(i) for i in model.loc[model['index'].str.contains("'slabs_and_billets_storage', 'e_EAF', 'v_80%'")]['value'].to_list()],
        'v_100%': [float(i) for i in model.loc[model['index'].str.contains("'slabs_and_billets_storage', 'e_EAF', 'v_100%'")]['value'].to_list()]
    }
    model_loaded['steel_produced'] = [float(i) for i in model.loc[model['index'].str.contains('steel_produced_in_eq')]['value'].to_list()]

    model_loaded['mean_power_exchange'] = [float(i) for i in model.loc[model['index'].str.contains('mean_power_exchange')]['value'].to_list()]
    model_loaded['electricity_price'] = [float(i) for i in model.loc[model['index'].str.contains('electricity_price')]['value'].to_list()]
    model_loaded['profits'] = [float(i) for i in model.loc[model['index'].str.contains('electricity_market_profit')]['value'].to_list()]
    model_loaded['cost'] = [float(i) for i in model.loc[model['index'].str.contains('electricity_market_cost')]['value'].to_list()]
    
    dist_above = [float(i) for i in model.loc[model['index'].str.contains('above_mean')]['value'].to_list()]
    dist_below = [float(i) for i in model.loc[model['index'].str.contains('below_mean')]['value'].to_list()]
    model_loaded['dist_from_goal_load'] = [above + below for above, below in zip(dist_above, dist_below)]

    keys = model_loaded['turnon'].keys()
    return fill_empty_equipments(model_loaded, keys)


def make_filler(length):
    return [np.nan for _ in range(length)]


def fill_empty_equipments(model_data, keys=['v_60%', 'v_80%', 'v_100%']):
    """ Fills time series of unused equipment with nan values in loaded model results
    """
    filler = make_filler(len(model_data['renewable_generation']))

    for key in keys:
        if model_data['turnon'][key] == [] or np.isnan(model_data['turnon'][key][0]):
            model_data['turnon'][key] = filler
            model_data['slabs_billets_storage'][key] = filler
    return model_data


def delete_empty_equipments(model_data, keys=['v_60%', 'v_80%', 'v_100%']):
    """ Deletes time series of unused equipment with nan values in loaded model results
    """
    new_model_data = model_data
    for key in keys:
        if model_data['turnon'][key] == [] or np.isnan(model_data['turnon'][key][0]):
            del new_model_data['turnon'][key]
            del new_model_data['slabs_billets_storage'][key]
    return new_model_data
