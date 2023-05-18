# Project name: Optimisation models to plan energy aggregator business models
# Author: Yixi Rao
# Author uid: u6826541
# Supervisor: Jose Iria

## Description:
# This project proposes to develop a Mixed-Integer Linear Programming (MILP) optimisation framework to optimise DER operations
# and identify their economic benefits in different business models and compute the fee for clients. The aim is to plan and 
# establish new business models for aggregators and clients.
# 
# This framework contains two MILP models:
# - Aggregation Bidding Optimisation Model (ABOM): This model plans energy and capacity bids based on wholesale prices to minimise energy 
#   costs and maximise the FCAS market revenues.
# - Retail Bidding Optimisation Model (RBOM): This model plans energy bids based on tariffs to minimise energy cost.

## Instruction: 
# 1. change the inputs["start_client"] and inputs["end_client"] to change the starting client number and ending client number to specify 
#    the model to run within this clients' number range (avaliable range is [0, 91]).
# 2. change the inputs["FCAS"] to decide whether the aggregator participates in the FCAS market, if it does, please change it to True, 
#    if it only participates in the Energy market, please change it to False.
# 3. inputs["Model"] indicates which model is running, you can choose between ABOM and TBOM
# 4. After you have completed all the configurations, simply run the model.

# Imports ---------------------------------------------------------------------
from read import *
from model import *
from write import *
from collections  import OrderedDict
from time import time
import numpy as np

# inputs ---------------------------------------------------------------------
inputs = OrderedDict() # contain MILP model information

# client index [0, 91]
inputs["start_client"]   = 0                                                 # starting index (includsive)
inputs["end_client"]     = 0                                                 # ending index (includsive)
inputs["number_clients"] = inputs["end_client"] - inputs["start_client"] + 1 # max : 92
inputs["FCAS"]           = True                                             # indicates whether or not to participate in the FCAS market
inputs["Model"]          = "RBOM"                                            # which model to run, "ABOM" or "RBOM"
print(f'#############################################################################################################')
print(f'# The model that is running now is {inputs["Model"]}. Participate in FCAS market? - {inputs["FCAS"]}       ')
print(f'# The range of customers is from {inputs["start_client"]} to {inputs["end_client"] }                       ')
print(f'#############################################################################################################')



## Aggregation Bidding Optimisation Model (ABOM)
if inputs["Model"] == "ABOM":
    #! Read the Indices, sets, and Parameters 
    data    = read_aggregation_business_model("aggregation_model_data/DER.xlsx", "aggregation_model_data/Prices.csv", "aggregation_model_data/Load time_series.csv", "aggregation_model_data/PV time_series.csv")
    outputs = initialisation(inputs, data)
    
    #! Planning optimisation 
    for cnum in range(inputs["start_client"], inputs["end_client"] + 1):
        print(f"::::::::::::::::::::::::::::::: client ID = {cnum} :::::::::::::::::::::::::::::::")
        outputs = Aggregation_Bidding_Optimisation_Model(data, outputs, cnum, saveDetail=True, FCAS=inputs["FCAS"])
        
    #! Print and write the outputs to the folder output/aggregation_business_model/with_FCAS or without_FCAS
    if inputs["FCAS"]:    
        write_cost_outputs(outputs, inputs, data, "aggregation_business_model/with_FCAS")
        write_var_output(outputs, inputs, data, "aggregation_business_model/with_FCAS")
    else:
        write_cost_outputs(outputs, inputs, data, "aggregation_business_model/without_FCAS")
        write_var_output(outputs, inputs, data, "aggregation_business_model/without_FCAS")
    
    print("------------------------------writing done------------------------------")

## Retail Bidding Optimisation Model (RBOM)
elif inputs["Model"] == "RBOM":
    #! Read the Indices, sets, and Parameters 
    data    = read_retail_business_model("retail_model_data/DER.xlsx", "retail_model_data/retail_sell.csv", "retail_model_data/retail_buy.csv", "retail_model_data/Wholesale prices.csv", "retail_model_data/Inflexible load.csv", "retail_model_data/PV.csv")
    outputs = initialisation(inputs, data)
    
    #! Planning optimisation based on four tariffs
    for tnum in range(0, 4):
        for cnum in range(inputs["start_client"], inputs["end_client"] + 1):
            print(f"::::::::::::::::::::::::::::::: client ID = {cnum} with tariff {tnum} :::::::::::::::::::::::::::::::")
            outputs = Retail_Bidding_Optimisation_Model(data, outputs, cnum, tnum, saveDetail=True)
        #! Print and write the outputs to the folder output/retail_business_model/tariff_{tnum}
        write_cost_outputs(outputs, inputs, data, f'retail_business_model/tariff_{tnum}/')
        write_var_output_v2(outputs, inputs, data, f'retail_business_model/tariff_{tnum}/')
        
    print("------------------------------writing done------------------------------")

        