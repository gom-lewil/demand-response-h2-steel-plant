import pyomo.environ as pyo
from pyomo.opt import SolverFactory
import csv

def solve_model(model, solver=SolverFactory('gurobi'), tee=False, max_runtime=-1, mipgap=0):
    """ Starts solving of model with the given solver

    Arguments: 
        model: Optimisation problem created with .construct.multi_equipment_model()
        solver: usable solver from Solver Factory of pyomo
        tee: Boolean if output from solver is shown in terminal
        max_runtime: maximum amounts of seconds solver can run
        mipgap: minimum value of model quality which solver has to reach
    """
    # Solve the optimization problem
    if max_runtime > 0:
        solver.options['TimeLimit'] = max_runtime  # for gurobi use parameter 'TimeLimit' for cbc 'sec'
    if mipgap > 0:
        solver.options['mipgap'] = mipgap
    return solver.solve(model, tee=tee)


def safe_model_results(model, filename='1_output/model_results.csv'):
    """ Method to store the reults of a solved model in a csv file. 

    Arguments: 
        model: solved model data created with .construct.multi_equipment_model() 
        filename: path to store results
    """
    data_to_safe = [  # usual variable
        # Parameter
        model.T,
        model.E,
        model.V,
        model.B,
        model.minutes_per_step,
        model.steel_demand,  
        model.renewable_generation,  # pyo.Param(model.T)
        model.electricity_price,
        model.max_capacity_electrolyser, 
        model.min_consumption_electrolyser,
        model.electrolyser_efficiency,
        model.nominal_cap_hydrogen_tank,
        model.initial_h2_tank_filling,  # pyo.Param()
        model.h2_MWh_per_DRI, 
        model.fc_capacity, 
        model.fc_efficiency, 
        model.batch_load_profile,
        model.DRI_demand,
        model.output_steel_products,
        model.virtual_equipment_duration,
        model.T_pause,
        model.rolling_duration,
        model.rolling_cap,
        model.rolling_mass_efficiency,
        model.given_goal_load,
        model.draw_power_from_grid,

        # Variables        
        model.equipment_decision_turnon, 
        model.electrolysers_decision_turnon, 
        model.electricity_consumption_electrolysers,  
        model.fc_generation,
        model.h2_MWh_for_DRI,
        model.h2_MWh_storage_flow,
        model.virtual_eq_running,  
        model.equipment_running,  
        model.equipment_load_profile,  
        model.rolling_running,
        model.rolling_load,
        model.power_to_grid,
        model.power_exchange,
        model.dist_power_exchange_above_mean,  
        model.dist_power_exchange_below_mean, 
        model.load_jump, 
        model.h2_storage_content, 
        model.output_steel_products,
        model.DRI_storage_content,
        model.slabs_and_billets_storage,
        model.steel_produced_in_eq,
        model.electricity_market_profit,
        model.electricity_market_cost,
    ]

    if model.given_goal_load: # depending on objective safe given goal load ...
        data_to_safe.append(model.goal_load)
    else: # ...  or calculated mean
        data_to_safe(model.mean_power_exchange)
    
    
    if model.draw_power_from_grid:  # When power can be utilised from grid store dependend vars
        data_to_safe.append(model.grid_charge_power_price)
        data_to_safe.append(model.grid_charge_energy_price)
        data_to_safe.append(model.power_from_grid)
        data_to_safe.append(model.max_power_from_grid)
    
    with open(filename, 'w') as f:
        write = csv.writer(f)

        for data in data_to_safe:
            for key, value in data.items(): 
                if type(key) == tuple:
                    key = data.getname(), *key
                elif type(key) == str:
                    key = data.getname(), key
                else:
                    key = data.getname()

                if type(value) == float:
                    write.writerow([key, value])
                elif type(value) == int:
                    write.writerow([key, value])
                elif type(value) == list:
                    write.writerow([key, value])
                else:
                    write.writerow([key, value.value])
    return None
