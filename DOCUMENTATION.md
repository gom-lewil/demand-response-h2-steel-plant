# Introduction 
In this model steel plant scenarios are modelled in a linear optimisation model developed in pyomo. With the given input data the model optimises the operation schedule over a one year period in a resolution of 10 minute steps and focusses on electric loads of equipment and material flows within the steel plant as well as profits by selling residual electricity, or losses from buying required electricity.

# Input Data

## Wind Generation Profile 
The most important input for the model is the time series of renewable wind generation of the modelled time period. This data was generated as described by Hölling et al. (2021). Wind speed data at height 102 m, temperature and air pressure data at 101 m was obtained from FINO1 offshore research platform. Data gaps larger than one hour were filled by wind speed data at 100 m of the global atmospheric reanalysis ERA5. This procedure is done via the sript '0_input_data/weather/weather_data_processing.py'.


This data, in combination with a power curve for a Haliade X-12MW wind power plant described in the function `calc_power_coef()` of ['flexible_batch_production/generation_data.py'](flexible_batch_production/generation_data.py) is used to calculate a generation profile of a scenario specific wind park with the python module windpowerlib in `get_wind_farm_output()`. 

## Electricity Price
Data in ['0_input_data/price'](0_input_data/price) is taken from Agorameter.de for German Energy market day ahead prices. 

## Steel Plant Data
Technical information about the plant, its equipment and electricity consumption patterns is acquired from Hölling et al. 2021 and Dock et al. 2021 for planning and sizing the equipment. This data is described in the .dat files in the ['0_input_data'](0_input_data) folder. The following table describes all required parameters. 

**Name** | **Domain** | **Description**
---|:---:|---: 
 --- | **Sets** | ---
E | List of Strings | One name for each Steel Making Unit of the modeled industry plant as one plant can have multiple EAFs running at the same time
V | List of Strings | One value for each 'Virtual Equipment' or possible operation model of a Steel Making Unit of the modeled industry plant as an EAF can be operated flexible through changing filling degree, etc. and changing energy consumption
B | List of Strings | All penalties that are considered for weighting load jumps. Minimise load jumps optimisation is currently depreciated 
---|**Parameter**|--- 
minutes_per_step | $\mathbb{N}$ |Amount of minutes which are in one time step of the model
steel_demand | $\mathbb{R_{\gt{0}}}$ |The mass of steel which needs to be produced in one year
netto_power_wind_park | $\mathbb{R_{\gt{0}}}$ | Netto amount of Megawatt in Windpark
**Reduction Unit** |  | 
max_capacity_electrolyser| $\mathbb{R_{\gt{0}}}$ | maximal capacity of electrolyser 
min_consumption_electrolyser | $\mathbb{R_{\gt{0}}}$ | minimum power consumption of reduction unit in Megawatt
efficiency_electrolyser | $\mathbb{R_{\gt{0}}}$ | efficiency of water electrolysis producing hydrogen 
capacity_h2_tank | $\mathbb{R_{\gt{0}}}$ | Maximal capacity of hydrogen tank in MWh
initial_h2_tank_filling | $\mathbb{R_{\geq{0}}}$ | Initial filling of hydrogen tank in regards maximal capacity [%]
DRI_init_content | $\mathbb{R_{\geq{0}}}$ | Initial Content of DRI [tons]
h2_MWh_per_DRI | $\mathbb{R_{\gt{0}}}$ | Consumed quantity of Hydrogen per ton of direct reduced iron in MWh
**Storage** | | 
use_storage_goals  | $\{0,1\}$ | Binary Parameter if storage goals to reach at the end of a model period are given or not
goal_h2_content | $\mathbb{R_{\geq{0}}}$ | Goal of Hydrogen Tank content at end of modelling period
goal_DRI_content | $\mathbb{R_{\geq{0}}}$ | Goal amount of DRI in storage at end of modelling period
**Fuel Cell** | |
fuel_cell_capacity | $\mathbb{R_{\geq{0}}}$ | Maximal power capacity of fuel cell reverting H2 to Electricity in MW
fuel_cell_efficiency | $\mathbb{R_{\geq{0}}}$ | Efficiency of fuel cell reverting hydrogen to Electricity
**Steel Making Unit**| |
batch_load_profile | List of $\mathbb{R_{\geq{0}}}$ for each V | Power load value for each time step in a batch of all virtual equipments $V_u$ of each steel making unit $U$
DRI_demand | $\mathbb{R_{\geq{0}}}$ for each V|  DRI needed for start of one batch in V in tons 
output_steel_products | $\mathbb{R_{\geq{0}}}$ | Output of steel products produced in one batch of each virtual equipment in V
virtual_equipment_duration | $\mathbb{R_{\geq{0}}}$ for each V|  number of timesteps of a batch in virtual equipment. lower than amount of time steps in batch_load_profile profile because of storage usage, which buffers at start load jump and refills at the end 
T_down | $\mathbb{R_{\geq{0}}}$ for each V| Minimum downtime after production of a batch in a steel making unit of U
rolling_mass_efficiency | $\mathbb{R_{\geq{0}}}$ for each V|  Efficiency of mass conversion from steel billets to rolled steel 
rolling_duration | $\mathbb{R_{\geq{0}}}$ for each V|  Number of timesteps it takes to cast and roll produced steel  
rolling_cap  | $\mathbb{R_{\geq{0}}}$ for each V|  Nominal capacity of Rolling Unit in MW
**Grid Connection**| |
draw_power_from_grid | $\{0,1\}$ | Binary parameter rater power can be drawn for grid prices from grid or not
grid_charge_power_price  | $\mathbb{R_{\geq{0}}}$| Grid charge for maximum power consumption from grid as €/MW/month or €/MW/year
grid_charge_energy_price  | $\mathbb{R_{\geq{0}}}$ | Grid charge per energy unit in €/MWh
given_goal_load | $\{0,1\}$ | set to true if objective is stability as then goal load is given in MW
goal_load   | $\mathbb{R_{\geq{0}}}$ | load in MW which to constantly reach in stability objective


