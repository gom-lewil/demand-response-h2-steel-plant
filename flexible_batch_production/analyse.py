import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pyomo.environ as pyo
import numpy as np

def model_summary_plot(model, startdate, time_range=-1):
    """
    Visualises a summary of a successfully calculated model output from pyomo for a given time 
    range. This includes multiple subplots:
        1. Overview of power consumption of green steel production plant units
        2. Overview of batch starts in steel making equipments 
        3. Storage content of Hydrogen and direct reduced iron
        4. Power exchange between plant and grid - visualizing
    """
    if type(time_range) != range:
        time_range = range(len(model.T)) # if no range was given take whole time range

    time_series = np.array([startdate + np.timedelta64(10, 'm')*step 
                            for step in model.T if step in time_range])

    f, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(5, 1, figsize=(10, 15), 
                                                gridspec_kw={'height_ratios': [2, 1, 1, 1, 1]},
                                                sharex=True)

    plots = []
    ax1_1 = ax1.twinx()
    steel_produced = [sum([pyo.value(model.steel_produced_in_eq[e, t]) for e in model.E]) 
                      for t in model.T if t in time_range]
    steel_plot = ax1_1.step(time_series, 
                            steel_produced, 
                            label='Produced Steel', 
                            color='black')
    ax1_1.get_yaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ','))
    )
    ax1_1.set_ylabel('Tons Steel')
    plots.append(steel_plot[0])

    for e in model.E:
        eaf_load = np.array([pyo.value(model.equipment_load_profile[e, t]) 
                             for t in model.T if t in time_range])
        rolling_load = np.array([pyo.value(model.rolling_load[e, t]) 
                                 for t in model.T if t in time_range])
        
        rolling_plot = ax1.fill_between(time_series, np.zeros(len(time_series)), rolling_load, 
                                        step='pre', alpha=1, linewidth=0,
                                        label='Casting & Rolling Consumption', color='#deebf7')
        plots.append(rolling_plot)

        steelmaking_plot = ax1.fill_between(time_series, rolling_load, rolling_load+eaf_load, 
                                            step='pre', alpha=1, linewidth=0, 
                                            label=str(e) + ' Consumption', color='#4472c4')
        plots.append(steelmaking_plot)

    ru_load = np.array([pyo.value(model.electricity_consumption_electrolysers[t]) 
                        for t in model.T if t in time_range])
    reduction_unit_plot = ax1.fill_between(time_series, 
                                           rolling_load+eaf_load, 
                                           rolling_load+eaf_load+ru_load, 
                                           step='pre', alpha=1, linewidth=0, 
                                           label='Reduction Unit Consumption', color='#5b9bd5')
    plots.append(reduction_unit_plot)
    
    plant_power_load = [-pyo.value(model.power_exchange[t]) 
                        + pyo.value(model.renewable_generation[t]) 
                        for t in model.T if t in time_range]
    plant_power_plot = ax1.step(time_series, plant_power_load, c='#000', linewidth=0.5,
                                label='Total Power Plant Consumption', )
    plots.append(plant_power_plot[0])
    

    renewable_generation = [pyo.value(model.renewable_generation[t]) 
                            for t in model.T if t in time_range]
    renewable_generation_plot = ax1.step(time_series, renewable_generation, 
                                         label='Renewable generation', color='g')
    
    fuel_cell_generation = [pyo.value(model.fc_generation[t]) for t in model.T if t in time_range]
    if sum(fuel_cell_generation) > 0:
        fuel_cell_generation_plot = ax1.step(
            time_series,
            fuel_cell_generation,
            c='r',
            linewidth=0.5,
            label='Fuel Cell Power generation'
        )
        plots.append(fuel_cell_generation_plot[0]) 

    ax1.set_ylabel('Power in MW')
    ax1.set_title('Electricity Exchange')
    ax1.grid(True)


    labels = [l.get_label() for l in plots]
    ax1.legend(plots, labels, loc=(1.1, 0.3))

    # ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y %H:%M'))
    # ax1.xaxis.set_major_locator(mdates.DayLocator())

    for v in model.V:
        ax2.step(time_series, 
                 [pyo.value(model.equipment_decision_turnon[v, t]) 
                  for t in model.T if t in time_range], 
                 label= str(v[1]) + ' turnon')
    try:
        ax2.step(time_series, 
            [pyo.value(model.electrolysers_decision_turnon[t]) 
            for t in model.T if t in time_range], 
            label='Electrolyser running',
            linewidth=0.5)
    except:
        pass
    ax2.set_ylabel('Binary On/Off')
    ax2.legend(loc=(1.1, 0.35))
    ax2.set_title('Equipment TurnOn')
    
    ax3.set_ylabel('MWh in Hydrogen Tank')
    h2_plot = ax3.step(
        time_series, 
        [pyo.value(model.h2_storage_content[t]) for t in model.T if t in time_range], 
        label='Hydrogen Tank Energy Content',
        color='#0a9396',
        alpha=0.5,
    )
   
    ax3_1 = ax3.twinx()
    dri_storage = [pyo.value(model.DRI_storage_content[t]) 
                   for t in model.T if t in time_range]
    dri_plot = ax3_1.step(
        time_series, 
        dri_storage, 
        label='DRI storage', 
        color='#ca6702',
        alpha=1
    )
    
    intermediate_steel_products = (
        [sum([pyo.value(model.slabs_and_billets_storage[v, t]) for v in model.V])
         for t in model.T if t in time_range]
    )
    intermediate_steel_products_plot = ax3_1.step(
        time_series,
        intermediate_steel_products,
        label='Steel slabs & billets Storage Content',
        color='grey',
    )
    ax3_1.set_ylabel('Tons')
    ax3_1.get_yaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ','))
    )

    # Add legend for both y-axes
    plots = h2_plot + dri_plot + intermediate_steel_products_plot
    labels = [l.get_label() for l in plots]
    ax3.legend(plots, labels, loc=(1.1, 0.35))
    ax3.set_title('Storage Content: Hydrogen and Intermediate Steel Products')
    
    
    data = [pyo.value(model.power_exchange[t]) for t in model.T if t in time_range]
    ax4.step(time_series, data, label='Power Exchange')
    if model.given_goal_load:
        goal_load = pyo.value(model.goal_load)
    else: 
        goal_load = pyo.value(model.mean_power_exchange)
    ax4.fill_between(time_series, 
                     data, 
                     goal_load + np.zeros(len(data)), 
                     step='pre', 
                     alpha=0.2, 
                     color='b', 
                     label='Deviation from Goal Load')
    ax4.axhline(y=goal_load, 
                color='r', 
                linestyle='-', 
                label='Goal Load = ' + str(round(goal_load, 2)))
    ax4.set_ylabel('Power in MW')
    ax4.legend(loc= (1.1, 0.4))
    ax4.set_title('Power Exchange between Plant and Grid')

    ax5.set_title('Profit and Losses from Electricty Market')
    ax5.set_ylabel('Euro')
    ax5.get_yaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ','))
    )
    ax5.set_xlabel('Time')
    profit_plot = ax5.step(
        time_series,
        [pyo.value(model.electricity_market_profit[t]) for t in model.T if t in time_range], 
        label='Electricity Market Profits',
        c = '#0a9396'
    )
    ax5_1 = ax5.twinx()
    ax5_1.set_ylabel('Price €/MWh')
    price_plot = ax5_1.step(
        time_series,
        [pyo.value(model.electricity_price[t]) for t in model.T if t in time_range], 
        label='Current Price €/MWh',
        c='#e9d8a6'
    )
    plots = profit_plot  + price_plot

    if model.draw_power_from_grid:
        costs_plot = ax5.step(
            time_series,
            [-pyo.value(model.electricity_market_cost[t]) 
             for t in model.T if t in time_range],
            label='Electricity Cost & Grid Charge',
            c='#bb3e03'
        )
        plots += costs_plot

    labels = [l.get_label() for l in plots]
    ax5.legend(plots, labels, loc=(1.1, 0.4))
    return f


