# Project name: Optimisation models to plan energy aggregator business models
# Author: Yixi Rao
# Author uid: u6826541
# Supervisor: Jose Iria

## Description:
# This python file contains functions that define the reading of business model data, which will be read into the two optimisation models, 
# and initialise the storage container for the optimisation results.

# Imports ---------------------------------------------------------------------
import numpy as np
import pandas as pd
from collections import OrderedDict
import os

## Read aggregator business model data ---------------------------------------------------------------------
def read_aggregator_business_model(DERFile, PriceFile, LoadFile, PVFile):
    '''Read the data related to aggregator business model

        Args:
            DERFile :   File path of DER parameters
            PriceFile : File path of wholesale prices
            LoadFile :  File path of Load time series
            PVFile :    File path of PV time series

        Returns:
            data (OrderedDict): A dictionary that contains all the information needed to optimise DER.
    '''
    data = OrderedDict()
    # Read BESS data, and clients' id
    readSameBESS(DERFile, data)
    # Read energy and FCAS wholesale prices
    readWholesalePrices(PriceFile, data)
    # Read clients' load
    readLoad(LoadFile, data)
    # Read clients' PV generation
    readPV(PVFile, data)
    # Compute other parameters useful to the MILP optimisation model
    readSetting(data)
    
    return data

def readSameBESS(DERFile, data):
    '''read data related to BESS such as Max_SOC, Min_SOC, efficiency, maximum charging/discharging power and also clients' id
    '''
    df_Battery = pd.read_excel(f'{os.getcwd()}/data/{DERFile}', sheet_name="Battery")
    df_PVID    = pd.read_excel(f'{os.getcwd()}/data/{DERFile}', sheet_name="PV")
    data["Ids"]     = df_PVID.columns.values
    data["power"]   = df_Battery["power"].item()
    data["Max_SOC"] = df_Battery["energy"].item()
    data["Min_SOC"] = 0
    data["eff"]     = df_Battery["eff"].item()
    
def readWholesalePrices(PriceFile, data):
    '''Read energy and FCAS market wholesale prices and also time intervals
    '''
    df_Prices = pd.read_csv(f'{os.getcwd()}/data/{PriceFile}', na_values=["  "])
    # Time interval (5min): from 2018/1/1 0:00 to 2018/12/31 23:55
    data["Time"]         = df_Prices["Time"]
    ## Orignal price is $/MWh, now change to kwh
    # Energy wholesale prices
    data["energy_price"] = df_Prices["ENERGY"].apply(lambda x: x / 1000).iloc[:105120]
    # FCAS market prices (Raise - 6s, 60s, 5min and lower - 6s, 60s, 5min)
    tmp_R_FCAS = []
    tmp_L_FCAS = []
    for i in ["RAISE6S", "RAISE60S", "RAISE5MIN"]:
        tmp_R_FCAS.append(df_Prices[i].apply(lambda x: x / 1000).iloc[:105120])
        
    for i in ["LOWER6S", "LOWER60S", "LOWER5MIN"]:
        tmp_L_FCAS.append(df_Prices[i].apply(lambda x: x / 1000).iloc[:105120])

    data["R_FCAS_price"] = pd.concat(tmp_R_FCAS, axis=1).to_numpy()
    data["L_FCAS_price"] = pd.concat(tmp_L_FCAS, axis=1).to_numpy()

## Read retail business model data ---------------------------------------------------------------------
def read_retail_business_model(DERFile, tariffSellFile, tariffBuyFile, WholesalePriceFile, LoadFile, PVFile):
    '''read the data related to retail business model

        Args:
            DERFile : File path of DER parameters
            tariffSellFile : File path of four tariff energy sales prices
            tariffBuyFile : File path of four tariff energy purchase prices
            WholesalePriceFile : File path of wholesale prices
            LoadFile : File path of load time series
            PVFile : File path of PV time series

        Returns:
            data (OrderedDict): A dictionary that contains all the information needed to optimise DER.
    '''
    data = OrderedDict()
    # Read BESS data for each client, and clients' id
    readDiffBESS(DERFile, data)
    # Read the four tariff energy sales prices and energy purchase prices, and also the time
    readTariff(tariffSellFile, tariffBuyFile, data)
    # Read energy wholesale prices and also time intervals
    readWholesalePrice(WholesalePriceFile, data)
    # Read clients' load
    readLoad(LoadFile, data)
    # Read clients' PV generation
    readPV(PVFile, data)
    # Compute other parameters useful to the MILP optimisation model
    readSetting(data)
    
    return data

def readDiffBESS(DERFile, data):
    '''read data related to BESS for each client such as Max_SOC, Min_SOC, efficiency, maximum charging/discharging power and also clients' id
    '''
    df_Battery = pd.read_excel(f'{os.getcwd()}/data/{DERFile}', sheet_name="Battery")
    data["Ids"]     = df_Battery.columns.values
    data["power"]   = df_Battery.iloc[0, :].to_numpy(dtype = "float")
    data["Max_SOC"] = df_Battery.iloc[1, :].to_numpy(dtype = "float")
    data["Min_SOC"] = 0
    data["eff"]     = df_Battery.iloc[2, :].to_numpy(dtype = "float")