# Model

First step is to construct a model in pyomo. ['flexible_batch_production/construct.py'](flexible_batch_production/construct.py) does this in the function `multi_equipment_model()`. This requires all the inputs described above or in further detail in the docstring, and a string describing the objective. Objective options are: 
- 'max_profit'
- 'stability'
- 'min_load_jumps' (not tested)

The constructed model is given as an output and can be optimised with the function [`solve_model()`](flexible_batch_production/solve.py) for ['flexible_batch_production/solve.py'](flexible_batch_production/solve.py). The standard solver is gurobi, if another solver such as cbc is used Parameter Names for reducing the runtime limit have to be adjusted in the function. 

When the optimisation is finished the function passes the solved model as an output. This can be used for further calculation or be saved with the function 'safe_model_results()' into a .csv file. 

For further analysis and visualisation ['flexible_batch_production/analyse.py'](flexible_batch_production/analyse.py) offers several methods. 
1. `model_summary_plot()`: Summary of given time period of plant dynamics
2. `loaded_model_summary_plot()`: Summary of given time period of plant dynamics for model results saved in and loaded from .csv file via `load_model()` method.
3. `sort_model_data()`: Sorts model loaded from .csv file via `load_model()` method according to a given key variable. 
4. `sorted_model_summary_plot()`: Summary of steel plant dynamics in form of a duration curve. 
5. `summary()`: Aggregated results of plant dynamics over the whole model period in Table form. 

## Equation System

### Objectives
#### Maximising Profits
This objective aims for reaching the best economic performance on the participation on the day ahead electricity market and providing stability through offering electricity feed in, in times of high demand and using high amounts of power in times of high electricity availability. The objective combines the profits of selling residual electricity from the wind park for the day ahead market price $M^{sell}_t$ at each time step $t$ and costs of buying electricity from the day ahead market $M^{buy}_t$ if electricity at time step $t$ is not sufficient to produce enough steel  and the scenario allows to draw electricity from the grid.
A important modelling assumption is that neither grid charges nor taxes are included, only the day-ahead market prices are considered. This simplification isolates the effect of price-driven operational flexibility on economic outcomes without the added complexity of regulatory cost structures. Additionally, it is important to highlight that in instances of negative electricity prices, purchasing electricity can result in financial gain, whereas selling excess electricity generates costs, adding a strategic dimension to grid interactions under volatile markets.

$\max \sum\limits_{t\in T} M^{sell}_t - M^{buy}_t % \max M^{LP} + \sum\limits_{t\in T} M^{sell}_t - M^{buy}_t$

