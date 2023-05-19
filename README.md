# Optimisation models to plan energy aggregator business models 
>Name: *Yixi Rao*  
Email: *u6826541@anu.edu.au*  
UID: *u6826541*  
Supervisor: *Dr. José Iria*  
***
## 1. Project information
This project submitted for the course [COMP4560](https://programsandcourses.anu.edu.au/2023/course/COMP4560) - Advanced Computing Project. The project description is in [Optimisation of distributed energy resources](https://cecc.anu.edu.au/research/student-research-projects/optimisation-distributed-energy-resources).

## 2. Artefact description
This project proposes two optimisation frameworks to support aggregators to develop new business models and assess the economic benefits of various business models. These new business models aim to foster a better distribution of the possible economic gains between aggregators and their clients, and with this attract more clients.The frameworks consist of two MILP models:
+ ***Aggregator Optimisation Model (AOM)***: This model calculates the wholesale costs of aggregator by optimising DER operations and bidding in the FCAS markets.
+ ***Retail Optimisation Model (ROM)***: This model calculates the retail costs of clients by optimising DER operations under different tariffs.  

The optimisation models will explore mixed-integer linear techniques to optimise the operation of DER and identify their economic benefits in different business models.  

## 3. Software and hardware requirements
+ Python version: Anaconda Python 3.8.3
+ NumPy
+ Pandas
+ Pyomo: Python Optimisation Modeling Objects
+ Solver:
    + IBM(R) ILOG(R) CPLEX(R) Interactive Optimiser 22.1.0.0
    + GLPK (GNU Linear Programming Kit) package
+ RAM requirement: It is better to have more than 32GB of RAM, because the amount of optimisation operations in a year is extremely large and small RAM may report the existence of memory overflow errors (My computer is 32GB)

## 4. Instruction
**Please change only the configurations in main.py, and do not change the other files.**  
To run the model, follow the steps mentioned in 4.1.

### 4.1 [main.py](main.py)
The central file of this project, which can read data from different business models to run AOM or ROM on a specific client's ID range and optimise the usage of their DER for a year. The optimisation results are displayed as CSV files in the output directory in the corresponding business model subdirectory.
The model configurations stored in `inputs ` that can be changed are:  
1. `inputs["start_client"]` and `inputs["end_client"]`: Changing the starting client ID and ending client ID to specify 
the model to run within this clients' ID range (available range is [0, 91]).
2. `inputs["FCAS"]`: Deciding whether the aggregator participates in the FCAS market, if it does, please change it to True, 
if it only participates in the Energy market, please change it to False.
3. `inputs["Model"]`: indicating which model is running, you can choose between "AOM" and "TOM"
4. `inputs['saveDetail']`: Deciding whether to save variable values into the output files.

After you have completed all the configurations, simply run the model. The terminal shows the model configurations and the current optimisation progress.

### 4.2 [read.py](read.py)
This python file contains functions that define the reading of business model data, which will be read into the two optimisation models, 
and initialise the storage container for the optimisation results. This file contains two read data functions:
+ `read_aggregator_business_model`: Read the aggregator business model data files stored in the *data\aggregator_model_data*
+ `read_retail_business_model`: Read the retail business model data files stored in the *data\retail_model_data folder*

and an optimisation result storage container initialisation function.
+ `initialisation`: Configure the optimisation results container `outputs`

### 4.3 [model.py](model.py)
This file contains two MILP optimisation model functions. This function integrates model definition, optimisation problem solving, and optimization result export. The two models (AOM & ROM) are in:
+ `Aggregator_Optimisation_Model`: AOM
+ `Retail_Optimisation_Model`: ROM

Specific indices, parameter variable definition, objective function and constraint details are well commented in the model.

### 4.4 [write.py](write.py)
This file writes the optimisation result data of AOM or ROM stored in `outputs` into the CSV files, where:
+ `write_cost_outputs`: Write the objective function values of all client IDs specified in main.py into:
    + `output\aggregator_business_model`: AOM results. There will be different subdirectories for different market participation scenarios.
    + `output\retail_business_model`: ROM results. There will be different subdirectories for different tariffs.
+ `write_var_output` or `write_var_output_v2`: Write the variables values of all client IDs specified in main.py into the folder mentioned above. 

## 5. Acknowledgement
I would like to express my Deepest gratitude to Dr. José Iria for his professional competence and meticulous guidance.