def readTariff(tariffSellFile, tariffBuyFile, data):
    '''Read the four tariff energy sales prices and energy purchase prices, and also the time
    '''
    df_BuyPrices  = pd.read_csv(f'{os.getcwd()}/data/{tariffBuyFile}', na_values=["  "])
    df_SellPrices = pd.read_csv(f'{os.getcwd()}/data/{tariffSellFile}')
    # time interval
    data["Time"]        = df_BuyPrices["Time"]
    # Tariff 0, 1, 2, 3 selling prices and buying price
    data["tariff_buy"]  = {"0" : df_BuyPrices.iloc[:, 1],
                           "1" : df_BuyPrices.iloc[:, 2],
                           "2" : df_BuyPrices.iloc[:, 3],
                           "3" : df_BuyPrices.iloc[:, 4]}
    data["tariff_sell"] = {"0" : df_SellPrices.iloc[:, 0].item(),
                           "1" : df_SellPrices.iloc[:, 1].item(),
                           "2" : df_SellPrices.iloc[:, 2].item(),
                           "3" : df_SellPrices.iloc[:, 3].item()}
    
def readWholesalePrice(WholesalePriceFile, data):
    '''Read energy wholesale prices and also time intervals
    '''
    df_WSPrice           = pd.read_csv(f'{os.getcwd()}/data/{WholesalePriceFile}')
    data["energy_price"] = df_WSPrice["ENERGY"].iloc[:105120]

## General function ---------------------------------------------------------------------
def readLoad(LoadFile, data):
    '''Read clients' load
    '''
    df_load = pd.read_csv(f'{os.getcwd()}/data/{LoadFile}')
    data["load"] = df_load.iloc[:, 1:]

def readPV(PVFile, data):
    '''Read clients' PV generation
    '''
    df_PV = pd.read_csv(f'{os.getcwd()}/data/{PVFile}')
    data["PV"] = df_PV.iloc[:-1, 1:]
    
def readSetting(data):
    '''Compute other parameters useful to the MILP optimisation model
    '''
    # total time interval
    lenT       = len(data["load"])
    # time interval index
    data["T"]  = range(lenT)
    # FCAS market types - 6s, 60s, 5min
    data["W"]  = range(3)
    # time interval = 1/12 h = 5min
    data["Δt"] = (365 * 24) / lenT

## Output initialisation ---------------------------------------------------------------------
def initialisation(inputs, data):
    '''configure the optimisation results container
    '''
    outputs      = OrderedDict()
    client_range = range(inputs["start_client"], inputs["end_client"] + 1)
    # model information
    outputs["time"]        = [0 for _ in range(len(data["Ids"]))]
    outputs["bin_vars"]    = [0 for _ in range(len(data["Ids"]))]
    outputs["real_vars"]   = [0 for _ in range(len(data["Ids"]))]
    outputs["constraints"] = [0 for _ in range(len(data["Ids"]))]
    
    # Objective function information
    outputs["total_net_cost"]  = [0 for _ in range(len(data["Ids"]))]
    outputs["energy_net_cost"] = [0 for _ in range(len(data["Ids"]))]
    outputs["FCAS_net_cost"]   = [0 for _ in range(len(data["Ids"]))]
    # Electricity wholesale cost for ROM
    outputs["cost_c"] = [0 for _ in range(len(data["Ids"]))]
    
    # Variable information
    outputs["E_b"]    = np.zeros((len(data["T"]),   len(data["Ids"])))
    outputs["E_buy"]  = np.zeros((len(data["T"]),   len(data["Ids"])))
    outputs["E_sell"] = np.zeros((len(data["T"]),   len(data["Ids"])))
    
    outputs["L_b"] = np.zeros((len(data["T"]),      len(data["Ids"])), dtype=np.object)
    outputs["R_b"] = np.zeros((len(data["T"]),      len(data["Ids"])), dtype=np.object)
    
    outputs["L_c"] = np.zeros((len(data["T"]),      len(data["Ids"])))
    outputs["L_d"] = np.zeros((len(data["T"]),      len(data["Ids"])))
    outputs["R_c"] = np.zeros((len(data["T"]),      len(data["Ids"])))
    outputs["R_d"] = np.zeros((len(data["T"]),      len(data["Ids"])))
    
    outputs["PV"]   = np.zeros((len(data["T"]),     len(data["Ids"])))
    outputs["L_pv"] = np.zeros((len(data["T"]),     len(data["Ids"])))
    outputs["R_pv"] = np.zeros((len(data["T"]),     len(data["Ids"])))
    
    outputs["SOC"]  = np.zeros((len(data["T"]) + 1, len(data["Ids"])))
    outputs["P_c"]  = np.zeros((len(data["T"]),     len(data["Ids"])))
    outputs["P_d"]  = np.zeros((len(data["T"]),     len(data["Ids"])))
    
    return outputs