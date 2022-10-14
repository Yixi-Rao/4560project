from pyomo.environ import *
import numpy as np
import pandas as pd
def bidding_model_backup (data, outputs, cnum):
    m = ConcreteModel()
    
    #! indices
    # time intervals
    m.T     = Set(initialize = [t for t in data["T"]])
    m.T_SOC = Set(initialize = [t for t in range(len(data["T"]) + 1)])
    # FCAS markets
    m.W = Set(initialize = [w for w in data["W"]])
    
    #! parameters    
    # inflexible load profile (kW)
    m.P_il = Param(m.T, initialize=data["load"].iloc[:, cnum])
    # PV generation profile (kW)
    m.MPV  = Param(m.T, initialize=data["PV"].iloc[:, cnum])
    # maximum charging power of the BESS (kW)
    MP_C = data["power"]
    # maximum discharging power of the BESS (kW)
    MP_D = data["power"]
    # minimum, maximum state-of-charge of the BESS (kW)
    SOC_min = data["Min_SOC"]
    SOC_max = data["Max_SOC"]
    # energy price ($/kWh)
    m.λ_E = Param(m.T,      initialize=data["energy_price"])
    # raise FCAS price ($/kW) 
    def init_Param_RFCAS(model, t, w):
        return data["R_FCAS_price"][t, w]
    m.λ_R = Param(m.T, m.W, initialize=init_Param_RFCAS)
    # lower FCAS price ($/kW) 
    def init_Param_LFCAS(model, t, w):
        return data["L_FCAS_price"][t, w]
    m.λ_L = Param(m.T, m.W, initialize=init_Param_LFCAS)
    # length of the time interval t (h)
    Δt  = data["Δt"]
    # efficiency of the BESS
    η   = data["eff"]
    
    #! variables
    # energy bids (kW)
    m.E    = Var(m.T,      within=Reals)
    # Lower FCAS bids (kW) 
    m.L    = Var(m.T, m.W, within=Reals)
    # Raise FCAS bids (kW) 
    m.R    = Var(m.T, m.W, within=Reals)
    # Lower capacity provided by BESS (kW)
    m.L_c  = Var(m.T,      within=Reals)
    m.L_d  = Var(m.T,      within=Reals)
    # raise capacity provided by BESS (kW)
    m.R_c  = Var(m.T,      within=Reals)
    m.R_d  = Var(m.T,      within=Reals)
    # Raise/lower capacity provided by PV (kW)
    m.L_pv = Var(m.T,      within=Reals)
    m.R_pv = Var(m.T,      within=Reals)
    # charging/discharging power of the BESS (kW)
    m.P_c  = Var(m.T,      within=Reals)
    m.P_d  = Var(m.T,      within=Reals)
    # PV generation (kW)
    m.PV   = Var(m.T,      within=Reals)
    # state-of-charge (kWh)
    m.SOC  = Var(m.T_SOC,  within=Reals)
    # charging or discharging (0 or 1)
    m.τ    = Var(m.T,      within=Binary)
    print("variables done")
    
    #! objective function
    def obj_rule(m):
        return (summation(m.λ_E, m.E)) * Δt - (summation(m.λ_R, m.R)) * Δt - (summation(m.λ_L, m.L)) * Δt
    m.obj = Objective(rule=obj_rule, sense=minimize)
    print("objective done")
    
    #! constraints
    # Constraint (18) defines the consumption or generation of the prosumer
    def Constraint_18(m, t):
        return m.E[t] == m.P_c[t] - m.P_d[t] + m.P_il[t] - m.PV[t]
    m.constrs18 = Constraint(m.T, rule = Constraint_18)
    
    # Constraints (19) and (20) define the raise and lower capacities traded in each FCAS market
    def Constraint_19_1(m, t, w):
        return m.R[t, w] >= 0
    def Constraint_19_2(m, t, w):
        return m.R[t, w] <= m.R_c[t] + m.R_d[t] + m.R_pv[t]
    m.constrs19_1 = Constraint(m.T, m.W, rule = Constraint_19_1)
    m.constrs19_2 = Constraint(m.T, m.W, rule = Constraint_19_2)
    
    def Constraint_20_1(m, t, w):
        return m.L[t, w] >= 0
    def Constraint_20_2(m, t, w):
        return m.L[t, w] <= m.L_c[t] + m.L_d[t] + m.L_pv[t]
    m.constrs20_1 = Constraint(m.T, m.W, rule = Constraint_20_1)
    m.constrs20_2 = Constraint(m.T, m.W, rule = Constraint_20_2)
    
    # Constraints (24) and (25) set the ranges of the discharging power and charging power
    def Constraint_24_1(m, t):
        return m.P_d[t] >= 0
    def Constraint_24_2(m, t):
        return m.P_d[t] <= (1 - m.τ[t]) * MP_D
    m.constrs24_1 = Constraint(m.T, rule = Constraint_24_1)
    m.constrs24_2 = Constraint(m.T, rule = Constraint_24_2)
    
    def Constraint_25_1(m, t):
        return m.P_c[t] >= 0
    def Constraint_25_2(m, t):
        return m.P_c[t] <= m.τ[t] * MP_C
    m.constrs25_1 = Constraint(m.T, rule = Constraint_25_1)
    m.constrs25_2 = Constraint(m.T, rule = Constraint_25_2)
    
    # Constraints (26) and (27) set the state-of-charge SOC[t+1] of the BESS within its limits
    def Constraint_26(m, t):
        return m.SOC[t + 1] == m.SOC[t] + (m.P_c[t] * η - m.P_d[t] * (1 / η)) * Δt
    m.constrs26 = Constraint(m.T, rule = Constraint_26)
    
    def Constraint_27(m, t):
        return (SOC_min, m.SOC[t + 1], SOC_max)
    m.constrs27 = Constraint(m.T, rule = Constraint_27)
    
    # Constraints (28) and (29) bound the raise capacity
    def Constraint_28_1(m, t):
        return m.R_d[t] >= 0
    def Constraint_28_2(m, t):
        return m.R_d[t] <= MP_D - m.P_d[t]
    m.constrs28_1 = Constraint(m.T, rule = Constraint_28_1)
    m.constrs28_2 = Constraint(m.T, rule = Constraint_28_2)
    
    def Constraint_29_1(m, t):
        return m.R_c[t] >= 0
    def Constraint_29_2(m, t):
        return m.R_c[t] <= m.P_c[t]
    m.constrs29_1 = Constraint(m.T, rule = Constraint_29_1)
    m.constrs29_2 = Constraint(m.T, rule = Constraint_29_2)
    
    # Constraints (30) and (31) bound the lower capacity
    def Constraint_30_1(m, t):
        return m.L_c[t] >= 0
    def Constraint_30_2(m, t):
        return m.L_c[t] <= MP_C - m.P_c[t]
    m.constrs30_1 = Constraint(m.T, rule = Constraint_30_1)
    m.constrs30_2 = Constraint(m.T, rule = Constraint_30_2)
    
    def Constraint_31_1(m, t):
        return m.L_d[t] >= 0
    def Constraint_31_2(m, t):
        return m.L_d[t] <= m.P_d[t]
    m.constrs31_1 = Constraint(m.T, rule = Constraint_31_1)
    m.constrs31_2 = Constraint(m.T, rule = Constraint_31_2)
    
    # Constraints (32) and (33) ensure that the BESS only provides lower and raise capacities, when SOC[t+1] is within its technical limits.
    def Constraint_32(m, t):
        return (m.L_c[t] * η + m.L_d[t] * (1 / η)) * Δt <= SOC_max - m.SOC[t + 1]
    m.constrs32 = Constraint(m.T, rule = Constraint_32)
    
    def Constraint_33(m, t):
        return (m.R_c[t] * η + m.R_d[t] * (1 / η)) * Δt <= m.SOC[t + 1] - SOC_min  
    m.constrs33 = Constraint(m.T, rule = Constraint_33)
    
    # Constraint (34) sets the range of pv generation based on the forecasted solar power
    def Constraint_34(m, t):
        return (0, m.PV[t], m.MPV[t])
    m.constrs34 = Constraint(m.T, rule = Constraint_34)
    
    # Constraint (35) and (36) define the raise and lower capacities of the PV
    def Constraint_35_1(m, t):
        return m.R_pv[t] >= 0
    def Constraint_35_2(m, t):
        return m.R_pv[t] <= m.MPV[t] - m.PV[t]
    m.constrs35_1 = Constraint(m.T, rule = Constraint_35_1)
    m.constrs35_2 = Constraint(m.T, rule = Constraint_35_2)
    
    def Constraint_36_1(m, t):
        return m.L_pv[t] >= 0
    def Constraint_36_2(m, t):
        return m.L_pv[t] <= m.PV[t]
    m.constrs36_1 = Constraint(m.T, rule = Constraint_36_1)
    m.constrs36_2 = Constraint(m.T, rule = Constraint_36_2)
    
    # SOC 
    m.socc = Constraint(expr=m.SOC[0] == 0)
    
    print("Constraint done")

    opt        = SolverFactory('cplex')  # opt = SolverFactory('glpk')
    solution   = opt.solve(m, tee=True)             
    # model_file = m.write('model.lp') 
    print("solution done")
    
    # output TODO output
    
    # Solver
    outputs["time"][cnum]        = solution.Solver.Time
    outputs["bin_vars"][cnum] = len(m.τ)
    outputs["real_vars"][cnum] = solution.Problem.Number_of_variables - outputs["bin_vars"][cnum]
    outputs["constraints"][cnum] = solution.Problem.Number_of_constraints
    
    # Annual costs
    outputs["total_net_cost"][cnum] = value(m.obj)
    outputs["energy_net_cost"][cnum] = (value(summation(m.λ_E, m.E))) * Δt
    outputs["FCAS_net_cost"][cnum] = - (value(summation(m.λ_R, m.R))) * Δt - (value(summation(m.λ_L, m.L))) * Δt
    print("outputs done")
    return outputs

