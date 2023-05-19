# Project name: Optimisation models to plan energy aggregator business models
# Author: Yixi Rao
# Author uid: u6826541
# Supervisor: Jose Iria

## Description:
# Aggregator Optimisation Model (AOM): This model minimises the annual electricity expenditure and maximises the annual
# FCAS market revenues in the context of using the electricity wholesale market price. It is designed for the DER aggregators, 
# which helps them to explore what is the expenditure of managing the DER for their clients for one year such as importing energy 
# from the electricity wholesale market to meet client's needs and bidding the capacity in FCAS market to earn additional revenues.
#
# Retail Optimisation Model (TOM): In the context of using the TOU tariffs or FR tariffs as the electricity price, 
# this model minimises the annual electricity expenditure for the client or the retailing revenue under the aspect of retailers. 
# This model simulates the case where the aggregator selects the traditional pricing scheme such as tariff structure as their 
# pricing scheme, and optimally manage clients’ demand and DER, to explore what is the possible minimum electricity expenditure
# under the tariff structure. The aggregator's annual wholesale expenditure can be calculated by multiplying energy bids with 
# the corresponding wholesale market prices.

# Imports ---------------------------------------------------------------------
from pyomo.environ import *
import numpy as np
import pandas as pd
from read import *

def Aggregator_Optimisation_Model(data, outputs, cnum, saveDetail=False, FCAS=True):
    '''This model plans energy and capacity bids based on wholesale prices to minimise energy costs and maximise the FCAS market revenues. Objective function is in (1).
        It has the following constraints:
            1. Total energy constraint (2)
            2. Battery energy storage systems constraints (3)-(8)
            3. Frequency Control Ancillary Services constraints (9)-(14)
            4. Photovoltaic systems constraint (15)-(17)

        Args:
            data (OrderedDict): Parameter data of the model
            outputs (OrderedDict): Optimisation outputs container   
            cnum (Int): client number or ID
            saveDetail (bool, optional): Whether to save variable specific data
            FCAS (bool, optional): Whether to participate in FCAS markets

        Returns:
            outputs: Optimisation outputs
    '''
    m = ConcreteModel()
    
    ##! Indices
    lenT    = len(data["T"])
    # Time intervals                             
    m.T     = Set(initialize = [t for t in data["T"]])    
    # Time intervals for SOC   
    m.T_SOC = Set(initialize = [t for t in range(lenT + 1)])
    # FCAS markets' index
    if FCAS:
        m.W = Set(initialize = [w for w in data["W"]])
    
    ##! Parameters    
    # Inflexible load profile (kW)
    m.P_il = Param(m.T, initialize=data["load"].iloc[:, cnum])
    # (Maximum) PV generation profile (kW)
    m.MPV  = Param(m.T, initialize=data["PV"].iloc[:, cnum])
    # Maximum charging power of the BESS (kW)
    MP_C = data["power"]
    # Maximum discharging power of the BESS (kW)
    MP_D = data["power"]
    # Minimum, maximum state-of-charge of the BESS (kW)
    SOC_min = data["Min_SOC"]
    SOC_max = data["Max_SOC"]
    # Energy wholesale prices ($/kWh)
    m.λ_E = Param(m.T,  initialize=data["energy_price"])
    # Duration of time interval t (hour)
    Δt = data["Δt"]
    # Efficiency of the BESS
    η  = data["eff"]
    
    # Parameters related to FCAS markets
    if FCAS:
        # Raise FCAS prices ($/kW) 
        def init_Param_RFCAS(model, t, w):
            return data["R_FCAS_price"][t, w]
        m.λ_R = Param(m.T, m.W, initialize=init_Param_RFCAS)
        # Lower FCAS prices ($/kW) 
        def init_Param_LFCAS(model, t, w):
            return data["L_FCAS_price"][t, w]
        m.λ_L = Param(m.T, m.W, initialize=init_Param_LFCAS)
    print("------------------------------Parameters done----------------------------")
    
    ##! Variables
    # Energy bids (kW)
    m.E   = Var(m.T,     within=Reals)
    # Charging/discharging power of the BESS (kW)
    m.P_c = Var(m.T,     within=Reals, bounds=GE_0_Bound_V2)
    m.P_d = Var(m.T,     within=Reals, bounds=GE_0_Bound_V2)
    # PV generation (kW)
    m.PV  = Var(m.T,     within=Reals, bounds=GE_0_Bound_V2)
    # State-of-charge (kWh)
    m.SOC = Var(m.T_SOC, within=Reals)
    # Charging or discharging (0 or 1)
    m.τ   = Var(m.T,     within=Binary)
    
    # Variables related to FCAS markets
    if FCAS:
        # Lower FCAS bids (kW) 
        m.L    = Var(m.T, m.W, within=Reals, bounds=GE_0_Bound_V1)
        # Raise FCAS bids (kW) 
        m.R    = Var(m.T, m.W, within=Reals, bounds=GE_0_Bound_V1)
        # Lower capacity provided by BESS (kW)
        m.L_c  = Var(m.T,      within=Reals, bounds=GE_0_Bound_V2)
        m.L_d  = Var(m.T,      within=Reals, bounds=GE_0_Bound_V2)
        # Raise capacity provided by BESS (kW)
        m.R_c  = Var(m.T,      within=Reals, bounds=GE_0_Bound_V2)
        m.R_d  = Var(m.T,      within=Reals, bounds=GE_0_Bound_V2)
        # Raise/lower capacity provided by PV (kW)
        m.L_pv = Var(m.T,      within=Reals, bounds=GE_0_Bound_V2)
        m.R_pv = Var(m.T,      within=Reals, bounds=GE_0_Bound_V2)
    print("------------------------------Variables done------------------------------")
    
    ##! Objective function
    def obj_rule(m):
        '''The objective function (1) minimises the annual net-cost of energy transactions in the wholesale market and
            FCAS capacity transactions in FACS market.
        '''
        # If participating in FCAS markets and energy market
        if FCAS:
            return (summation(m.λ_E, m.E)) * Δt - (summation(m.λ_R, m.R)) * Δt - (summation(m.λ_L, m.L)) * Δt
        # If participating in energy market
        else:
            return (summation(m.λ_E, m.E)) * Δt
    m.obj = Objective(rule=obj_rule, sense=minimize)
    print("------------------------------Objective function done---------------------")
    
    ##! Constraints
    # Constraint (2) defines the net energy usage of the client
    def Constraint_2(m, t):
        return m.E[t] == m.P_c[t] - m.P_d[t] + m.P_il[t] - m.PV[t]
    m.constrs2 = Constraint(m.T, rule = Constraint_2)
    
    # Constraints (3)-(4) specify the lower and upper bounds of the BESS's discharging or charging power at time t
    def Constraint_3(m, t):
        return m.P_d[t] <= (1 - m.τ[t]) * MP_D
    m.constrs3 = Constraint(m.T, rule = Constraint_3)
    
    def Constraint_4(m, t):
        return m.P_c[t] <= m.τ[t] * MP_C
    m.constrs4 = Constraint(m.T, rule = Constraint_4)
    
    # Constraint (5)-(6) define the BESS variation at different time step and capacity of the battery
    def Constraint_5(m, t):
        return m.SOC[t + 1] == m.SOC[t] + (m.P_c[t] * η - m.P_d[t] * (1 / η)) * Δt
    m.constrs5 = Constraint(m.T, rule = Constraint_5)
    
    def Constraint_6(m, t):
        return (SOC_min, m.SOC[t + 1], SOC_max)
    m.constrs6 = Constraint(m.T, rule = Constraint_6)
    
    # Constraint (15) sets the range of pv generation based on the forecasted solar power
    def Constraint_15(m, t):
        return (0, m.PV[t], m.MPV[t])
    m.constrs15 = Constraint(m.T, rule = Constraint_15)
    
    # Additional SOC constraint to ensure that SOC is 0 at time step 0
    m.socc = Constraint(expr=m.SOC[0] == 0)
    
    # Constraints related to FCAS markets
    if FCAS:
        #  Constraint (9)-(10) defines total FCAS bids in FCAS raise markets and FCAS lower markets
        def Constraint_9(m, t, w):
            return m.R[t, w] <= m.R_c[t] + m.R_d[t] + m.R_pv[t]
        m.constrs9 = Constraint(m.T, m.W, rule = Constraint_9)
        
        def Constraint_10(m, t, w):
            return m.L[t, w] <= m.L_c[t] + m.L_d[t] + m.L_pv[t]
        m.constrs10 = Constraint(m.T, m.W, rule = Constraint_10)
        
        # Constraint (11)-(12) define the quantity of raise capacity provided by BESS (kW).
        def Constraint_11(m, t):
            return m.R_d[t] <= MP_D - m.P_d[t]
        m.constrs11 = Constraint(m.T, rule = Constraint_11)
        
        def Constraint_12(m, t):
            return m.R_c[t] <= m.P_c[t]
        m.constrs12 = Constraint(m.T, rule = Constraint_12)
        
        # Constraint (13)-(14) defines the quantity of lower capacity provided by BESS (kW).
        def Constraint_13(m, t):
            return m.L_c[t] <= MP_C - m.P_c[t]
        m.constrs13 = Constraint(m.T, rule = Constraint_13)
        
        def Constraint_14(m, t):
            return m.L_d[t] <= m.P_d[t]
        m.constrs14 = Constraint(m.T, rule = Constraint_14)
        
        # Constraint (7)-(8) restrict the state-of-charge within the technical limit of the battery when DER aggregator places the capacity in the FACS markets
        def Constraint_7(m, t):
            return (m.L_c[t] * η + m.L_d[t] * (1 / η)) * Δt <= SOC_max - m.SOC[t + 1]
        m.constrs7 = Constraint(m.T, rule = Constraint_7)
        
        def Constraint_8(m, t):
            return (m.R_c[t] * η + m.R_d[t] * (1 / η)) * Δt <= m.SOC[t + 1] - SOC_min  
        m.constrs8 = Constraint(m.T, rule = Constraint_8)
        
        # Constraint (16)-(17) define the quantity of raise and lower capacity provided by PV (kW).
        def Constraint_16(m, t):
            return m.R_pv[t] <= m.MPV[t] - m.PV[t]
        m.constrs16 = Constraint(m.T, rule = Constraint_16)
        
        def Constraint_17(m, t):
            return m.L_pv[t] <= m.PV[t]
        m.constrs17 = Constraint(m.T, rule = Constraint_17)       
    print("------------------------------Constraints done----------------------------")

    ##! Solver 
    opt      = SolverFactory('cplex')  # or opt = SolverFactory('glpk')
    solution = opt.solve(m, tee=False)               
    print("------------------------------Solution done------------------------------")
    
    ##! Output 
    # Solver output
    outputs["time"][cnum]        = solution.Solver.Time
    outputs["bin_vars"][cnum]    = len(m.τ)
    outputs["real_vars"][cnum]   = solution.Problem.Number_of_variables - outputs["bin_vars"][cnum]
    outputs["constraints"][cnum] = solution.Problem.Number_of_constraints
    print(solution.solver.termination_condition) 
    print(solution.solver.termination_message) 
    print(solution.solver.status)
    
    # Annual costs for client cnum
    outputs["total_net_cost"][cnum]  = value(m.obj)
    outputs["energy_net_cost"][cnum] = (value(summation(m.λ_E, m.E))) * Δt
    outputs["FCAS_net_cost"][cnum]   = outputs["total_net_cost"][cnum] - outputs["energy_net_cost"][cnum]
    print("Annual cost output done") 
    
    # Whether to save variable specific data
    if saveDetail:
        # Energy bid
        outputs["E_b"][:, cnum] = np.array([value(m.E[t]) for t in data["T"]])
        if FCAS:
            # FCAS bid
            outputs["L_b"][:, cnum] = ["-".join([str(value(m.L[t, w])) for w in data["W"]]) for t in data["T"]]
            outputs["R_b"][:, cnum] = ["-".join([str(value(m.R[t, w])) for w in data["W"]]) for t in data["T"]]
            # FCAS bid related to BESS
            outputs["L_c"][:, cnum] = np.array([value(m.L_c[t]) for t in data["T"]])
            outputs["L_d"][:, cnum] = np.array([value(m.L_d[t]) for t in data["T"]])
            outputs["R_c"][:, cnum] = np.array([value(m.R_c[t]) for t in data["T"]])
            outputs["R_d"][:, cnum] = np.array([value(m.R_d[t]) for t in data["T"]])
        print("energy and FCAS bid output done")
        
        # BESS charging/discharging
        outputs["P_c"][:, cnum] = np.array([value(m.P_c[t]) for t in data["T"]])
        outputs["P_d"][:, cnum] = np.array([value(m.P_d[t]) for t in data["T"]])
        outputs["SOC"][:, cnum] = np.array([value(m.SOC[t]) for t in range(lenT + 1)])
        print("BESS charging/discharging output done")
        
        # PV generation
        outputs["PV"][:, cnum] = np.array([value(m.PV[t]) for t in data["T"]])
        if FCAS:
            # FCAS bid related to PV
            outputs["L_pv"][:, cnum] = np.array([value(m.L_pv[t]) for t in data["T"]])
            outputs["R_pv"][:, cnum] = np.array([value(m.R_pv[t]) for t in data["T"]])
        print("PV generation output done") 
    print("-----------------------------Outputs done--------------------------------")
    
    return outputs