### Minimising Deviation from a given Goal Load
In essence this objective pushes the model to smooth the input of electricity from renewable sources into the grid with the help of DR through flexible steel production. Electrolysers, EAF and their accompanying load profiles are operated flexibly in order to balance the fluctuating energy generation profiles from renewables. This is achieved by minimising the mean deviation of actual power exchange from a given load profile. For simplicity the given profile is supposed to be the mean power exchange between grid and steel plant to promote a stable use of the electricity grid. This objectives tries to evaluate the general ability of a steel plant operator to shape the electricity load profile into a prescribed form, which does not necessarily need to be a stable baseload profile but could be any shape. Mean deviation is calculated by the absolute of difference between each value of a vector and its goal value, divided by the number of values in the vector. As a linear optimisation can not calculate absolute values, the deviation from goal load is separated into two variables, one describing the distance above the goal load $D^{above}_t$ and one below the goal load $D^{below}_t$ for each time step $t$. These derived variables are calculated in equation \ref{eq:absolute_split}. Therefore the objective function is represented as:

$\min \quad \frac{\sum\limits_{t\in T} D^{above}_t + D^{below}_t}{T^{end}}$


### Constraints

#### Constraints of Reduction Unit and Hydrogen Storage
##### Maximum load of reduction unit
The reduction unit, especially the water electrolysers (WEL) are consuming varying electricity loads for producing hydrogen over time, represented by the decision variable $L^{WEL}_t$. The maximum power usage is given by a parameter for the installed capacity of the unit $C^{WEL, max}$. In the MILP optimisation problem, power demand of the reduction unit is a semi-continuous variable, as it is either zero or between the range of installed capacity and minimum power $C^{WEL,min}$. As the optimisation tool used for this problem is not able to map semi-continuous variables this is realised through implementing an additional binary decision variable $\Lambda^{WEL}_t$ depicting if the reduction unit is turned on or not.   

$L^{WEL}_t \leq C^{WEL,max} \cdot \Lambda^{WEL}_t \quad \forall t \in T$

##### Minimum load of the reduction unit 
The reduction unit of the plant needs a minimum power which is given by the parameter $C^{WEL,min}$. If the reduction unit is turned off $\Lambda^{WEL}_t$ equals zero as well as the load $L^{WEL}_t$. 

$L^{WEL}_t \geq C^{WEL,min} \cdot \Lambda^{WEL}_t \quad \forall t \in T$

##### Flow of produced hydrogen
Hydrogen produced by the electrolysers can either be directly used for DRI production, or be stored in a tank for later use in reduction or fuel cell. In the process electrolyser loose a certain amount of consumed energy given by parameter $\eta^{WEL}$, whereas the parameter $\Delta t$ is important for the conversion from power in MW to energy in MWh, representing the amount of an hour passed in one time step. Produced hydrogen it is separated by two decision variables in a hydrogen flow directly utilised in DRI production $Q^{H_2 \rightarrow DRI}_{t}$ and one for storage $Q^{H_2 \leftrightarrow tank}_t$. Hydrogen can also flow out of the storage for DRI production in times of low electrolyser utilisation with a negative $Q^{H_2 \leftrightarrow tank}_t$. 

$L^{WEL}_t \cdot \eta^{WEL} \cdot \Delta t = Q^{H_2 \rightarrow DRI}_t + Q^{H_2 \leftrightarrow tank}_t \quad \forall t \in T $

##### Maximum utilisation of reduction unit
The reduction unit has the capacity to process at maximum utilisation the amount of hydrogen which is produced by the electrolysers at max utilisation within one hour. 

$Q^{H_2 \rightarrow DRI}_t \leq C^{WEL, max} \eta^{WEL} \cdot \Delta t \quad \forall t \in T$

##### Content of DRI storage
In the shaft furnace of the reduction unit, hydrogen from electrolysers and possibly hydrogen from storage at time step $t$ $Q^{H_2\rightarrow DRI}_t$ reduces iron ore to iron sponges, or so called direct reduced iron. This DRI is stored in a corresponding storage, which content at time step $t$ is described by $S^{DRI}_t$. The storage is initialised with an amount of DRI already stored, given by the parameter $S^{DRI}_{init}$, which is zero in all scenarios. The reduction process requires $Q^{H_2 \rightarrow DRI}$ units of hydrogen for production of one unit DRI and storing it. This is a given parameter and not to mix up with the time dependent decision variable $Q^{H_2 \rightarrow DRI}_t$. Together with scrap steel, DRI is used in the later process of steel making, this means storage content is reduced by the given parameter for required quantity of DRI $Q^{DRI\rightarrow STM}_{u, v}$ for a starting batch process of steel making virtual equipment $v$ of steel making unit $u$. The binary decision variable $\Lambda^{STM}_{u,v,t}$ describes if steel making virtual equipment was turned on at time step $t$. The content of the DRI storage is constrained and calculated through the following two equations:        