def loaded_model_summary_plot(model_data, 
                              startdate, 
                              timedelta=np.timedelta64(10, 'm'),
                              time_range=-1, 
                              show_produced_steel=True, 
                              ):
    """ Visualises model data from a loaded model 
    Visualises a summary of a successfully calculated model stored via safe_model_results 
    funtion for a given time range. This includes multiple subplots:
        1. Overview of power consumption of green steel production plant units
        2. Overview of batch starts in steel making equipments 
        3. Storage content of Hydrogen and direct reduced iron
        4. Power exchange between plant and grid - visualizing

    Arguments:
        model_data: dictionary loaded with flexible_batch_production.load.load_model()
        startdate: startdate of the model
        timerange: range of time indexesto be visualised 
    """
    if type(time_range) != range:
        time_range = range(len(model_data['renewable_generation'])) 
    
    time_series = np.array([startdate + timedelta*step for step in time_range])

    f, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(
        5, 1, figsize=(10, 15), 
        gridspec_kw={'height_ratios': [2, 1, 1, 1, 1]},
        sharex=True
    )

    plots = []
    if show_produced_steel:
        ax1_1 = ax1.twinx()
        steel_produced = [float(model_data['steel_produced'][i]) for i in time_range]
        steel_plot = ax1_1.step(time_series, 
                                steel_produced, 
                                label='Produced Steel', 
                                color='black')
        ax1_1.get_yaxis().set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ','))
        )
        ax1_1.set_ylabel('Tons Steel')
        plots.append(steel_plot[0])
    
    eaf_load = np.array([float(model_data['steelmaking_load'][i]) for i in time_range])
    rolling_load = np.array([float(model_data['rolling_load'][i]) for i in time_range])
        
    rolling_plot = ax1.fill_between(
        time_series, np.zeros(len(time_series)), rolling_load, step='pre', 
        label='Casting & Rolling Consumption', color='#deebf7', linewidth=0
    )
    plots.append(rolling_plot)

    steelmaking_plot = ax1.fill_between(
        time_series, rolling_load, rolling_load+eaf_load, step='pre', label='e_EAF Consumption', 
        color='#4472c4', linewidth=0
    )
    plots.append(steelmaking_plot)

    ru_load = np.array([float(model_data['electrolyser_load'][i]) for i in time_range])
    reduction_unit_plot = ax1.fill_between(
        time_series, rolling_load+eaf_load, rolling_load+eaf_load+ru_load, step='pre', 
        label='Reduction Unit Consumption', color='#5b9bd5', linewidth=0
    )
    plots.append(reduction_unit_plot)
    
    power_plant_load = [-float(model_data['power_exchange'][t]) 
                        + float(model_data['renewable_generation'][t]) for t in time_range]
    power_plant_plot = ax1.step(time_series, power_plant_load, c='#000', linewidth=0.5,
             label='Total Power Plant Consumption')
    plots.append(power_plant_plot[0])

    renewable_generation = [float(model_data['renewable_generation'][i]) for i in time_range]
    renewable_generation_plot = ax1.step(
        time_series, renewable_generation, label='Renewable generation', color='g'
    )
    plots.append(renewable_generation_plot[0])

    fuel_cell_generation = [float(model_data['fuel_cell_generation'][i]) for i in time_range]
    if sum(fuel_cell_generation) > 0:
        fuel_cell_generation_plot = ax1.step(
            time_series,
            fuel_cell_generation,
            c='r',
            linewidth=0.5,
            label='Fuel Cell Power generation'
        )
        plots.append(fuel_cell_generation_plot[0])

    ax1.set_ylabel('Power in MW')
    labels = [l.get_label() for l in plots]
    ax1.legend(plots, labels, loc=(1.12, 0.3))
    ax1.set_title('Electrical Power Generation & Consumption')

    colors = {'v_60%': '#1f77b4', 'v_80%': '#ff7f0e', 'v_100%': '#2ca02c'}
    for v in model_data['turnon'].keys():
        if not (model_data['turnon'][v] == [] or np.isnan(model_data['turnon'][v][0])):
            ax2.step(time_series, 
                    [float(model_data['turnon'][v][i]) for i in time_range], 
                    label= str(v) + ' in use', 
                    color=colors[v])
    ax2.set_ylabel('Binary On/Off')
    ax2.legend(loc=(1.1, 0.35))
    ax2.set_title('Steel Making Virtual Equipment Use')

    
    ax3.set_ylabel('MWh in Hydrogen Tank')
    ax3.get_yaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ','))
    )
    h2_plot = ax3.step(
        time_series, 
        [float(model_data['tank_hydrogen_content'][i]) for i in time_range], 
        label='Hydrogen Tank Content',
        color='#0a9396',
        alpha=0.5,
    )

    ax3_1 = ax3.twinx()
    
    dri_storage = [float(model_data['DRI_storage_content'][i]) for i in time_range]
    dri_plot = ax3_1.step(
        time_series, 
        dri_storage, 
        label='Direct Reduced Iron', 
        color='#ca6702',
    )

    intermediate_steel_products = [
        sum([
            float(model_data['slabs_billets_storage'][key][t]) 
            for key in model_data['slabs_billets_storage'].keys()
            ]) 
        for t in time_range
    ]
    intermediate_steel_products_plot = ax3_1.step(
        time_series,
        intermediate_steel_products,
        label='Steel Slabs & Billets',
        color='grey',
    )

    ax3_1.set_ylabel('Tons')
    ax3_1.get_yaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ','))
    )
    plots = h2_plot + dri_plot + intermediate_steel_products_plot
    labels = [l.get_label() for l in plots]
    ax3.legend(plots, labels, loc=(1.1, 0.35))
    ax3.set_title('Storage Contents')
    
    
    power_exchange = [float(model_data['power_exchange'][i]) for i in time_range]
    ax4.step(time_series, power_exchange, label='Power Exchange')
    mean = float(model_data['mean_power_exchange'][0])
    ax4.axhline(y=mean, 
                color='r', 
                linestyle='-', 
                label='Goal Load')
    ax4.set_ylabel('Power in MW')
    ax4.legend(loc= (1.1, 0.4))
    ax4.set_title('Goal and real Power Exchange between Plant and Grid')

    ax5.set_title('Economics')
    ax5.set_ylabel('€ at Day-Ahead Spot Market')
    ax5.get_yaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ','))
    )
    ax5.set_xlabel('Time')

    profit = [float(model_data['profits'][i]) for i in time_range]
    profit_plot = ax5.step(
        time_series,
        profit, 
        label='Electricity Market Sell Profit',
        c = '#0a9396'
    )

    ax5_1 = ax5.twinx()
    ax5_1.set_ylabel('Price €/MWh')
    price_plot = ax5_1.step(time_series,
                            [float(model_data['electricity_price'][i]) for i in time_range], 
                            label='Current Price €/MWh',
                            c='#e9d8a6')#

    plots = profit_plot + price_plot 

    if model_data['cost'] != []:
        cost = [-float(model_data['cost'][i]) for i in time_range]
        costs_plot = ax5.step(
            time_series,
            cost,
            label='Electricity Cost',
            c='#bb3e03'
        )
        
        plots = profit_plot  + price_plot + costs_plot
    
    
    labels = [l.get_label() for l in plots]
    ax5.legend(plots, labels, loc=(1.1, 0.4))
    return f


