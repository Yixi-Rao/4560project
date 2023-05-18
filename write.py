# Project name: Optimisation models to plan energy aggregator business models
# Author: Yixi Rao
# Author uid: u6826541
# Supervisor: Jose Iria

## Description:
# Write the optimization results to a csv file.

# Imports ---------------------------------------------------------------------
import time
import os
import pandas as pd
import numpy as np

def write_cost_outputs(outputs, inputs, data, outputdir):
    '''Write the result of the objective function to CSV file

        Args:
            outputs (OrderedDict): Outputs container
            inputs (OrderedDict): MILP model configuration
            data (OrderedDict): Model information
            outputdir (String):  Output file path
    '''
    client_range = range(inputs["start_client"], inputs["end_client"] + 1)
    # different name for different business models
    obj_name_1   = "wholesale cost" if inputs["Model"] == 1 else "retail cost"
    obj_name_2   = "None" if inputs["Model"] == 1 else "wholesale cost"
    
    with open(f'{os.getcwd()}/output/{outputdir}/COST.csv', 'w') as file:
        # write IDs
        file.write("\nClient id,")
        for cnum in client_range:
            file.write(f'{data["Ids"][cnum]},')    
        file.write("\n")    

        # write Total net cost
        file.write(f'{obj_name_1},')
        for cnum in client_range:
            file.write(f'{outputs["total_net_cost"][cnum]},')
        file.write("\n")
        
        # write energy net cost
        file.write("energy net cost,")
        for cnum in client_range:
            file.write(f'{outputs["energy_net_cost"][cnum]},')
        file.write("\n")
        
        # write FCAS net cost
        file.write("FCAS net cost,")
        for cnum in client_range:
            file.write(f'{outputs["FCAS_net_cost"][cnum]},')
        file.write("\n")
        
        # write wholesale cost
        file.write(f'{obj_name_2},')
        for cnum in client_range:
            file.write(f'{outputs["cost_c"][cnum]},')
        file.write("\n")

def write_var_output_v2(outputs, inputs, data, outputdir):
    '''Write the variable value to CSV file

        Args:
            outputs (OrderedDict): Outputs container
            inputs (OrderedDict): MILP model configuration
            data (OrderedDict): Model information
            outputdir (String):  Output file path
    '''
    client_range = range(inputs["start_client"], inputs["end_client"] + 1)
    file_names = {"E_b":"energy_bids", "L_b":"Lower_FCAS_bids", "R_b":"Raise_FCAS_bids", "L_c":"Lower_c_BESS", "L_d":"Lower_d_BESS", "R_c":"Raise_c_BESS",
                  "R_d":"Raise_d_BESS", "L_pv":"Lower_PV", "R_pv":"Raise_PV", "PV":"PV_generation", "P_c":"charging_BESS", "P_d":"discharging_BESS",
                  "SOC":"state_of_charge", "E_buy":"energy_buy", "E_sell":"energy_sell"}
    
    for dir_index, file_name in file_names.items():
        if np.count_nonzero(outputs[dir_index]) != 0:
            DF = pd.DataFrame({data["Ids"][i] : outputs[dir_index][:, i] for i in client_range})
            DF.insert(0, "Time", data["Time"])
            DF.to_csv(f'{os.getcwd()}/output/{outputdir}/{file_name}.csv', encoding='gbk')
    