$S^{DRI}_{0} = S^{DRI}_{init} + Q^{H_2\rightarrow DRI}_{0} \cdot Q^{H_2 \rightarrow DRI} - \sum\limits_{u \in U}\sum\limits_{v \in V_u}\Lambda^{STM}_{u,v,0} \cdot Q^{DRI\rightarrow STM}_{u, v}$

$S^{DRI}_{t} = S^{DRI}_{t-1} + Q^{H_2\rightarrow DRI}_{t} \cdot Q^{H_2 \rightarrow DRI} - \sum\limits_{u \in U}\sum\limits_{v \in V_u}\Lambda^{STM}_{u,v,t} \cdot Q^{DRI\rightarrow STM}_{u, v} \quad\forall t \in T \cup t>0$

##### Content of hydrogen storage tank 
The hydrogen tank with the given nominal capacity of $S^{H_2}_t$ is filled at the start of the model with an initial filling share between 0 and 100\% given by the parameter $S^{H_2}_{init}$. The content of the tank is influenced by hydrogen flow $Q^{H_2 \leftrightarrow tank}_t$ adding overproduced hydrogen from electrolysers not directly required for direct reduction, or taking out hydrogen for direct reduction in times of low electrolyser utilisation. Also the fuel cell can reduce the hydrogen tank content by generating electricity $G^{FC}_t$ with an efficiency of $\eta^{FC}$, whereby $G^{FC}_t$ is a decision variable.

$S^{H_2}_0 = C^{S^{H_2}} \cdot S^{H_2}_{init} + Q^{H_2 \leftrightarrow tank}_t - \frac{G^{FC}_t \cdot \Delta t}{\eta^{FC}}\\$

$S^{H_2}_t = S^{H_2}_{t-1} + Q^{H_2 \leftrightarrow tank}_t - \frac{G^{FC}_t \cdot \Delta t}{\eta^{FC}}\quad \forall t \in T\cup t>0 $

##### Range of hydrogen tank content
The content in the hydrogen tank can not surpass the given nominal capacity $C^{H_2}$ or fall below 0.  

$0 \leq S^{H_2}_t \leq C^{S^{H_2}} \quad \forall t \in T$

##### Fuel Cell
The only constraint of the fuel cell power generation $G^{FC}_t$ decision variable is, that it can not surpass its installed capacity $C^{FC}$ at each time step $t$:

$G^{FC}_t \leq C^{FC} \quad \forall t \in T$


#### Constraints of Steel Making Unit
Constraints of Steel Making Unit 

##### Operating one equipment at a time for a given duration
Every steel making unit $u \in U$ in the plant is separated into several virtual equipments. One steel making unit consists of an electric arc furnace, ladle oven and continuous casting equipment. Each virtual equipment $v \in V_u$ represents a capacity utilisation rate, resulting in diverging load profiles and outputs of one production batch. If virtual equipment $v$ is turned on, which is decided by variable $\Lambda^{STM}_{u,v,t}$, it runs for a given duration parameter $\Delta T^{STM}_{u,v}$. For this duration the derived binary variable $\mu^{STM}_{u,v,t}$ has an entry of 1 at the corresponding time steps and $\mu^{STM}_{u,t}$ if any virtual equipment in steel making unit $u$ are running. As long as one equipment is running, every other virtual equipment of the corresponding steel making unit $u$ can not work, therefore:

$\mu^{STM}_{u,v,t} = \sum\limits_{max(0,t-\Delta T^{STM}_{u,v}+1)}^t \Lambda^{STM}_{u,v,t} \quad \forall u,v,t \in U,V_u,T$

$\mu^{STM}_{u,t} = \sum\limits_{v\in V_u} \mu^{STM}_{u,v,t} \quad \forall u, t  \in U,T$

$\mu^{STM}_{u,t} \leq 1  \quad \forall u, t  \in U,T$

##### Constraint of batch starting time\\
The final batch must be initiated at a time step which ensures it and its rolling unit are still completed before the last time step of $T$. 

