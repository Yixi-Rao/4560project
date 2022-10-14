import time
import os
import pandas as pd

def write_cost_outputs(outputs, inputs, data):
    client_range = range(inputs["start_client"], inputs["end_client"] + 1)
    with open(f'{os.getcwd()}/output/COST.csv', 'w') as file:
        file.write("\nClient id,")
        for cnum in client_range:
            file.write(f'{data["Ids"][cnum]},')    
        file.write("\n")    

        file.write("Total net cost,")
        for cnum in client_range:
            file.write(f'{outputs["total_net_cost"][cnum]},')
        file.write("\n")
        
        file.write("energy net cost,")
        for cnum in client_range:
            file.write(f'{outputs["energy_net_cost"][cnum]},')
        file.write("\n")
        
        file.write("FCAS net cost,")
        for cnum in client_range:
            file.write(f'{outputs["FCAS_net_cost"][cnum]},')
        file.write("\n")

def write_var_output(outputs, inputs, data):
    client_range = range(inputs["start_client"], inputs["end_client"] + 1)
    # energy and FCAS bid 
    E_bDF = pd.DataFrame({data["Ids"][i] : outputs["E_b"][:, i] for i in client_range})
    E_bDF.insert(0, "Time", data["Time"])
    E_bDF.to_csv(f'{os.getcwd()}/output/energy_bids.csv', encoding='gbk')
    
    L_bDF = pd.DataFrame({data["Ids"][i] : outputs["L_b"][:, i] for i in client_range})
    L_bDF.insert(0, "Time", data["Time"])
    L_bDF.to_csv(f'{os.getcwd()}/output/Lower_FCAS_bids.csv', encoding='gbk')

    R_bDF = pd.DataFrame({data["Ids"][i] : outputs["R_b"][:, i] for i in client_range})
    R_bDF.insert(0, "Time", data["Time"])
    R_bDF.to_csv(f'{os.getcwd()}/output/Raise_FCAS_bids.csv', encoding='gbk')
    
    L_cDF = pd.DataFrame({data["Ids"][i] : outputs["L_c"][:, i] for i in client_range})
    L_cDF.insert(0, "Time", data["Time"])
    L_cDF.to_csv(f'{os.getcwd()}/output/Lower_c_BESS.csv', encoding='gbk')
    
    L_dDF = pd.DataFrame({data["Ids"][i] : outputs["L_d"][:, i] for i in client_range})
    L_dDF.insert(0, "Time", data["Time"])
    L_dDF.to_csv(f'{os.getcwd()}/output/Lower_d_BESS.csv', encoding='gbk')
    
    R_cDF = pd.DataFrame({data["Ids"][i] : outputs["R_c"][:, i] for i in client_range})
    R_cDF.insert(0, "Time", data["Time"])
    R_cDF.to_csv(f'{os.getcwd()}/output/Raise_c_BESS.csv', encoding='gbk')
    
    R_dDF = pd.DataFrame({data["Ids"][i] : outputs["R_d"][:, i] for i in client_range})
    R_dDF.insert(0, "Time", data["Time"])
    R_dDF.to_csv(f'{os.getcwd()}/output/Raise_d_BESS.csv', encoding='gbk')
    
    # PV generation 
    L_pvDF = pd.DataFrame({data["Ids"][i] : outputs["L_pv"][:, i] for i in client_range})
    L_pvDF.insert(0, "Time", data["Time"])
    L_pvDF.to_csv(f'{os.getcwd()}/output/Lower_PV.csv', encoding='gbk')
    
    R_pvDF = pd.DataFrame({data["Ids"][i] : outputs["R_pv"][:, i] for i in client_range})
    R_pvDF.insert(0, "Time", data["Time"])
    R_pvDF.to_csv(f'{os.getcwd()}/output/Raise_PV.csv', encoding='gbk')
    
    PVDF = pd.DataFrame({data["Ids"][i] : outputs["PV"][:, i] for i in client_range})
    PVDF.insert(0, "Time", data["Time"])
    PVDF.to_csv(f'{os.getcwd()}/output/PV_generation.csv', encoding='gbk')
    
    # BESS charging/discharging
    P_cDF = pd.DataFrame({data["Ids"][i] : outputs["P_c"][:, i] for i in client_range})
    P_cDF.insert(0, "Time", data["Time"])
    P_cDF.to_csv(f'{os.getcwd()}/output/charging_BESS.csv', encoding='gbk')
    
    P_dDF = pd.DataFrame({data["Ids"][i] : outputs["P_d"][:, i] for i in client_range})
    P_dDF.insert(0, "Time", data["Time"])
    P_dDF.to_csv(f'{os.getcwd()}/output/discharging_BESS.csv', encoding='gbk')
    
    SOCDF = pd.DataFrame({data["Ids"][i] : outputs["SOC"][:, i] for i in client_range})
    SOCDF.insert(0, "Time", data["Time"])
    SOCDF.to_csv(f'{os.getcwd()}/output/state_of_charge.csv', encoding='gbk')
    