def sort_model_data(
    loaded_model_data,
    sort_key='renewable_generation',
    do_not_sort = ['minutes_per_step','mass_production','mean_power_exchange']      
):
    """ Sorts and returns loaded model data in regards to given key
    
    Arguments: 
        loaded_model_data: dictionary loaded with flexible_batch_production.load.load_model()
        sort_key: key value which is used for sorting algorithm
        do_not_sort: key values of loaded_model_data which should not be sorted 
    """
    sorted_model_data = loaded_model_data
    indexes_sorted = [i for i in range(len(loaded_model_data[sort_key]))]
    indexes_sorted = sorted(range(len(loaded_model_data[sort_key])), 
                            key=loaded_model_data[sort_key].__getitem__,
                            reverse=True)

    for key in loaded_model_data.keys():
        if key in do_not_sort:
                    pass
        elif type(loaded_model_data[key]) == dict:
            for key2 in loaded_model_data[key].keys():
                sorted_model_data[key][key2] = [
                    loaded_model_data[key][key2][i] for i in indexes_sorted
                ]
        else:
            sorted_model_data[key] = [loaded_model_data[key][i] for i in indexes_sorted]
    return sorted_model_data


def sorted_model_summary_plot(loaded_model_data, 
                              sort_key='renewable_generation', 
                              do_not_sort='',
                              time_range=-1, fill_line=0.1, alpha=0.5, title=''):
    """ Visualises model data from a loaded model 
    Visualises a sorted summary of a successfully calculated model stored via safe_model_results 
    funtion for a given time range. This includes multiple subplots:
        1. Overview of power consumption of green steel production plant units
        2. Overview of batch starts in steel making equipments 
        3. Storage content of Hydrogen and direct reduced iron
        4. Power exchange between plant and grid - visualizing

    Arguments:
        loaded_model_data: dictionary loaded with flexible_batch_production.load.load_model()
        sort_key: key value which is used for sort
        do_not_sort: key values of loaded_model_data which should not be sorted 
        timerange: range of time indexesto be visualised 
    """

    if do_not_sort:
        loaded_model_data = sort_model_data(loaded_model_data, 
                                            sort_key=sort_key, 
                                            do_not_sort=do_not_sort)
    else:
        loaded_model_data = sort_model_data(loaded_model_data, sort_key=sort_key)
        
    if type(time_range) != range:
        time_range = range(len(loaded_model_data['renewable_generation'])) 
    
    time_series = time_range

    f, (ax1, ax2, ax3, ax4) = plt.subplots(
        4, 1, figsize=(13, 10), 
        gridspec_kw={'height_ratios': [2, 1, 1, 1]},
        sharex=True
    )    

    plots = []
    eaf_load = np.array([float(loaded_model_data['steelmaking_load'][i]) for i in time_range])
    rolling_load = np.array([float(loaded_model_data['rolling_load'][i]) for i in time_range])
        
    rolling_plot = ax1.fill_between(time_series, np.zeros(len(time_series)), rolling_load, step='pre',
                        alpha=alpha, label='Casting & Rolling \nConsumption', color='#deebf7', 
                        linewidth=fill_line)
    plots.append(rolling_plot)

    steelmaking_plot = ax1.fill_between(time_series, rolling_load, rolling_load+eaf_load, step='pre', 
                        alpha=alpha, label='Steel Making Consumption', color='#4472c4', linewidth=fill_line)
    plots.append(steelmaking_plot)

    ru_load = np.array([float(loaded_model_data['electrolyser_load'][i]) for i in time_range])
    if sum(ru_load) > 0:
        reduction_unit_plot = ax1.fill_between(
            time_series, rolling_load+eaf_load, rolling_load+eaf_load+ru_load, step='pre', 
            alpha=alpha, label='Reduction Unit \nConsumption', color='#5b9bd5', 
            linewidth=fill_line)
        plots.append(reduction_unit_plot)

    renewable_generation = [float(loaded_model_data['renewable_generation'][i]) for i in time_range]
    renewable_generation_plot = ax1.step(time_series, renewable_generation, 
                                         label='Renewable Generation', color='g')
    plots.append(renewable_generation_plot[0])

    fuel_cell_generation = [float(loaded_model_data['fuel_cell_generation'][i]) for i in time_range]
    if sum(fuel_cell_generation) > 0:
        fuel_cell_generation_plot = ax1.step(
            time_series,
            fuel_cell_generation,
            c='r',
            linewidth=0.5,
            label='Fuel Cell \nPower Generation'
        )
        plots.append(fuel_cell_generation_plot[0])

    ax1.set_ylabel('Power in MW')
    labels = [l.get_label() for l in plots]
    ax1.legend(plots, labels)#, loc=(1.1, 0.3))
    ax1.set_title('Electrical Power Generation & Consumption')

    colors = {'v_60%': '#1f77b4', 'v_80%': '#ff7f0e', 'v_100%': '#2ca02c'}

    for v in sorted(loaded_model_data['turnon'].keys()):
        if not (loaded_model_data['turnon'][v] == [] or np.isnan(loaded_model_data['turnon'][v][0])):
            ax2.step(time_series, 
                    [float(loaded_model_data['turnon'][v][i]) for i in time_range], 
                    label= str(v) + ' in use', 
                    color=colors[v],
                    linewidth=0.5)
    # ax2.step(time_series, 
    #          [float(model_data['electrolyser_running'][i]) for i in time_range], 
    #          label='Electrolyser running',
    #          linewidth=0.5)
    ax2.set_ylabel('Binary Off/On ')
    ax2.legend()#loc=(1.1, 0.35))
    ax2.set_title('Steel Making Virtual Equipment Use')

    power_exchange = [float(loaded_model_data['power_exchange'][i]) for i in time_range]
    ax3.step(time_series, power_exchange, label='Power Exchange', linewidth=0.5)
    mean = float(loaded_model_data['mean_power_exchange'][0])
    ax3.axhline(y=mean, 
                color='r', 
                linestyle='-', 
                label='Goal Load')
    ax3.set_ylabel('Power in MW')
    ax3.legend()#loc= (1.1, 0.4))
    ax3.set_title('Goal and real Power Exchange between Plant and Grid')

    ax4.set_title('Economics')
    ax4.set_ylabel('€ at Day-Ahead Spot Market')
    ax4.get_yaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ','))
    )
    ax4.set_xlabel('Sorted Annual Time Steps')

    profit = [float(loaded_model_data['profits'][i]) for i in time_range]
    profit_plot = ax4.step(
        time_series,
        profit, 
        label='Sales at Electricity Market Profit',
        c = '#0a9396'
    )

    ax4_1 = ax4.twinx()
    ax4_1.set_ylabel('Price €/MWh')
    price_plot = ax4_1.step(time_series,
                            [float(loaded_model_data['electricity_price'][i]) for i in time_range], 
                            label='Current Price €/MWh',
                            c='#e9d8a6')#

    plots = profit_plot + price_plot 

    if not (loaded_model_data['cost'] == [] or np.isnan(loaded_model_data['cost'][0])):
        cost = [-float(loaded_model_data['cost'][i]) for i in time_range]
        costs_plot = ax4.step(
            time_series,
            cost,
            label='Buying at Electricity Market Cost',
            c='#bb3e03'
        )
        
        plots = profit_plot  + price_plot + costs_plot
    
    
    labels = [l.get_label() for l in plots]
    ax4.legend(plots, labels, loc='lower left')#, loc=(1.1, 0.4))
    if title:

        f.suptitle(title, fontsize=20)
    