$t \cdot \Lambda^{STM}_{u,v,t} \leq T^{total} - T^{STM}_{u,v} - T^{ROL}_{u} + 1 \quad \forall u,v,t  \in U,V_u,T$
        
##### Constraint of minimum downtime after batch production
Each steel making unit $u \in U$ has a minimum downtime $T^{pause}_u$ that must elapse after a batch has been produced. After this downtime a next batch in one of the virtual equipment $v \in V$ of the equipment $u$ can be started. This is depicted by the following constraints:

$\Lambda^{STM}_{u,v,t} \cdot T^{pause}_u \leq T^{pause}_u - \sum\limits_{t_1=1}^{min(t, T^{pause}_u)} \mu^{STM}_{u,t-t_1-1} \quad \forall u, v, t \in U,V_u,T$

##### Constraint of steel making unit load
$L^{STM}_{u,t}$ depicts the load profile of steel making unit $u$ at time step $t$. It summarises the load profiles of each virtual equipment $v \in V_u$ and the corresponding batches. The load profile of a single batch in $v$ is given by the parameter $L^{STM}_{u,v,z}$, where $z$ is a time step within a single batch. 

$L^{STM}_{u,t} = \sum\limits_{v\in V_u}\sum\limits_{z = 1}^{min(\Delta T^{STM}_{u,v}, t)} \Lambda^{STM}_{u,v,t-z+1} \cdot L^{STM}_{e,v,z} \quad \forall u,t \in U,T$

##### Content of intermediate steel making products storage \\
When a batch of virtual equipment $v$ of steel making unit $u$ is finished after given $T^{STM}_{u,v}$ time steps a certain amount of steel slabs or billets is produced. This output amount is given in weight by the parameter $O^{STM}_{u,v}$. After a finished batch, this is added to the storage variable of intermediate steel products $S^{STM}_{u,v,t}$. This intermediate products are directly processed further in the rolling unit but in this model the storage content is only reduced when the rolling batch is finished after the duration of a rolling process parameter $T^{ROL}_u$. This leads to a decrease in storage content equivalent to the output created in the batch that initiated the rolling process. This method of modelling intermediate product storage does not accurately reflect the reality of a steel making facility. Rolling is not directly contingent upon steel making operations, and storage is not specific to any unit or virtual equipment as represented in this model. However implementing intermediate steel products as a conversion step between DRI and rolled steel facilitates an interface for incorporation of more realistic models of rolling operations in the future. 

