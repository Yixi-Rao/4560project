import numpy as np
import pandas as pd
from collections import OrderedDict
import os

# -------------------------------------------------model 1-------------------------------------------------
def read_model_1(DERFile, PriceFile, LoadFile, PVFile):
    data = OrderedDict()
    readSameBESS(DERFile, data)
    readMarginPrice(PriceFile, data)
    readLoad(LoadFile, data)
    readPV(PVFile, data)
    readSetting(data)
    
    return data

def readSameBESS(DERFile, data):
    df_Battery = pd.read_excel(f'{os.getcwd()}/data/{DERFile}', sheet_name="Battery")
    df_PVID    = pd.read_excel(f'{os.getcwd()}/data/{DERFile}', sheet_name="PV")
    data["Ids"]     = df_PVID.columns.values
    data["power"]   = df_Battery["power"].item()
    data["Max_SOC"] = df_Battery["energy"].item()
    data["Min_SOC"] = 0
    data["eff"]     = df_Battery["eff"].item()
    
def readMarginPrice(PriceFile, data):
    df_Prices = pd.read_csv(f'{os.getcwd()}/data/{PriceFile}', na_values=["  "])
    data["Time"]         = df_Prices["Time"]
    data["energy_price"] = df_Prices["ENERGY"].apply(lambda x: x / 1000).iloc[:105120]
    tmp_R_FCAS = []
    tmp_L_FCAS = []
    for i in ["RAISE6S", "RAISE60S", "RAISE5MIN"]:
        tmp_R_FCAS.append(df_Prices[i].apply(lambda x: x / 1000).iloc[:105120])
        
    for i in ["LOWER6S", "LOWER60S", "LOWER5MIN"]:
        tmp_L_FCAS.append(df_Prices[i].apply(lambda x: x / 1000).iloc[:105120])

    data["R_FCAS_price"] = pd.concat(tmp_R_FCAS, axis=1).to_numpy()
    data["L_FCAS_price"] = pd.concat(tmp_L_FCAS, axis=1).to_numpy()

# -------------------------------------------------model 2-------------------------------------------------
def read_model_2(DERFile, tariffSellFile, tariffBuyFile, WholesalePriceFile, LoadFile, PVFile):
    data = OrderedDict()
    readDiffBESS(DERFile, data)
    readTariff(tariffSellFile, tariffBuyFile, data)
    readWholesalePrice(WholesalePriceFile, data)
    readLoad(LoadFile, data)
    readPV(PVFile, data)
    readSetting(data)
    
    return data

def readDiffBESS(DERFile, data):
    df_Battery = pd.read_excel(f'{os.getcwd()}/data/{DERFile}', sheet_name="Battery")
    data["Ids"]     = df_Battery.columns.values
    data["power"]   = df_Battery.iloc[1, :].to_numpy(dtype = "float")
    data["Max_SOC"] = df_Battery.iloc[0, :].to_numpy(dtype = "float")
    data["Min_SOC"] = 0
    data["eff"]     = df_Battery.iloc[2, :].to_numpy(dtype = "float")

def readTariff(tariffSellFile, tariffBuyFile, data):
    df_BuyPrices = pd.read_csv(f'{os.getcwd()}/data/{tariffBuyFile}', na_values=["  "])
    df_SellPrices  = pd.read_csv(f'{os.getcwd()}/data/{tariffSellFile}')
    data["Time"]        = df_BuyPrices["Time"]
    data["tariff_buy"]  = {"0" : df_BuyPrices.iloc[:, 1],
                           "1" : df_BuyPrices.iloc[:, 2],
                           "2" : df_BuyPrices.iloc[:, 3],
                           "3" : df_BuyPrices.iloc[:, 4]}
    data["tariff_sell"] = {"0" : df_SellPrices.iloc[:, 0].item(),
                           "1" : df_SellPrices.iloc[:, 1].item(),
                           "2" : df_SellPrices.iloc[:, 2].item(),
                           "3" : df_SellPrices.iloc[:, 3].item()}
    