# Re-arrange legends to last axis
    all_axes = f.get_axes()
    for axis in all_axes:
        legend = axis.get_legend()
        if legend is not None:
            legend.remove()
            all_axes[-1].add_artist(legend)
    return f


def summary(model, print_results=True, decimal_precision=2):
    """
    Gives a descriptive summary with most important information about a feasible and finished
    model.  
    """
    results = {}
    renewable_generation = [pyo.value(model.renewable_generation[t]) for t in model.T]
    fuel_cell_generation = [pyo.value(model.fc_generation[t]) for t in model.T]

    results['Renewable Input'] = {
        'Generation [MWh]': sum(renewable_generation)*(pyo.value(model.minutes_per_step)/60),
        'Capacity Factor [%]': (
            sum(renewable_generation)
            / (max(renewable_generation)*len(renewable_generation)) 
        ), 
    }
    results['Reduction Unit'] = {
        'Reduction Unit Energy Consumption [MWh]': (
            sum([pyo.value(model.electricity_consumption_electrolysers[t]) for t in model.T])
            * (pyo.value(model.minutes_per_step)/60) 
        ),
        'Total Hydrogen Production [MWh]': (
            sum([pyo.value(model.h2_MWh_for_DRI[t]) for t in model.T]) 
            + pyo.value(model.h2_storage_content[model.T.at(-1)])
        ),
        'Total DRI Production [ton]': (
            sum([pyo.value(model.h2_MWh_for_DRI[t]) for t in model.T]) 
            / pyo.value(model.h2_MWh_per_DRI)
        ) 
    }
    if sum(fuel_cell_generation) > 0:
        results['Fuel Cell'] = {
            'FC Hydrogen Consumption [MWh]': (
                (sum(fuel_cell_generation) * model.minutes_per_step/60) / model.fc_efficiency
            ),
            'FC Electricity Generation [MWh]': (
                (sum(fuel_cell_generation) * model.minutes_per_step/60)
            ),
        }
    results['Steel making'] = {
        'Steel making Energy Consumption [MWh]': (
            sum([pyo.value(model.equipment_load_profile[e,t]) for e in model.E for t in model.T])
            * (pyo.value(model.minutes_per_step)/60)     
        ),
        'Total Intermediate Steel Products [ton]': sum(
            [pyo.value(model.equipment_decision_turnon[v, t])
             * pyo.value(model.output_steel_products[v]) for v in model.V for t in model.T]
        ),
        'Virtual Equipments Turnon': {
            v: sum([pyo.value(model.equipment_decision_turnon[v, t]) for t in model.T]) 
            for v in model.V
        }
    }
    results['Rolling'] = {
        'Rolling Energy Consumption [MWh]': (
            sum([pyo.value(model.rolling_load[e,t]) for e in model.E for t in model.T])
            * (pyo.value(model.minutes_per_step)/60) 
        )
    }
    results['Green Steel Production Plant'] = {
        'Total Production Steel [ton]': (
            sum([pyo.value(model.steel_produced_in_eq[e, model.T.at(-1)]) for e in model.E])
        ),
        'Total Energy Consumption [MWh]': (
            ( # Total amount of consumed energy
                sum(renewable_generation) 
                - sum([pyo.value(model.power_exchange[t]) for t in model.T])
            ) * (pyo.value(model.minutes_per_step)/60) 
        ),
        'Consumed Energy per Unit Steel [MWh/ton]': (
            ( # Total amount of consumed energy
                sum(renewable_generation) 
                - sum([pyo.value(model.power_exchange[t]) for t in model.T])
            ) * (pyo.value(model.minutes_per_step)/60) 

            # Divided by total production of steel
            / sum([pyo.value(model.steel_produced_in_eq[e, model.T.at(-1)]) for e in model.E])
        ),
    }
    total_price_sold =  sum([pyo.value(model.electricity_market_profit[t]) for t in model.T])
    if model.draw_power_from_grid:
        total_cost_bought = sum([pyo.value(model.electricity_market_cost[t]) for t in model.T])

    if model.draw_power_from_grid:
        results['Economical'] = {
            'Total price of sold Electricity [€]': total_price_sold,
            'Total cost of bought Electricity [€]' : total_cost_bought,
            'Power Grid Charges (LP) [€]' : pyo.value(model.grid_charges_power),
            'Sum [€]' : (
                total_price_sold - total_cost_bought - pyo.value(model.grid_charges_power)
            ),
        }
    else: 
        results['Economical'] = {
            'Total price of sold Electricity [€]': total_price_sold,
        }

    if print_results:
        for part, values in results.items():
            print(f"\n {part:{'-'}^{60}} ")
            for name, value in values.items():
                if type(value) == dict:
                    print(f"\t{5*'-'} {name} {5*'-'}")
                    for n,v in value.items():
                        print(f"\t {n}: {v:,.0f}")
                else:
                    print(f"{name:<40} {value:>15,.{decimal_precision}f}")
    return results


def hourlize_model_data(
        loaded_model_data,
        step_size = 6,
        do_not_hourlize = ['minutes_per_step','mass_production', 'mean_power_exchange']      
):
    """ Summarises loaded model data in hourly steps """
    hourlized_model_data = loaded_model_data
    indexes = range(0, len(loaded_model_data['renewable_generation']), step_size)

    for key in loaded_model_data.keys():
        if key in do_not_hourlize:
            pass
        elif type(loaded_model_data[key]) == dict:
            for key2 in loaded_model_data[key].keys():
                hourlized_model_data[key][key2] = [
                    max(loaded_model_data[key][key2][i:i+step_size]) for i in indexes
                ]
        elif key in ['electrolyser_running']:
             hourlized_model_data[key] = [
                max(loaded_model_data[key][i:i+step_size]) for i in indexes
            ]
        else:
            hourlized_model_data[key] = [
                np.mean(loaded_model_data[key][i:i+step_size]) for i in indexes
            ]
    return hourlized_model_data
