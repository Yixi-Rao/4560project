from read import *
from model import *
from write import *
from collections  import OrderedDict
from time import time
import numpy as np

# inputs ---------------------------------------------------
inputs = OrderedDict()

inputs["start_client"]   = 0
inputs["end_client"]     = 45
inputs["number_clients"] = inputs["end_client"] - inputs["start_client"] + 1 # max : 93
inputs["FCAS"]           = True
inputs["Model"]          = 0 #0,1


if inputs["Model"] == 0:
    # Read -----------------------------------------------------
    data = read_model_1("DER.xlsx", "Prices.csv", "Load time_series.csv", "PV time_series.csv")
    outputs = initialization(inputs, data)
    # Optimization ---------------------------------------------
    for cnum in range(inputs["start_client"], inputs["end_client"] + 1):
        print(f"::::::::::::::::::::::::: client ID = {cnum} :::::::::::::::::::::::::")
        outputs = bidding_model(data, outputs, cnum)
    # Print ---------------------------------------------    
    write_cost_outputs(outputs, inputs, data)
    write_var_output(outputs, inputs, data)
    print("------------------------------writing done------------------------------")
    
elif inputs["Model"] == 1:
    data = read_model_2("Clients/DER.xlsx", "Clients/Export.csv", "Clients/Import.csv", "Clients/Wholesale prices.csv", "Clients/Inflexible load.csv", "Clients/PV.csv")
    outputs = initialization(inputs, data)
    for cnum in range(inputs["start_client"], inputs["end_client"] + 1):
        print(f"::::::::::::::::::::::::: client ID = {cnum} :::::::::::::::::::::::::")
        outputs = bidding_model(data, outputs, cnum)

        