def readWholesalePrice(WholesalePriceFile, data):
    df_WSPrice = pd.read_csv(f'{os.getcwd()}/data/{WholesalePriceFile}')
    data["energy_price"] = df_WSPrice["ENERGY"].iloc[:105120]
    
    tmp_R_FCAS = []
    tmp_L_FCAS = []
    for i in ["RAISE6S", "RAISE60S", "RAISE5MIN"]:
        tmp_R_FCAS.append(df_WSPrice[i].iloc[:105120])
        
    for i in ["LOWER6S", "LOWER60S", "LOWER5MIN"]:
        tmp_L_FCAS.append(df_WSPrice[i].iloc[:105120])

    data["R_FCAS_price"] = pd.concat(tmp_R_FCAS, axis=1).to_numpy()
    data["L_FCAS_price"] = pd.concat(tmp_L_FCAS, axis=1).to_numpy()

# ------------------------------------------------- common -------------------------------------------------
def readLoad(LoadFile, data):
    df_load = pd.read_csv(f'{os.getcwd()}/data/{LoadFile}')
    data["load"] = df_load.iloc[:, 1:]

def readPV(PVFile, data):
    df_PV = pd.read_csv(f'{os.getcwd()}/data/{PVFile}')
    data["PV"] = df_PV.iloc[:-1, 1:]
    
def readSetting(data):
    lenT            = len(data["load"])
    data["T"]       = range(lenT)
    data["W"]       = range(3)
    data["Δt"]      = (365 * 24) / lenT

# ------------------------------------------------- output initialization -----------------------------------   
def initialization(inputs, data):
    outputs = OrderedDict()
    client_range = range(inputs["start_client"], inputs["end_client"] + 1)
    # model information
    outputs["time"]        = [0 for _ in range(len(data["Ids"]))]
    outputs["bin_vars"]    = [0 for _ in range(len(data["Ids"]))]
    outputs["real_vars"]   = [0 for _ in range(len(data["Ids"]))]
    outputs["constraints"] = [0 for _ in range(len(data["Ids"]))]
    
    # objective information
    outputs["total_net_cost"]  = [0 for _ in range(len(data["Ids"]))]
    outputs["energy_net_cost"] = [0 for _ in range(len(data["Ids"]))]
    outputs["FCAS_net_cost"]   = [0 for _ in range(len(data["Ids"]))]
    
    # variable information
    outputs["E_b"]  = np.zeros((len(data["T"]),     len(data["Ids"])))
    
    outputs["L_b"]  = np.zeros((len(data["T"]),     len(data["Ids"])), dtype=np.object)
    outputs["R_b"]  = np.zeros((len(data["T"]),     len(data["Ids"])), dtype=np.object)
    
    outputs["L_c"]  = np.zeros((len(data["T"]),     len(data["Ids"])))
    outputs["L_d"]  = np.zeros((len(data["T"]),     len(data["Ids"])))
    outputs["R_c"]  = np.zeros((len(data["T"]),     len(data["Ids"])))
    outputs["R_d"]  = np.zeros((len(data["T"]),     len(data["Ids"])))
    
    outputs["PV"]   = np.zeros((len(data["T"]),     len(data["Ids"])))
    outputs["L_pv"] = np.zeros((len(data["T"]),     len(data["Ids"])))
    outputs["R_pv"] = np.zeros((len(data["T"]),     len(data["Ids"])))
    
    outputs["SOC"]  = np.zeros((len(data["T"]) + 1, len(data["Ids"])))
    outputs["P_c"]  = np.zeros((len(data["T"]),     len(data["Ids"])))
    outputs["P_d"]  = np.zeros((len(data["T"]),     len(data["Ids"])))
    
    # company cost
    outputs["cost_c"] = [0 for _ in range(len(data["Ids"]))]
    
    return outputs
    
if __name__ == '__main__':
    model = "1"
    if (model == "1"):
        data = read_model_1("DER.xlsx", "Prices.csv", "Load time_series.csv", "PV time_series.csv")
        inputs = OrderedDict()
        inputs["start_client"]   = 0
        inputs["end_client"]     = 2
        inputs["number_clients"] = 3 # max : 92
        inputs["FCAS"]           = True
        outputs = initialization(inputs, data)
    elif (model == "2"):
        data = read_model_2("Clients/DER.xlsx", "Clients/Export.csv", "Clients/Import.csv", "Clients/Wholesale prices.csv", "Clients/Inflexible load.csv", "Clients/PV.csv")
        inputs = OrderedDict()
        inputs["start_client"]   = 0
        inputs["end_client"]     = 2
        inputs["number_clients"] = 3 # max : 92
        inputs["FCAS"]           = True
        outputs = initialization(inputs, data)
        
    