def write_var_output(outputs, inputs, data, outputdir):
    '''Write the variable value to CSV file

        Args:
            outputs (OrderedDict): Outputs container
            inputs (OrderedDict): MILP model configuration
            data (OrderedDict): Model information
            outputdir (String):  Output file path
    '''
    client_range = range(inputs["start_client"], inputs["end_client"] + 1)
    # energy and FCAS bid 
    E_bDF = pd.DataFrame({data["Ids"][i] : outputs["E_b"][:, i] for i in client_range})
    E_bDF.insert(0, "Time", data["Time"])
    E_bDF.to_csv(f'{os.getcwd()}/output/{outputdir}/energy_bids.csv', encoding='gbk')
    
    L_bDF = pd.DataFrame({data["Ids"][i] : outputs["L_b"][:, i] for i in client_range})
    L_bDF.insert(0, "Time", data["Time"])
    L_bDF.to_csv(f'{os.getcwd()}/output/{outputdir}/Lower_FCAS_bids.csv', encoding='gbk')

    R_bDF = pd.DataFrame({data["Ids"][i] : outputs["R_b"][:, i] for i in client_range})
    R_bDF.insert(0, "Time", data["Time"])
    R_bDF.to_csv(f'{os.getcwd()}/output/{outputdir}/Raise_FCAS_bids.csv', encoding='gbk')
    
    L_cDF = pd.DataFrame({data["Ids"][i] : outputs["L_c"][:, i] for i in client_range})
    L_cDF.insert(0, "Time", data["Time"])
    L_cDF.to_csv(f'{os.getcwd()}/output/{outputdir}/Lower_c_BESS.csv', encoding='gbk')
    
    L_dDF = pd.DataFrame({data["Ids"][i] : outputs["L_d"][:, i] for i in client_range})
    L_dDF.insert(0, "Time", data["Time"])
    L_dDF.to_csv(f'{os.getcwd()}/output/{outputdir}/Lower_d_BESS.csv', encoding='gbk')
    
    R_cDF = pd.DataFrame({data["Ids"][i] : outputs["R_c"][:, i] for i in client_range})
    R_cDF.insert(0, "Time", data["Time"])
    R_cDF.to_csv(f'{os.getcwd()}/output/{outputdir}/Raise_c_BESS.csv', encoding='gbk')
    
    R_dDF = pd.DataFrame({data["Ids"][i] : outputs["R_d"][:, i] for i in client_range})
    R_dDF.insert(0, "Time", data["Time"])
    R_dDF.to_csv(f'{os.getcwd()}/output/{outputdir}/Raise_d_BESS.csv', encoding='gbk')
    
    # PV generation 
    L_pvDF = pd.DataFrame({data["Ids"][i] : outputs["L_pv"][:, i] for i in client_range})
    L_pvDF.insert(0, "Time", data["Time"])
    L_pvDF.to_csv(f'{os.getcwd()}/output/{outputdir}/Lower_PV.csv', encoding='gbk')
    
    R_pvDF = pd.DataFrame({data["Ids"][i] : outputs["R_pv"][:, i] for i in client_range})
    R_pvDF.insert(0, "Time", data["Time"])
    R_pvDF.to_csv(f'{os.getcwd()}/output/{outputdir}/Raise_PV.csv', encoding='gbk')
    
    PVDF = pd.DataFrame({data["Ids"][i] : outputs["PV"][:, i] for i in client_range})
    PVDF.insert(0, "Time", data["Time"])
    PVDF.to_csv(f'{os.getcwd()}/output/{outputdir}/PV_generation.csv', encoding='gbk')
    
    # BESS charging/discharging
    P_cDF = pd.DataFrame({data["Ids"][i] : outputs["P_c"][:, i] for i in client_range})
    P_cDF.insert(0, "Time", data["Time"])
    P_cDF.to_csv(f'{os.getcwd()}/output/{outputdir}/charging_BESS.csv', encoding='gbk')
    
    P_dDF = pd.DataFrame({data["Ids"][i] : outputs["P_d"][:, i] for i in client_range})
    P_dDF.insert(0, "Time", data["Time"])
    P_dDF.to_csv(f'{os.getcwd()}/output/{outputdir}/discharging_BESS.csv', encoding='gbk')
    
    SOCDF = pd.DataFrame({data["Ids"][i] : outputs["SOC"][:, i] for i in client_range})
    SOCDF.insert(0, "Time", data["Time"])
    SOCDF.to_csv(f'{os.getcwd()}/output/{outputdir}/state_of_charge.csv', encoding='gbk')
    
    E_buyDF = pd.DataFrame({data["Ids"][i] : outputs["E_buy"][:, i] for i in client_range})
    E_buyDF.insert(0, "Time", data["Time"])
    E_buyDF.to_csv(f'{os.getcwd()}/output/{outputdir}/energy_buy.csv', encoding='gbk')
    
    E_sellDF = pd.DataFrame({data["Ids"][i] : outputs["E_sell"][:, i] for i in client_range})
    E_sellDF.insert(0, "Time", data["Time"])
    E_sellDF.to_csv(f'{os.getcwd()}/output/{outputdir}/energy_sell.csv', encoding='gbk')
