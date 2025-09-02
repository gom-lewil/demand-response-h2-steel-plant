import pyomo.environ as pyo


def multi_equipment_model(input_dictionary, generation_data, price_data, objective='max_profit'):
    """This function creates a flexible batch production model for an industrial green steel 
    production plent. The steel plant is segregated into three parts: 
        1. reduction unit
        2. steel making 
        3. rolling

    Reduction unit produces direct reduced iron (DRI) by utilising hydrogen from integrated 
    electrolysers. Steel making unit is producing steel by melting iron products in an electric 
    arc furnaces (EAF), refining the molten steel in a ladle oven and casting it into slabs or 
    billets. The rolling unit produces steel end products by rolling the steel.  
    
    This model can integrate multiple steelmaking units, representing especially multiple EAFs.
    One steelmaking unit is called "equipment" due to the modelling approach developed by 
    Liu & Gao, 2022 - doi: 10.1049/gtd2.12559. This approach enables modelling flexible batch 
    production processes in a linear optimisation model. Each equipment can have multiple 
    so called virtual equipments. Each representing an operation mode resulting in another load 
    profile. 


    'input_dictionary': 
        A Dictionary which contains all the information about the equipments in the industrial 
        plant; its operation modes or so called virtual equipments. This includes the following 
        information: 
        ----- Sets -----
            'E':
                Set of all equipments of the modeled steel making unit (e ∈ E)
            'V': 
                Set of virtual versions of an equipment e, due to the different types of raw 
                materials and production modes (v ∈ V_e)
            'P': 
                Set of penalties that are considered for weighting load jumps (p ∈ P)

        ----- Parameters -----
            'minutes_per_step' : used to calculate $Δ t$ by dividing with 60
                Amount of minutes in one time step of given profiles
            'steel_demand': $m^{total}$
                The total mass of steel which needs to be produced [tons]

            -- Reduction Unit --
            'max_capacity_electrolyser' : $C^{WEL, max}$ 
                Maximal power capacity of the electrolysers to produce hydrogen [MW]
            'min_consumption_electrolyser' : $C^{WEL, min}$
                Minimum power capacity utilization of electrolysis [MW]
            'efficiency_electrolyser' : $η^{WEL}$ 
                Efficiency of water electrolysis [%]
            'capacity_h2_tank': $C^{I^{H_2}}$ 
                Storage capacity of hydrogen tank [MWh]
            'initial_h2_tank_filling': $I^{H_2}_0$ 
                Initial storage content level of hydrogen tank [%]
            'h2_MWh_per_DRI' : $Q^{H_2 → DRI}$ 
                Quantity of MWh Hydrogen needed to produce a ton of direct reduced iron [MWh]
                
            -- Fuel Cell --
            'fuel_cell_capacity' : $C^{FC}$
                Nominal power capacity of a fuel cell for reverting hydrogen back to electricity 
                in times of low generation [MW]
            'fuel_cell_efficiency' : $η^{FC}$
                Efficiency of fuel cell [%]

            -- Steelmaking --
            'batch_load_profile': $Q^{electricity -> batch}_{e,v,z}$
                Electricity load profile for each virtual equipment of all equipments as a 
                vector [MW]
            'DRI_demand' : $Q^{DRI → batch}_{e,v}$ 
                DRI in tons used for a batch in vth virtual equipment of eth equipment [tons]
            'output_steel_products': $O^{batch}_{e,v}$
                Output of produced steel products like slabs and billets, in one batch for 
                each virtual equipment [tons]
            virtual_equipment_duration : Δ T^{batch}_{e,v}
                number of timesteps it takes to produce a batch in the corresponding virtual 
                equipment
            'T_down': $Δ T^{pause}_{e}$
                Minimum downtime after production of a batch in an equipment for each equipment
            
            -- Rolling -- 
            'rolling_cap' : $C^{ROL}_e$
                MW nominal capacity of Rolling Unit - one rolling unit per equipment [MW]
            'rolling_mass_efficiency' : η^{ROL}_e
                Efficiency of mass conversion from steel billets to rolled steel per rolling 
                unit [%]
            'rolling_duration' : Δ T^{ROL}_e
                Number of timesteps it takes to roll steel

        ----- Penalties -----
            'boundary_limit'
            'boundary_penalty'

                
    'generation_data': $G_{t}$
        A vector with energy produced by local renewables for each time step in time T
    
    'price_data': A vector with electricty price per time step. Used to calculate profits [€/MWh]

    'objective': 
        String to specify the objective of optimisation. Possible choices: 
            - 'max_profit'
            - 'stability'
            - 'min_load_jumps'
    """
    model = pyo.ConcreteModel()  # Create an empty Concrete Model for the optimization


    """
    ------------------------------------------- Sets -------------------------------------------
    'T' : $T$ 
        All time steps (t ∈ T)
    'E' : $E$ 
        Set of all equipments of the modeled steel making unit (e ∈ E), one equipment aggregates 
        electric arc furnace, ladle oven and continuous casting 
    'V' : $V_e$ 
       All virtual versions of an equipment $e$, due to different types of input materials, or 
       production modes (v ∈ V_e)
    'Z' : $Z_{e,v}$ 
        Time steps within a batch of a virtual equipment v of equipment e (z ∈ Z_e,v)
    'B' : $B$
        Boundaries for calculating penalties when reaching a certain boundary limit
    """

    model.T = pyo.Set(initialize=[_ for _ in range(len(generation_data))], doc='Time steps')
    model.E = pyo.Set(initialize=input_dictionary['E'], doc='Equipments')
    model.V = pyo.Set(
        initialize=[(e, v) for e in input_dictionary['E'] for v in input_dictionary['V'][e]], 
        doc='Virtual equipments',
    )
    Z = {e : {v: [_ for _ in range(len(z))] for v, z in V.items()} 
         for e, V in input_dictionary['batch_load_profile'].items()}
    model.B = pyo.Set(initialize=[b for b in input_dictionary['B']])


    """-------------------------------------- Parameters ---------------------------------------  
        'minutes_per_step' : used to calculate $Δt$ by dividing with 60
            Minutes passing per time step for calculation of energy content in hydrogen storage
        'steel_demand' : $m^{total}$
            Steel demand, which needs to be produced in total time span [tons] 
        'renewable_generation' : $G_t$
            Renewable power generation at time step t [MW]
    """
    model.minutes_per_step = pyo.Param(
        initialize=input_dictionary['minutes_per_step'], 
        doc="Minutes passing per time step"
    )
    
    model.steel_demand = pyo.Param(
        initialize=input_dictionary['steel_demand'], 
        doc='Total Steel demand [tons]'
    )   

    model.renewable_generation = pyo.Param(
        model.T, initialize=generation_data, 
        doc='Renewable power generation at time step t [MW]'
    )
    

    """
    -----  Reduction Unit  -----
        'max_capacity_electrolyser' : $C^{WEL, max}$ 
            Maximal power capacity of the electrolysers to produce hydrogen [MW]
        'min_consumption_electrolyser' : $C^{WEL, min}$
            Minimum power capacity utilization of electrolysis [MW]
        'efficiency_electrolyser' : $η^{WEL}$ 
            Efficiency of water electrolysis
        'nominal_cap_hydrogen_tank': $C^{I^{H_2}}$ 
            Storage capacity of hydrogen tank [MWh]
        'initial_h2_tank_filling': $I^{H_2}_0$ 
            Initial storage content level of hydrogen tank [%]
        'initial_DRI_content' : S^{DRI}_{init}
            Initial amount of DRI in Storage
        'h2_MWh_per_DRI' : $Q^{H_2 rightarrow DRI}$ 
            Quantity of MWh hydrogen needed to produce a ton of direct reduced iron

        Modelling with the goal to reach certain storage content at the end of period
        'use_storage_goals':
            Boolean determining to use production goals for DRI and H2 or not
        'goal_h2_content': 
            Goal of Hydrogen Tank content at end of modelling period
        'goal_DRI_content': 
            Goal amount of DRI in storage at end of modelling period

    """
    model.max_capacity_electrolyser = pyo.Param(
        initialize=input_dictionary['max_capacity_electrolyser'], 
        doc="Maximum power capacity of electrolyser [MW]"
    )

    model.min_consumption_electrolyser = pyo.Param(
        initialize=input_dictionary['min_consumption_electrolyser'], 
        doc="Minimum power capacity of Electrolyser [MW]"
    )

    model.electrolyser_efficiency = pyo.Param(
        initialize=input_dictionary['efficiency_electrolyser'], 
        doc="Efficiency of water electrolysis [%]"
    )

    model.nominal_cap_hydrogen_tank = pyo.Param(
        initialize=input_dictionary['capacity_h2_tank'], 
        doc="Nominal Capacity of Hydrogen Storage [MWh]"
    )

    model.initial_h2_tank_filling = pyo.Param(
        initialize=input_dictionary['initial_h2_tank_filling'], 
        doc="Initial filling of Hydrogen Tank [%]"
    )

    model.initial_DRI_content = pyo.Param(
        initialize=input_dictionary['DRI_init_content'],
        doc='Initial amount of DRI in Storage [tons]'
    )

    model.use_storage_goals = pyo.Param(
        initialize=input_dictionary['use_storage_goals'], 
        doc='Boolean determining to use production goals for DRI and H2 or not')

    if model.use_storage_goals:
        model.goal_h2_content = pyo.Param(
            initialize=input_dictionary['goal_h2_content']
        )
        model.goal_DRI_content = pyo.Param(
            initialize=input_dictionary['goal_DRI_content']
        )

    model.h2_MWh_per_DRI = pyo.Param(
        initialize=input_dictionary['h2_MWh_per_DRI'], 
        doc='Hydrogen per ton of direct reduced iron [MWh]'
    )

    """ 
    -----  Fuel Cell  -----
        'fc_capacity' : $C^{FC}$
            Maximal power capacity of a fuel cell for reverting hydrogen back to electricity 
            in times of low generation [MW]
        'fc_efficiency' : $η^{FC}$
            Efficiency of fuel cell [%]
    """

    model.fc_capacity = pyo.Param(
        initialize=input_dictionary['fuel_cell_capacity'],
        doc='Nominal power capacity of fuel cell [MW]'
    )

    model.fc_efficiency = pyo.Param(
        initialize=input_dictionary['fuel_cell_efficiency'],
        doc='Efficiency of fuel cell [%]'
    )


    """
    -----  Steel making -----
        'batch_load_profile': $L^{STM}_{e,v,z}$
            Electricity load profile for each virtual equipment to make one batch of steel [MW]
        'DRI_demand' : $Q^{DRI → STM}_{e,v}$ 
            DRI in tons used for a batch in vth virtual equipment of eth equipment [tons]
        'output_steel_products': $O^{STM}_{e,v}$
            Output of produced steel products like slabs and billets, in one batch for 
            each steel making virtual equipment [tons]
        virtual_equipment_duration : $T^{STM}_{e,v}$
            number of timesteps it takes to produce a batch in the corresponding steel making 
            virtual equipment 
        'T_pause': $T^{pause}_{e}$
            Minimum downtime after production of a steel making batch in an equipment
    """ 
    def initialize_profiles(model, e, v):  # two parameters due to tuple indexing of the set V
        return input_dictionary['batch_load_profile'][e][v]
    model.batch_load_profile = pyo.Param(
        model.V, 
        initialize=initialize_profiles, 
        doc='Steel making load profiles of one batch in virtual equipment [MW]', 
        domain=pyo.Any
    ) 

    def initialize_DRI_demand(model, e, v):  # two parameters due to tuple indexing of the set V
        return input_dictionary['DRI_demand'][e][v]  
    model.DRI_demand = pyo.Param(
        model.V, 
        initialize=initialize_DRI_demand, 
        doc="DRI demand for a batch [tons]"
        )

    def initialize_output_steel_products(model, e, v):  # two parameters due to tuple indexing 
        return input_dictionary['output_steel_products'][e][v]  # data given by the input file
    model.output_steel_products = pyo.Param(
        model.V, 
        initialize=initialize_output_steel_products, 
        doc='Mass of steel intermediate products produced in one batch in virtual equipment [tons]'
        )
    
    def initialize_virtual_equipment_duration(model, e, v):
        return input_dictionary['virtual_equipment_duration'][e][v]
    model.virtual_equipment_duration = pyo.Param(
        model.V, initialize=initialize_virtual_equipment_duration, doc='Batch duration'
        )

    def initialize_T_pause(model, e): 
        return input_dictionary['T_down'][e]  # data given by the input data file in 'T_down'
    model.T_pause = pyo.Param(
        model.E, initialize=initialize_T_pause, 
        doc='Minimum downtime after production of a batch in equipment e'
        )

    """
    -----  Rolling -----
    'rolling_duration' :  $T^{ROL}_e$
        Number of time steps rolling of equipment e is running
    'rolling_cap' : $C^{ROL}_e$
        Power load which the rolling of equipment e requires if it is running [MW]
    'rolling_mass_efficiency': $η^{ROL}_e$
        Efficiency of mass conversion from steel billets to rolled steel [%]. 
    """

    def initialize_rolling_duration(model, e):
        return input_dictionary['rolling_duration'][e]
    model.rolling_duration = pyo.Param(
        model.E, 
        initialize=initialize_rolling_duration,
        doc='Time duration of a rolling batch of equipment e'
    )
    
    def initialize_rolling_cap(model, e):
        return input_dictionary['rolling_cap'][e]
    model.rolling_cap = pyo.Param(
        model.E, 
        initialize=initialize_rolling_cap,
        doc='Power load which the rolling of equipment e requires if it is running [MW]')
    

    def initialize_rolling_mass_efficiency(model, e):
        return input_dictionary['rolling_mass_efficiency'][e]
    model.rolling_mass_efficiency = pyo.Param(
        model.E, 
        initialize=initialize_rolling_mass_efficiency,
        doc='Mass efficiency of rolling billets to steel [%]'
    ) 

    """
    -----  Penalties -----
    'boundary_limit' : $B^{limit}_b$
        Limit for boundary b 
    'boundary_penalty' : $B^{penalty}_b$
        Penalty to be multiplied with overshoot of boundary limit
    """
    # def initialize_boundary_penalty(model, b):
    #     return input_dictionary['boundary_penalty'][b]
    # model.boundary_penalty = pyo.Param(model.B, initialize=initialize_boundary_penalty, 
    #                                    domain=pyo.Reals)

    # def initialize_boundary_limit(model, b):
    #     return input_dictionary['boundary_limit'][b]
    # model.boundary_limit = pyo.Param(model.B, initialize=initialize_boundary_limit)

    """
    ----- Electricity Market -----
    'electricity_price' : $p^{€}_t$ 
        Price of electricity at time $t$ [€/MWh]
    'draw_power_from_grid': 
        Boolean Variable stating if power can be drawn from grid or not
    'grid_charge_power_price' : $M^{LP}$
        Grid charge for maximum power consumption from grid [€/MW/a]. Only initialized if 
        'draw_power_from_grid' is True
    'grid_charge_energy_price' : $M^{AP}$
        Grid charge per energy unit [€/MWh]. Only initialized if 'draw_power_from_grid' is True
    """
    model.electricity_price = pyo.Param(
        model.T,
        initialize=price_data,
        doc='Price of electricity at time $t$ [€/MWh]'
    )

    model.draw_power_from_grid = pyo.Param(
        domain=pyo.Boolean, 
        initialize=input_dictionary['draw_power_from_grid']
    )
    if model.draw_power_from_grid:
        model.grid_charge_power_price = pyo.Param(
            initialize=input_dictionary['grid_charge_power_price']
        )
        model.grid_charge_energy_price = pyo.Param(
            initialize=input_dictionary['grid_charge_energy_price']
        )

    """
    ----- Electricity Exchange -----
    'given_goal_load' : not included in math model
        If mean exchnage is given as a parameter this boolean parameter is True. This is usually 
        for the objective of stability to minimise caqlculation time. 
    'goal_load' : $bar P$
        Mean power exchange between the plant and the grid over the total time span T [MW] if 
        given as a parameter
    """
    model.given_goal_load = pyo.Param(initialize=input_dictionary['given_goal_load'])

    if model.given_goal_load:
        model.goal_load = pyo.Param(
            initialize=input_dictionary['goal_load']
        )


    """ 
    ---------------------------------------- Variables -----------------------------------------
    -----  Decision Variables  -----
        'equipment_decision_turnon' : $λ^{STM}_{e,v,t}$
            1 if vth virtual equipment of eth steel making equipment at period t is turned on; 
            0 otherwise
        'electrolysers_decision_turnon' : $λ^{WEL}_{e,v,t}$ 
            1 if electrolysis is turned on at time t; 0 otherwise
        'electricity_consumption_electrolysers' : $L^{WEL}_t$
            Load of electrolysis at time t [MW]
        'fc_generation' : $G^{FC}_t$
            Power generation by fuel cell at time t [MW]
        'h2_MWh_for_DRI' : $Q^{H_2 → DRI}_t$
            Quantity of hydrogen used for direct reduction of iron ore at time step t [MWh]
        'h2_MWh_storage_flow' : $Q^{H_2 ↔ tank}_t$
            Quantity of hydrogen flowing in (positive) or out (negative) of the hydrogen storage 
            outflow only for direct reduction, for fuel cell tank outflow is seperated [MWh]
        'power_from_grid' : $P^{from}_t$
            Power drawn from grid at time step t [MW]. Only initialized if 
            'draw_power_from_grid' is True

    """

    model.equipment_decision_turnon = pyo.Var(model.V, model.T, domain=pyo.Binary)
    model.electrolysers_decision_turnon = pyo.Var(model.T, domain=pyo.Binary)
    model.electricity_consumption_electrolysers = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.fc_generation = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.h2_MWh_for_DRI = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.h2_MWh_storage_flow = pyo.Var(model.T, domain=pyo.Reals)
    
    if model.draw_power_from_grid:
        model.power_from_grid = pyo.Var(model.T, domain=pyo.NonNegativeReals)


    """
    -----  Derived Variables  -----
        -- Reduction Unit -- 
        'h2_storage_content' : $I^{H_2}_t$
            Energy content of the hydrogen storage at time t [MWh]
        'DRI_storage_content' : $I^{DRI}_t$
            Mass of direct reduced iron in storage at time step t [tons]
    """
    model.h2_storage_content = pyo.Var(model.T, domain=pyo.NonNegativeReals) 
    model.DRI_storage_content = pyo.Var(model.T, domain=pyo.NonNegativeReals) 

    """
        -- Steel making -- 
        'equipment_load_profile' : $L^{STM}_{e,t}$ 
            Load profile of equipment e at time step t [MW]
        'virtual_eq_running' : $μ^{STM}_{e,v,t}$ 
            Binary variable for running virtual equipment v of equipment e at time t
        'equipment_running' : $μ_{e,t}$
            Binary variable for running equipment e at time t
        'slabs_and_billets_storage' : $I^{STM}_{e,v,t} 
            Storage content of intermediate products produced in steelmaking virtual equipment 
            at time step t [tons]
    """
    model.equipment_load_profile = pyo.Var(model.E, model.T, domain=pyo.NonNegativeReals) 
    model.virtual_eq_running = pyo.Var(model.V, model.T, initialize=0, domain=pyo.Binary)
    model.equipment_running = pyo.Var(model.E, model.T, initialize=0, domain=pyo.Binary)
    model.slabs_and_billets_storage = pyo.Var(model.V, model.T, domain=pyo.NonNegativeReals) 

    """   
        -- Rolling -- 
        'rolling_running' : $μ^{ROL}_{e,t}$
            1 if rolling unit for equipment e is running, 0 if not
        'rolling_load' :  $L^{ROL}_{e,t}$
            Electricity load of the rolling equipment for equipment e at time step t [MW].
        'steel_produced_in_eq' : $I^{steel}_t$
            Total mass of finished rolled steel at time step t [tons]  
    """
    model.rolling_running = pyo.Var(model.E, model.T, domain=pyo.Binary)
    model.rolling_load = pyo.Var(model.E, model.T, domain=pyo.NonNegativeReals) 
    model.steel_produced_in_eq = pyo.Var(model.E, model.T, domain=pyo.NonNegativeReals) 

    """
        -- Power -- 
        'power_exchange' : $P_t$ 
            Amount of electrical power exchange between plant and grid at time t Positive values 
            indicate energy feed in from plant to grid, Negative indicate energy consumption 
            from the grid by the plant [MW]
        'power_to_grid': $P^{to}_t$ 
            Power fed into grid at time step t [MW]
        'dist_power_exchange_above_mean' : P^{above} 
            As a linear optimisation can not calculate absolute values, power exchange is 
            separated into values above its mean and below its mean. This variable depicts the 
            distance between current Power exchange and the mean of power exchange at time t, if
            the exchange is above the mean. If power exchange is below the mean at t, this 
            variable is 0.
        'dist_power_exchange_below_mean' : $P^{below}$
            As a linear optimisation can not calculate absolute values, power exchange is 
            separated into values above its mean and below its mean. This variable depicts the 
            distance between current Power exchange and the mean of power exchange at time t, 
            if the exchange is below the mean. If power exchange is above the mean at t, this 
            variable is 0.   
        'load_jump' : $Δ L_t$
            Depicting the changes in power exchange [MW]
        'load_jump_up' : $Δ L^{up}_t$
            Depicting positive changes in power exchange [MW]
        'load_jump_down' : $Δ L^{down}_t$
            Depicting negative changes in power exchange [MW]
    """
    model.power_exchange = pyo.Var(model.T, domain=pyo.Reals)
    model.power_to_grid = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    if not model.given_goal_load:
        model.mean_power_exchange = pyo.Var(domain=pyo.Reals)
    model.dist_power_exchange_above_mean = pyo.Var(model.T, domain=pyo.NonNegativeReals)  
    model.dist_power_exchange_below_mean = pyo.Var(model.T, domain=pyo.NonNegativeReals) 
    model.load_jump = pyo.Var(model.T, domain=pyo.Reals)
    model.load_jump_up = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.load_jump_down = pyo.Var(model.T, domain=pyo.NonNegativeReals)


    """
        -- Boundary --
        'boundary_overshoot' : $B^{overshoot}_{b,t}$
            Overshoot of load jump at time step t over limit of boundary b, 0 if below limit
    """
    # model.boundary_overshoot = pyo.Var(model.T, model.B, domain=pyo.NonNegativeReals)


    """
        -- Electricity Market -- 
        'electricity_market_profit' : $M^{profit}_t$
            Profits of selling electricity at day ahead market at time step t [€]
        'electricity_market_cost :  $M^{cost}_t$
            Costs of buying electricity at day ahead market at time step t [€]
        'grid_charge_energy' :  $M^{AP}_t$
            Grid charge for buying electricity at day ahead market at time step t [€]
        'grid_charge_power' : $M^{LP}$
            Grid charge for maximum power consumption for whole modeled time period [€]
    """
    model.electricity_market_profit = pyo.Var(model.T, domain=pyo.Reals)
    if model.draw_power_from_grid:
        model.electricity_market_cost = pyo.Var(model.T, domain=pyo.Reals)
        model.grid_charges_power = pyo.Var(domain=pyo.NonNegativeReals)
        model.max_power_from_grid = pyo.Var(domain=pyo.NonNegativeReals)
    

    # ----------------------------------- Objective Function -----------------------------------

    def objective_stability(model):
        """ Equation (1) - Objective function - Stability
        For this system the primary objective is to minimise fluctuations in the electricity 
        exchange between the steel plant and the grid. This is achieved by reducing the mean 
        deviation of actual power exchange from the average power exchange over the given time T
        """
        return sum(model.dist_power_exchange_above_mean[t] + 
                   model.dist_power_exchange_below_mean[t] for t in model.T)/len(model.T)


    def objective_profit(model):
        """ Equation (2) - Objective Function - Price
        The other option which can be optimised in the model is the total profit made from 
        selling electricity to the grid. The price for electricity is given through the 
        parameter $p^{€}_t$, where $P_t * T^{Δ}$ is the exchange of energy at time t 
        between steel plant and grid. 
        """
        if model.draw_power_from_grid:
            return sum(
                model.electricity_market_profit[t]
                - model.electricity_market_cost[t]
                for t in model.T
            ) - model.grid_charges_power
        else: 
            return sum(model.electricity_market_profit[t] for t in model.T)
    

    def objective_minimise_load_jumps(model):
        return sum(model.load_jump_up[t] + model.load_jump_down[t] for t in model.T)


    if objective == 'max_profit':
        model.objective = pyo.Objective(rule=objective_profit, sense=pyo.maximize)
    elif objective == 'min_load_jumps':
        model.objective = pyo.Objective(rule=objective_minimise_load_jumps, sense=pyo.minimize)
    elif objective == 'stability':
        model.objective = pyo.Objective(rule=objective_stability, sense=pyo.minimize)
    else: 
        print("Wrong Objective string was given please select of given objectives in docu")
        return model

    # -------------------------------------- CONSTRAINTS --------------------------------------

    # ----- Reduction Unit and Hydrogen Storage -----

    def constraint_electrolyser_max_consumption(model, t):
        """ Maximum power of reduction unit
        The reduction unit, especially the electrolysers is consuming electricity for producing 
        hydrogen and direct reduction of iron ore. The maximum power usage is given by the 
        installed capacity of the unit 'max_capacity_electrolyser'. In the linear optimisation 
        problem power demand of the reduction unit is a semi-continuous variable, as it is 
        either zero or between the range of installed capacity and minimum power. As pyomo is 
        not able to map semi-continuous variables this is realised through the binary variable 
        'electrolysers_decision_turnon' depicting if the reduction unit is turned on or not"""
        return model.electricity_consumption_electrolysers[t] <= (
            model.max_capacity_electrolyser * model.electrolysers_decision_turnon[t]
        )
    model.constraint_electrolyser_max_consumption = pyo.Constraint(
        model.T, rule=constraint_electrolyser_max_consumption
        )


    def constraint_electrolyser_min_consumption(model, t):
        """ Minimum power of reduction unit
        The reduction unit of the plant needs a minimum power which is given 
        by the parameter 'min_consumption_electrolyser'. In the linear optimisation problem 
        power demand of the reduction unit is a semi-continuous variable, as it is either zero 
        or between the range of installed capacity and minimum power. As pyomo is not able to 
        map semi-continuous variables this is realised through the binary variable 
        'electrolysers_decision_turnon' depicting if the reduction unit is turned on or not."""
        return model.electricity_consumption_electrolysers[t] >= (
            model.min_consumption_electrolyser * model.electrolysers_decision_turnon[t]
            )
    model.constraint_electrolyser_min_consumption = pyo.Constraint(
        model.T, rule=constraint_electrolyser_min_consumption
    )
    

    def constraint_h2_flow(model, t):
        """ Hydrogen Flow 
        Hydrogen produced by the electrolysers can either be directly used for DRI production, 
        or be stored in a tank for later use in reduction or fuel cell. In the production 
        process electrolyser loose a certain amount of energy given by 
        'electrolyser_efficiency'. Hydrogen it is separated in a hydrogen flow for DRI and one 
        for storage.    
        """
        return ( # Produced hydrogen is balanced with
            model.electricity_consumption_electrolysers[t] 
            * model.electrolyser_efficiency 
            * (model.minutes_per_step/60)
                ) == ( # used hydrogen for DRI production and h2 storage flow.
                       # h2_storage_flow is negative if H2 is drawn from storage
                    model.h2_MWh_for_DRI[t] + model.h2_MWh_storage_flow[t]
                    )
    model.constraint_h2_flow = pyo.Constraint(model.T, rule=constraint_h2_flow)


    def constraint_reduction_unit_max_h2_consumption(model, t):
        """Max Reduction Unit Utilisation
        The reduction unit has the capacity to process at maximum utilisation the amount of 
        hydrogen which is produced by the electrolysers at max utilisation. 
        """
        return model.h2_MWh_for_DRI[t] <= (
            model.max_capacity_electrolyser 
            * (model.minutes_per_step / 60) 
            * model.electrolyser_efficiency
        )
    model.constraint_reduction_unit_max_h2_consumption = (
        pyo.Constraint(model.T, rule=constraint_reduction_unit_max_h2_consumption)
    )


    def constraint_DRI_storage_content(model, t):
        """ DRI Storage Content
        In a shaft furnace the produced hydrogen from electrolysers and possibly Hydrogaen from 
        storage reduces iron ore to iron sponges, or so called direct reduced iron (DRI). DRI is
        used in the later process of steelmaking.    
        """
        if t == 0:
            return model.DRI_storage_content[t] == (
                model.initial_DRI_content 
                + model.h2_MWh_for_DRI[t] / model.h2_MWh_per_DRI # + produced DRI at time step t
                # minus DRI demand of a starting batch in vth equipment
                - sum(model.equipment_decision_turnon[e, v, t] 
                      * model.DRI_demand[e, v] for e, v in model.V)
            )
        if t > 0: 
            return model.DRI_storage_content[t] == (
                model.DRI_storage_content[t-1] # DRI at timestep before
                + model.h2_MWh_for_DRI[t] / model.h2_MWh_per_DRI # + produced DRI at time step t
                # minus DRI demand of a starting batch in vth equipment
                - sum(model.equipment_decision_turnon[e, v, t] 
                      * model.DRI_demand[e, v] for e, v in model.V)
            )
    model.constraint_DRI_storage_content = pyo.Constraint(
        model.T, rule=constraint_DRI_storage_content
    )
    

    def constraint_hydrogen_storage_content(model, t):
        """ Hydrogen Storage Tank Content 
        The hydrogen tank with the given nominal capacity of 'nominal_cap_hydrogen_tank' is 
        filled at the start of the model with an initial share given by the parameter 
        'initial_h2_tank_filling'. The content of the tank is increased by addition of hydrogen 
        from the electrolysers or reduced by the hydrogen demand for direct reduction this is 
        modelled through the variable 'h2_MWh_storage_flow'. Additionally storage content can be 
        reduced through fuel cell generating electricity.
        """
        if t == 0:
            return model.h2_storage_content[t] == (
                model.initial_h2_tank_filling * model.nominal_cap_hydrogen_tank 
                + model.h2_MWh_storage_flow[t]
                - (model.fc_generation[t] * (model.minutes_per_step/60)) / model.fc_efficiency
            )
        if t > 0:
            return model.h2_storage_content[t] == (
                model.h2_storage_content[t-1] 
                + model.h2_MWh_storage_flow[t] 
                - (model.fc_generation[t] * (model.minutes_per_step/60)) / model.fc_efficiency
            )
    model.constraint_hydrogen_storage_content = pyo.Constraint(
        model.T, rule=constraint_hydrogen_storage_content
    )


    def constraint_max_hydrogen_storage_content(model, t):
        """ Range of hydrogen tank content
        The content in the hydrogen tank can not surpass the given nominal capacity 
        'nominal_cap_hydrogen_tank' or fall below 0. Falling below zero is prevented by the 
        domain of 'h2_storage_content' - NonNegativeReals
        """
        return model.h2_storage_content[t] <= model.nominal_cap_hydrogen_tank
    model.constraint_max_hydrogen_storage_content = pyo.Constraint(
        model.T, rule=constraint_max_hydrogen_storage_content
        )


    if model.use_storage_goals:
        def constraint_goal_hydrogen_content(model):
            return model.h2_storage_content[len(model.T)-1] >= model.goal_h2_content
        model.constraint_goal_hydrogen_content = pyo.Constraint(
            rule=constraint_goal_hydrogen_content
        )

        def constraint_goal_DRI_content(model):
            return model.DRI_storage_content[len(model.T)-1] >= model.goal_DRI_content
        model.constraint_goal_DRI_content = pyo.Constraint(rule=constraint_goal_DRI_content)


    # ----- Fuel Cell Constraints -----

    def constraint_max_fc_generation(model, t):
        """Constraint Fuel Cell Utilisation
    The only constraint of the fuel cell is, that its generation of electricity at time step t 
    'fc_generation' can not surpass its installed capacity 'fc_capacity'.
    """
        return model.fc_generation[t] <= model.fc_capacity
    model.constraint_max_fc_generation = pyo.Constraint(model.T, 
                                                        rule=constraint_max_fc_generation)



    # ----- Steel Making Constraints -----

    def constraint_virtual_eq_running(model, e, v, t):
        """Operating one equipment at a time for a given duration
        If virtual equipment v is turned on, it runs for a given duration len(Z). For this 
        duration 'virtual_eq_running' has an entry of 1 at the corresponding time steps. 
        """
        return model.virtual_eq_running[e, v, t] == (
            sum(model.equipment_decision_turnon[e, v, t-z] 
                for z in range(model.virtual_equipment_duration[e, v]) 
                if t >= z
                )
        )
    model.constraint_virtual_eq_running = pyo.Constraint(
        model.V, model.T, rule=constraint_virtual_eq_running
        )


    def constraint_equipment_running(model, e, t):
        """Operating one equipment at a time for a given duration
        If equipment e is turned on, it runs for a given duration len(Z). For this duration  
        'equipment_running' has an entry of 1 at the corresponding time steps. 
        """
        return model.equipment_running[e, t] == (
            sum(model.virtual_eq_running[v, t] for v in model.V if e == v[0])
        )
    model.constraint_equipment_running = pyo.Constraint(
        model.E, model.T, rule=constraint_equipment_running
    )


    def constraint_one_veq_running(model, e, t):
        """Operating one equipment at a time for a given duration
        Only one virtual equipment of equipment e can run at a time
        """
        return model.equipment_running[e, t] <= 1
    model.constraint_one_veq_running = pyo.Constraint(
        model.E, model.T, rule=constraint_one_veq_running
    )


    def constraint_starting_time(model, e, v, t):
        """Starting time of equipment
        The final batch must be initiated at a time step which ensures it is still completed 
        before the last time step"""
        return model.equipment_decision_turnon[e, v, t] * t <= (
            len(model.T) 
            - model.virtual_equipment_duration[e, v]
            - model.rolling_duration[e]
        )
    model.constraint_starting_time = pyo.Constraint(
        model.V, model.T, rule=constraint_starting_time
    )


    def constraint_T_pause(model, e, v, t):
        """Minimum downtime after batch production
        Each equipment e ∈ E has a minimum downtime 'T_pause' that must elapse after a batch 
        has been produced. After this downtime a next batch in one of the virtual equipment 
        v ∈ V of the equipment e can be started. This downtime does not need to be completely 
        endured after the last batch at the end of T end.
        """
        return model.equipment_decision_turnon[e, v, t] * model.T_pause[e] <= (
            model.T_pause[e] 
            - sum(model.equipment_running[e, t - t_1 - 1] 
                  for t_1 in range(int(model.T_pause[e])) if t > t_1)
        )
    model.constraint_wait = pyo.Constraint(model.V, model.T, rule=constraint_T_pause)


    def constraint_equipment_load(model, e, t):
        """Constraint of loads
        The variable 'equipment_load_profile' describes the load profile of equipment e over the 
        total time span T. It summarises the load profiles of each virtual equipment v ∈ Ve and 
        the corresponding batches. The load profile of a single batch in v is given by the 
        parameter 'batch_profile[z]', where z is a time step within a single batch.
        """
        e_load = 0  # initialise the load of equipment e at time t
        for v in model.V:  # iterate over all virtual equipments v of equipment e
            if e == v[0]:  # check if the virtual equipment v belongs to the equipment e
                for z in Z[e][v[1]]:  # iterate over all time steps z within a batch of v
                    if t>=z:  # check if index z would run out of range, before the start of T
                        # calculate the load of equipment e at time t
                        e_load += (
                            model.equipment_decision_turnon[v, t-z] 
                            * model.batch_load_profile[v][z] 
                                   )
        return model.equipment_load_profile[e, t] == e_load
    model.constraint_equipment_load = pyo.Constraint(
        model.E, model.T, rule=constraint_equipment_load
    )


    def constraint_slabs_and_billets_storage(model, e, v, t):
        """Constraint of Intermediate steel making Products Storage Content
        When batch of virtual equipment $v$ of steel making unit $u$ is finished after 
        'virtual_equipment_duration' time steps the output weight of steel billets of a batch in 
        of this virtual equipment 'output_steel_products' is added to the storage of 
        intermediate steel products like slabs and billets 'slabs_and_billets_storage'. This 
        intermediate products are directly processed further in the rolling unit but in this 
        model the storage content is only reduced when the rolling batch is finished after the
        duration of a rolling process 'rolling_duration'. This leads to a decrease in storage 
        content equivalent to the output created in the batch that initiated the rolling 
        process. This method of modelling intermediate product storage does not accurately
        reflect the reality of a steel making facility. Rolling is not directly contingent 
        upon steel making operations, and storage is not specific to any unit or virtual 
        equipment as represented in this model. Implementing intermediate steel products as a 
        conversion step between DRI and rolled steel however facilitates the incorporation of 
        more realistic models of rolling operations.
        """
        if t < model.virtual_equipment_duration[e, v]:
            return model.slabs_and_billets_storage[e, v, t] == 0
        elif t < model.virtual_equipment_duration[e,v] + model.rolling_duration[e]:
            return model.slabs_and_billets_storage[e,v,t] == (
                model.slabs_and_billets_storage[e, v, t-1] # storage level at t-1
                # plus - if batch was finished in v its+ duration ago - the produced weight 
                + (
                    model.equipment_decision_turnon[e,v,t - model.virtual_equipment_duration[e,v]]
                    * model.output_steel_products[e, v]
                )
            )
        else:
            return model.slabs_and_billets_storage[e,v,t] == (
                model.slabs_and_billets_storage[e, v, t-1] # tons of already produced billets in veq
                # plus - if batch was finished veq duration ago - the produced weight of billets
                + (
                    model.equipment_decision_turnon[e,v,t - model.virtual_equipment_duration[e,v]]
                    * model.output_steel_products[e, v]
                )
                - ( # after rolling duration intermediate steel products are taken out of  
                    # storage. ToDo: Introduce rolling flexibility, for that the intermediate 
                    # storage must be decoupled from virtual equipments
                    model.equipment_decision_turnon[e, v, 
                                                    t 
                                                    - model.virtual_equipment_duration[e,v]
                                                    - model.rolling_duration[e]
                                                    ]
                    * model.output_steel_products[e, v]
                )
            )
            
    model.constraint_slabs_and_billets_storage = pyo.Constraint(model.V, model.T,
                                                              rule=constraint_slabs_and_billets_storage)
 


    # ----- Rolling Equipment Constraints -----

    def constraint_rolling_running(model, e, t):
        """ Constraint of Rolling Equipment Running
        The process of rolling starts immediately after the process of steel making is done. The 
        process of steel making takes virtual_equipment_duration time steps. After this amount 
        of time a rolling process starts for rolling_duration time steps. If at time step t a 
        rolling process is running and consuming electricity rolling_running equals one, if it
        is off it equals 0. 
        """
        return model.rolling_running[e, t] == sum(  # rolling equipment is on 
            sum(model.equipment_decision_turnon[v, t - t_1 - 1]  # if equipment was turned on
                for t_1 in range(  # between 
                    model.virtual_equipment_duration[v],   # the length of a batch 
                    model.virtual_equipment_duration[v]+model.rolling_duration[e] # and length of batch and rolling duration together
                    ) 
                if t > t_1)  # as long you don't use indexes out of range of the time series
            for v in model.V if e == v[0]
        )
    model.constraint_rolling_running = pyo.Constraint(model.E, model.T, 
                                                      rule=constraint_rolling_running)


    def constraint_rolling_load(model, e, t):
        """ Constraint of Rolling Equipment Load
        After a batch in equipment u is finished the steel produced in has to be cast and 
        rolled in the final form. As this process is required to happen directly after the steel 
        making this process is not object of a decision variable but directly dependent on the 
        decision if equipment u was turned on in the range of '' time steps ago. The 
        demand is equal the given parameter $Q^{ROL}$. As described above this method of 
        modelling rolling does not accurately reflect the reality of a rolling facility. Rolling 
        is not directly contingent upon steel making operations. 
        """
        return model.rolling_load[e, t] == model.rolling_running[e, t] * model.rolling_cap[e]
    model.constraint_rolling_load = pyo.Constraint(model.E, model.T, 
                                                   rule=constraint_rolling_load)

   
    def constraint_steel_produced_in_eq(model, e, t):
        """ Constraints of Steel Production
        Adds continously rolled steel slabs and billets. In the process mass is lost by 
        rolling_mass_efficiency. In this model rolling is not modelled as an independet process,
        but directly dependet on steelmaking. 
        """
        if t == 0: 
            return model.steel_produced_in_eq[e, t] == 0
        else:
            return model.steel_produced_in_eq[e, t] == (
                model.steel_produced_in_eq[e, t-1]
                + sum(model.slabs_and_billets_storage[v, t] / model.rolling_duration[e] 
                      for v in model.V if e == v[0]) 
                * model.rolling_mass_efficiency[e]
            )
    model.constraint_steel_produced_in_eq = pyo.Constraint(model.E, model.T, 
                                                           rule=constraint_steel_produced_in_eq)


    def constraint_meet_steel_demand(model):
        """ Meet steel demand
        The steel demand of the plant needs to be met at the end of the modelling period 
        """
        # sum steel produced in each equipment at last timestep has to be larger that goal
        return sum(model.steel_produced_in_eq[e, len(model.T)-1] for e in model.E) >= model.steel_demand 
    model.constraint_meet_steel_demand = pyo.Constraint(rule=constraint_meet_steel_demand)


    # ----- Energy Management Constraints -----

    def constraint_energy_balance(model, t):
        """Constraints of energy balance 
        Electrical power is generated by renewables 'renewable_generation', the fuel cell 
        'fc_generation' or can be drawn from the power grid 'power_from_grid'. Power is consumed 
        by electrolysers 'electricity_consumption_electrolysers', each steel making unit
        'equipment_load_profile' and rolling units 'rolling_load'. Residual power is fed into 
        the power grid 'power_to_grid'. All these sum up to zero. 
        """
        if model.draw_power_from_grid:
            return 0 == (
                model.renewable_generation[t] 
                + model.fc_generation[t]
                + model.power_from_grid[t]
                - sum(model.equipment_load_profile[e, t] for e in model.E)
                - sum(model.rolling_load[e, t] for e in model.E)
                - model.electricity_consumption_electrolysers[t]
                - model.power_to_grid[t]
            )
        else:
            return 0 == (
                model.renewable_generation[t] 
                + model.fc_generation[t]
                - sum(model.equipment_load_profile[e, t] for e in model.E)
                - sum(model.rolling_load[e, t] for e in model.E)
                - model.electricity_consumption_electrolysers[t]
                - model.power_to_grid[t]
            )
    model.constraint_energy_balance = pyo.Constraint(model.T, rule=constraint_energy_balance)


    def constraint_power_exchange(model, t):
        """ Power Exchange Grid and Plant
        The power exchange between the plant and the grid 'power_exchange' is the balance of 
        power bought from grid and sold to the grid at time step t. Power fed into the grid is 
        positive, drawn from the grid is negative.
        """
        if model.draw_power_from_grid:
            return (
                model.power_exchange[t] == model.power_to_grid[t] - model.power_from_grid[t]
            )
        else: 
            return (
                model.power_exchange[t] == model.power_to_grid[t] 
            )
    model.constraint_power_exchange = pyo.Constraint(model.T, rule=constraint_power_exchange)


    if not model.given_goal_load:
        def constraint_mean_power_exchange(model):
            """ Mean power exchange
            The mean power exchange between the plant and the grid over the total time span T  
            is calculated if it is not given as a parameter with the following equation: 
            """
            return model.mean_power_exchange == sum(model.power_exchange[t] 
                                                    for t in model.T) / len(model.T)
        model.constraint_mean_power_exchange = pyo.Constraint(
            rule=constraint_mean_power_exchange
        )


    def constraint_max_power_from_grid(model, t):
        """ Max of Power drawn from Grid
        The max power from grid over the total time span T is calculated by this:
        """
        return model.max_power_from_grid >= model.power_from_grid[t]
    if model.draw_power_from_grid:
        model.constraint_max_power_from_grid = pyo.Constraint(
            model.T, rule=constraint_max_power_from_grid
        )

   
    def constraint_power_exchange_split(model, t): 
        """ Constraint of splitting power exchange to calculated absolute values
        As a linear optimisation can not calculate absolute values, the power exchange is 
        separated into the values above its mean and below its mean. 
        """
        if model.given_goal_load:
            return (
                model.dist_power_exchange_above_mean[t] - model.dist_power_exchange_below_mean[t]
            ) == (model.power_exchange[t] - model.goal_load)
        else:
            return (
                model.dist_power_exchange_above_mean[t] - model.dist_power_exchange_below_mean[t]
            ) == (model.power_exchange[t] - model.mean_power_exchange)
    model.constraint_power_exchange_split = pyo.Constraint(
        model.T, 
        rule=constraint_power_exchange_split
    )


    # ----- Penalised Load Jumps Constraints -----

    def constraint_load_jump(model, t):
        """ Constraint of Load Jumps
        Changes in the power exchange between plant and grid can be a stress on the grid,
        especially if they are really large in a short amount of time. Therefore the load jumps 
        between two time steps are monitored.        
        """
        if t == 0:
            return model.load_jump[t] == 0
        else: 
            return model.load_jump[t] == model.power_exchange[t-1] - model.power_exchange[t]
    model.constraint_load_jump = pyo.Constraint(model.T, rule=constraint_load_jump)


    def constraint_load_jump_split(model, t):
        """ Load Jump Split
        As the absolute value of load jumps is also required, a split as in the constraint
        above 'constraint_power_exchange_split' is conducted
        """
        return model.load_jump[t] == model.load_jump_up[t] - model.load_jump_down[t]
    model.constraint_load_jump_split = pyo.Constraint(model.T, rule=constraint_load_jump_split)


    # def constraint_boundary_overshoot(model, t, b):
    #      """ Boundary Overshoot
    #     When a load jump at time step $t$ is larger than a given limit 'boundary_limit' of a 
    #     boundary b, 'boundary_overshoot' describes the amount it surpasses the limit.
    #     """
    #      return model.boundary_overshoot[t, b] >= (
    #          (model.load_jump_up[t] + model.load_jump_down[t]) - model.boundary_limit[b]
    #      )
    # model.constraint_boundary_overshoot = pyo.Constraint(
    #     model.T, model.B, rule=constraint_boundary_overshoot
    # )



    # ----- Economics Constraints -----

    def constraint_electricity_market_profit(model, t):
        """ Electricity Market Profits
        Selling electrical energy at the electricity market at time step t yield profit of 
        'electricity_price' per energy unit. The sold energy content is calculated by the 
        electrical power sold 'power_to_grid' at time step t an the length of the time step in 
        relation to an hour. 
        """
        return model.electricity_market_profit[t] == (
            model.power_to_grid[t] * (model.minutes_per_step / 60) * model.electricity_price[t]
        )
    model.constraint_electricity_market_profit = pyo.Constraint(
        model.T, rule=constraint_electricity_market_profit
    )


    def constraint_electricity_market_cost(model, t):
        """ Electricity Market Costs
        Selling electrical energy at the electricity market at time step t yield profit of 
        'electricity_price' per energy unit. In addition to the energy price, an energy grid #
        charge of 'grid_charge_energy_price' has to be paid per bought energy unit as well.
        """
        return model.electricity_market_cost[t] == (
            model.power_from_grid[t] 
            * (model.minutes_per_step / 60) 
            * model.electricity_price[t]
            + model.grid_charge_energy_price
        )
    if model.draw_power_from_grid:
        model.constraint_electricity_market_cost = pyo.Constraint(
            model.T, rule=constraint_electricity_market_cost
        )


    def constraint_grid_charges_power(model):
        """
        Grid Charge Demand Rate In Germany currently grid charges do not only consist of
        a energy rate ”Arbeitspreis” but also a demand rate "Leistungspreis" 
        'grid_charge_power_price for the maximum drawn power 'max_power_from_grid'. 
        This rate is calculated once in a time period
        """
        return model.grid_charges_power == (
            model.max_power_from_grid * model.grid_charge_power_price
        )
    if model.draw_power_from_grid:
        model.constraint_grid_charges_power = pyo.Constraint(
            rule=constraint_grid_charges_power
        )

    return model

