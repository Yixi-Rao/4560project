# Project name: Optimisation models to plan energy aggregator business models
# Author: Yixi Rao
# Author uid: u6826541
# Supervisor: Jose Iria

## Description:
# This project proposes two optimisation frameworks to support aggregators to develop new business models and assess the economic benefits
# of various business models. The frameworks consist of two MILP models:
# 
# - Aggregator Optimisation Model (AOM): This model calculates the wholesale costs of aggregator by optimising DER operations 
#   and bidding in the FCAS markets
# - Retail Optimisation Model (ROM): This model calculates the retail costs of clients by optimising DER operations under different tariffs.

## Instruction: 
# 1. change the inputs["start_client"] and inputs["end_client"] to change the starting client number and ending client number to specify 
#    the model to run within this clients' number range (avaliable range is [0, 91]).
# 2. change the inputs["FCAS"] to decide whether the aggregator participates in the FCAS market, if it does, please change it to True, 
#    if it only participates in the Energy market, please change it to False.
# 3. inputs["Model"] indicates which model is running, you can choose between AOM and ROM
# 4. inputs['saveDetail']: Whether to save variable values.
# 5. After you have completed all the configurations, simply run the model.

# Imports ---------------------------------------------------------------------
from read import *
from model import *
from write import *
from collections  import OrderedDict
from time import time
import numpy as np

# inputs ---------------------------------------------------------------------
inputs = OrderedDict() # Contains MILP model information

# client index [0, 91]
# starting index (includsive)
inputs["start_client"]   = 0
# ending index (includsive)                                              
inputs["end_client"]     = 0
# indicates whether or not to participate in the FCAS market 
inputs["FCAS"]           = False
# which model to run, "AOM" or "ROM"                                              
inputs["Model"]          = "ROM"
# Whether to save variable values                                             
inputs["saveDetail"]     = False                                              
# max : 92                                                 
inputs["number_clients"] = inputs["end_client"] - inputs["start_client"] + 1

print(f'#############################################################################################################')
print(f'# The model that is running now is {inputs["Model"]}.')
print(f'# Participate in FCAS markets? - {inputs["FCAS"]}')
print(f'# Save variable values?        - {inputs["saveDetail"]}')
print(f'# The range of clients is from {inputs["start_client"]} to {inputs["end_client"] }')
print(f'#############################################################################################################')

## Aggregator Optimisation Model (AOM)
if inputs["Model"] == "AOM":
    #! Read the Indices, sets, and Parameters 
    data    = read_aggregator_business_model("aggregator_model_data/DER.xlsx", "aggregator_model_data/Prices.csv", "aggregator_model_data/Load time_series.csv", "aggregator_model_data/PV time_series.csv")
    outputs = initialisation(inputs, data)
    
    #! Planning optimisation 
    for cnum in range(inputs["start_client"], inputs["end_client"] + 1):
        print(f"::::::::::::::::::::::::::::::: client ID = {cnum} :::::::::::::::::::::::::::::::")
        outputs = Aggregator_Optimisation_Model(data, outputs, cnum, saveDetail=inputs["saveDetail"], FCAS=inputs["FCAS"])
        
    #! Print and write the outputs to the folder output/aggregator_business_model/with_FCAS or without_FCAS
    if inputs["FCAS"]:    
        write_cost_outputs(outputs, inputs, data, "aggregator_business_model/with_FCAS")
        if inputs["saveDetail"]:
            write_var_output(outputs, inputs, data, "aggregator_business_model/with_FCAS")
    else:
        write_cost_outputs(outputs, inputs, data, "aggregator_business_model/without_FCAS")
        if inputs["saveDetail"]:
            write_var_output(outputs, inputs, data, "aggregator_business_model/without_FCAS")
    
    print("------------------------------Writing done------------------------------")

## Retail Optimisation Model (ROM)
elif inputs["Model"] == "ROM":
    #! Read the Indices, sets, and Parameters 
    data    = read_retail_business_model("retail_model_data/DER.xlsx", "retail_model_data/retail_sell.csv", "retail_model_data/retail_buy.csv", "retail_model_data/Wholesale prices.csv", "retail_model_data/Inflexible load.csv", "retail_model_data/PV.csv")
    outputs = initialisation(inputs, data)
    
    #! Planning optimisation based on four tariffs
    for tnum in range(0, 1):
        for cnum in range(inputs["start_client"], inputs["end_client"] + 1):
            print(f"::::::::::::::::::::::::::::::: client ID = {cnum} with tariff {tnum} :::::::::::::::::::::::::::::::")
            outputs = Retail_Optimisation_Model(data, outputs, cnum, tnum, saveDetail=inputs["saveDetail"])
        #! Print and write the outputs to the folder output/retail_business_model/tariff_{tnum}
        write_cost_outputs(outputs, inputs, data, f'retail_business_model/tariff_{tnum}/')
        if inputs["saveDetail"]:
            write_var_output_v2(outputs, inputs, data, f'retail_business_model/tariff_{tnum}/')
        
    print("------------------------------Writing done------------------------------")