def Retail_Optimisation_Model(data, outputs, cnum, tnum, saveDetail=False):
    '''This model plans energy bids based on tariffs to minimise energy cost. Objective function is in (18).
        It has the following constraints:
            1. Energy constraints (19)-(21)
            2. Battery energy storage systems constraints (22)-(25)
            3. Photovoltaic systems constraint (26)

        Args:
            data (OrderedDict): Parameter data of the model
            outputs (OrderedDict): Optimisation outputs container   
            cnum (Int): client number or ID
            tnum (Int): The tariff used in this model
            saveDetail (bool, optional): Whether to save variable specific data

        Returns:
            outputs: Optimisation outputs
    '''
    m = ConcreteModel()
    
    ##! Indices
    lenT    = len(data["T"])
    # Time intervals
    m.T     = Set(initialize = [t for t in data["T"]])
    # Time intervals for SOC 
    m.T_SOC = Set(initialize = [t for t in range(lenT + 1)])
    
    ##! Parameters   
    # Inflexible load profile (kW)
    m.P_il = Param(m.T, initialize=data["load"].iloc[:, cnum])
    # PV generation profile (kW)
    m.MPV  = Param(m.T, initialize=data["PV"].iloc[:, cnum])
    # Maximum charging power of the BESS (kW) 
    MP_C = data["power"][cnum]
    # Maximum discharging power of the BESS (kW) 
    MP_D = data["power"][cnum]
    # Minimum, maximum state-of-charge of the BESS (kW)
    SOC_min = data["Min_SOC"]
    SOC_max = data["Max_SOC"][cnum]
    # Tariff: buy price ($/kWh)
    m.λ_TB = Param(m.T, initialize=data["tariff_buy"][str(tnum)])
    # Tariff: sell price ($/kWh)
    λ_TS   = data["tariff_sell"][str(tnum)] 
    # Wholesale price ($/kWh)
    m.λ_E  = Param(m.T, initialize=data["energy_price"])
    
    # Length of the time interval t (h)
    Δt = data["Δt"]
    # Efficiency of the BESS
    η  = data["eff"][cnum]
    print("------------------------------Parameters done----------------------------")
    
    ##! Variables
    # Energy bids (kW)
    m.E   = Var(m.T,     within=Reals)
    # Charging/discharging power of the BESS (kW)
    m.P_c = Var(m.T,     within=Reals, bounds=GE_0_Bound_V2)
    m.P_d = Var(m.T,     within=Reals, bounds=GE_0_Bound_V2)
    # PV generation (kW)
    m.PV  = Var(m.T,     within=Reals)
    # State-of-charge (kWh)
    m.SOC = Var(m.T_SOC, within=Reals)
    # Charging or discharging (0 or 1)
    m.τ   = Var(m.T,     within=Binary)
    # Energy bought and energy sold (kw)
    m.E_b = Var(m.T,     within=Reals, bounds=GE_0_Bound_V2)
    m.E_s = Var(m.T,     within=Reals, bounds=GE_0_Bound_V2)  
    print("------------------------------Variables done-----------------------------")
    
    ##! Objective function
    def obj_rule(m):
        '''The objective function (18) minimises the net-cost of trading energy through TOU tariffs or FR tariffs.
        '''
        return (sum(-1 * λ_TS * m.E_s[t] + m.λ_TB[t] * m.E_b[t] for t in data["T"])) * Δt
    m.obj = Objective(rule=obj_rule, sense=minimize)
    print("------------------------------Objective function done--------------------")
    
    #! Constraints
    # Constraint (19) defines the consumption or generation of the prosumer
    def Constraint_19(m, t):
        return m.E[t] == m.P_c[t] - m.P_d[t] + m.P_il[t] - m.PV[t]
    m.constrs19 = Constraint(m.T, rule = Constraint_19)
    
    # Constraint (20) connect the energy bought and energy sold to the total energy consumption.
    def Constraint_20(m, t):
        return m.E[t] == m.E_b[t] - m.E_s[t]
    m.constrs20 = Constraint(m.T, rule = Constraint_20)
    
    # Constraints (22) and (23) set the ranges of the discharging power and charging power
    def Constraint_22(m, t):
        return m.P_d[t] <= (1 - m.τ[t]) * MP_D
    m.constrs22 = Constraint(m.T, rule = Constraint_22)
    
    def Constraint_23(m, t):
        return m.P_c[t] <= m.τ[t] * MP_C
    m.constrs23 = Constraint(m.T, rule = Constraint_23)
    
    # Constraints (24) and (25) set the state-of-charge SOC[t+1] of the BESS within its limits
    def Constraint_24(m, t):
        return m.SOC[t + 1] == m.SOC[t] + (m.P_c[t] * η - m.P_d[t] * (1 / η)) * Δt
    m.constrs24 = Constraint(m.T, rule = Constraint_24)
    
    def Constraint_25(m, t):
        return (SOC_min, m.SOC[t + 1], SOC_max)
    m.constrs25 = Constraint(m.T, rule = Constraint_25)
    
    # Constraint (26) sets the range of pv generation based on the forecasted solar power.
    def Constraint_26(m, t):
        return (0, m.PV[t], m.MPV[t])
    m.constrs26 = Constraint(m.T, rule = Constraint_26)
    
    # Additional SOC constraint to ensure that SOC is 0 at time step 0.
    m.socc = Constraint(expr=m.SOC[0] == 0) 
    print("------------------------------Constraints done---------------------------")

    ##! Solver 
    opt      = SolverFactory('cplex')  # or opt = SolverFactory('glpk')
    solution = opt.solve(m, tee=False)             
    print("------------------------------Solution done------------------------------")
    
    ##! Output 
    print(solution.solver.termination_condition) 
    print(solution.solver.termination_message) 
    print(solution.solver.status)
    
    # Annual costs for client cnum under tariff tnum
    outputs["total_net_cost"][cnum] = value(m.obj)
    outputs["cost_c"][cnum]         = value(summation(m.λ_E, m.E)) * Δt # wholesale cost
    print(f'Retail cost: {outputs["total_net_cost"][cnum]}, wholesale cost: {outputs["cost_c"][cnum]}')
    print("Annual cost output done") 
    
    # Whether to save variable specific data
    if saveDetail:
        # Energy bid
        outputs["E_b"][:, cnum]    = np.array([value(m.E[t]) for t in data["T"]])
        # Energy bought
        outputs["E_buy"][:, cnum]  = np.array([value(m.E_b[t]) for t in data["T"]])
        # Energy bought
        outputs["E_sell"][:, cnum] = np.array([value(m.E_s[t]) for t in data["T"]])
        print("energy bid output done")
        
        # BESS charging/discharging and SOC
        outputs["P_c"][:, cnum] = np.array([value(m.P_c[t]) for t in data["T"]])
        outputs["P_d"][:, cnum] = np.array([value(m.P_d[t]) for t in data["T"]])
        outputs["SOC"][:, cnum] = np.array([value(m.SOC[t]) for t in range(lenT + 1)])
        print("BESS charging/discharging output done")
        
        # PV generation
        outputs["PV"][:, cnum] = np.array([value(m.PV[t]) for t in data["T"]])
        print("PV generation output done") 
    print("------------------------------Outputs done------------------------------")
    
    return outputs

def GE_0_Bound_V1(model, i, j):
    '''Ancillary function to define x_i_j > 0
    '''
    return (0, None)
    
def GE_0_Bound_V2(model, i):
    '''Ancillary function to define x_i > 0
    '''
    return (0, None)