\begin{flalign}
    \begin{split}
    S^{STM}_{u,v,t} = \left\{
        \begin{array}{rrr}
            0 \quad t < T^{STM_{u,v}} \\
            S^{STM}_{u,v,t-1} + \Lambda^{STM}_{u,v,t-T^{STM}_{u,v}} \cdot O^{STM}_{u,v} \quad t < T^{STM_{u,v}}\\
            S^{STM}_{u,v,t-1} + \Lambda^{STM}_{u,v,t-T^{STM}_{u,v}} \cdot O^{STM}_{u,v} - \Lambda^{STM}_{u,v,t-T^{STM}_{u,v}-T^{ROL}_u} \cdot O^{STM}_{u,v} \quad t < T^{STM}_{u,v} + T^{ROL}_u\\
        \end{array}\right. \\ \forall u,v,t \in U, V_u,T
    \end{split}
\end{flalign}

##### Constraints of Rolling Equipment 
After a batch in a virtual equipment $v$ of steel making unit $u$ is finished, produced steel has to be rolled in the final form. In this model rolling happens directly after the steel making and this process is not object of a decision variable but directly dependent on the decision if a virtual equipment was turned on. The process of rolling starts immediately when steel making is done, after $T^{STM}_{u,v}$ time steps. A rolling process takes the amount of $T^{ROL}_u$ parameter time steps. If at time step $t$ a rolling process is running and consuming electricity the derived and binary variable $\mu^{ROL}_{u,t}$ equals one, if it is off it equals 0. Load consumption of the rolling unit is described by derived variable $L^{ROL}_{u,t}$ per time step $t$ and is then constantly consuming the amount of power as the installed capacity. As described above this method of modelling rolling does not accurately reflect the reality of a rolling facility. Rolling is not directly contingent upon steel making operations. For this model however the focus is on reduction and steel making unit. 


$\mu^{ROL}_{u,t} = \sum\limits_{v \in V_u} \sum\limits_{t_1 = T^{STM}_{u,v}}^{min(t, T^{STM}_{u,v}+T^{ROL}_u)} \Lambda^{STM}_{u,v,t - t_1 - 1} \quad \forall u, t \in U,T$

$L^{ROL}_{u, t} = \mu^{ROL}_{u,t} \cdot L^{ROL}_u \quad \forall u, t \in U, T$

##### Constraints of Steel Production
As a rolling unit process is running, finished steel is added to the amount of produced steel of the unit $S^{steel}_{u,t}$. While this process steel intermediate products are lost with an efficiency of $\eta^{ROL}_u$. At the end of the modelled time period sum of produced steel must be larger than a given production goal parameter $m^{total}$. This results in the following two constraints. 

$ S^{steel}_{u,t} = \left\{ 
        \begin{array}{rr}
           0 \quad t=0  \\
           S^{steel}_{u,t-1} + \sum\limits_{v\in V_u} S^{STM}_{u,v,t} \cdot \eta^{ROL}_u / {T^{ROL}_u} \quad t>0
        \end{array}\right. \quad u,t \in U,T$
$m^{total} \leq \sum\limits_{u \in U} S^{steel}_{u, T^{end}}$

#### Constraints of Electrical Power Management

##### Energy Balance  
Electrical power is generated by renewables $G_t$, the fuel cell $G^{FC}_t$ or if the scenario includes this can be drawn from the power grid $P^{buy}_t$. The power is consumed by electrolysers $L^{WEL}_t$, each steel making unit $L^{STM}_{u,t}$ and rolling units $L^{ROL}_{u,t}$. Residual power is fed into the power grid $P^{sell}_t$. All these sum up to zero. 

$0 = G_t + G^{FC}_t + P^{buy}_t - L^{WEL}_t - \sum\limits_{u\in U}(L^{STM}_{u,t} + L^{ROL}_{u,t}) - P^{sell}_t \quad \forall t \in T\\$
    
##### Power Exchange between Grid and Plant 
The power exchange between the plant and the grid $P_t$ is the balance of the decision variable for power bought from grid $P^{buy}_t$ and sold to the grid $P^{sell}_t$ at time step $t$. If power is fed into the grid $P_t$ is positive, if drawn from the grid it is negative. In scenarios where power can not be drawn from the grid, exchange only includes sold power.

$P_t = P^{sell}_t - P^{buy}_t  \quad \forall t \in T$
        
##### Mean of Power Exchange
As the mean of the power exchange serves as the goal load in models using the objective to maximise profits, it is calculated by the following constraint. The calculated value for the profit maximising objective then is used as an externally given parameter goal load in models minimising deviation from goal load.

$\bar P = \frac{ \sum\limits_{t \in T}P_t} {T^{total}}$

$P^{max, buy} \geq P^{buy}_t \quad \forall t \in T$

##### Constraint of splitting power exchange to calculated absolute values
The mean deviation in the objective for fitting power consumption is calculated by the absolute of difference between each value of a vector and its goal value. As a linear optimisation can not calculate absolute values, the power exchange is separated into the values above its mean and below its mean. This means $D^{above}_t$ and $D^{below}_t$ depict the distance between actual power exchange $P_t$ at time step $t$ and the given parameter of goal load $P^{goal}$. Models with the objective to maximise profits, mean of the power exchange calculated in Equation \ref{eq:meanExchange} serves as the goal load. The derived variables are calculated through the following equation: 

$D^{above}_t - D^{below}_t = P_t - P^{goal} \quad \forall t \in T$


#### Constraints of Economics 
##### Electricity Market Profits
Selling electrical energy at the electricity market at time step $t$ yields profit based on the given price profile $p^{€}_t$ per energy unit and the amount of sold electricity $P^{sell}_t$ at time step $t$. The sold energy content is calculated by the electrical power sold $P^{sell}_t$ at time step $t$ an the length of the time step in relation to an hour $\Delta t$. 

$M^{sell}_t = P^{sell}_t \cdot \Delta t \cdot p^{€}_t$
        
##### Electrical Market Costs
Buying electrical energy at the electricity market at time step $t$ cost $p^{€}_t$ per bought energy unit $P^{buy}_t$. 

$ M^{buy}_t = P^{buy}_t \cdot \Delta t \cdot p^{€}_t %\cdot p^{grid,energy}$