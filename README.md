# Empirically-calibrated ABM for the evaluation of NPIs in Germany
The overall purpose of this model is to investigate the effects of various non-pharmaceutical interventions (NPI) in curbing the spread of COVID-19.
The model predicts case numbers of counterfactual scenarios in which certain NPIs are (not) implemented.
The model is evaluated by its ability to reproduce time-series data of empirically observed case numbers in a baseline scenario that mimics the factual implementation of NPIs happened in spring 2020 in Germany.
In the current version of the model the infections on the level of four federal states with differing social structures are simulated. 
We chose the four states in Germany (Baden-Wuerttemberg, Bavaria, Hamburg, Saarland) with the highest infection rate relative to its population size during the first wave of Covid-19 in Germany (March 2020).

## Requirements
- **SOEP**: An important prerequisite in order to use this version of the model is to have permission to use the Socio-economic Panel 2017 and to have a copy of this dataset on your local machine. You can get the data [here](https://www.diw.de/sixcms/detail.php?id=diw_01.c.738729.en).
- **STATA**: Unfortunately, the current version of the model also requires a working installation of STATA (version >= 13). *(We are currently working on an update which will remove the requirement for STATA and will replace the STATA-code by python-code.)*
- **Conda**: To install and activate the specific virtual python environment, a current installation of Conda is required.

## Setup
1. Clone this repository onto your local machine.
2. Take the folder `"soep.v34"` provided in the SOEP-data and copy it into the repository's folder `"data"`.
3. Open the STATA-file `"stata_01_merge_soep_datasets.do"`, change the working directory to the repository's root folder on your local machine.
4. Execute the STATA-skript `"stata_01_merge_soep_datasets.do"`.
5. Open the STATA-file `"stata_02_clean_soep_data.do"`, change the working directory to the repository's root folder on your local machine.
6. Execute the STATA-skript `"stata_02_clean_soep_data.do"`.
7. Install the virtual environment from the file `"env.yaml"` using conda.
8. If everything has been done correctly, the model is now ready for use.

## Overview
The building blocks of the simulation are located in the module `src.sim`, especially in the files `sim.py` and `agent.py`.
The main scripts to execute the simulation can be found in the module `src.run_sim`.

## Single simulation
A single simulation can be executed by first creating a `model`-object from the module `src.sim.sim` and then executing the `model`-method `run()`. 
The simplest way to do this, is to use the file `"run_simulation.py"` from the module `src.run_sim`.
Adjust the parameters, execute the python-file and the output-data will appear in the folder `"output_data"`.
In the output file the column `"cumulative_cases"` gives the cumulative number of infected agents per day and the column `"adj_cumulative_cases/100k"` scales this value to a population of 100,000 inhabitants. The column `"empirical_cumulative_cases/100k"` provides the empirical cumulative number of cases per 100,000 inhabitants in the chosen federal state.

## Simulation experiments
To conduct the simulation experiments performed in this [paper](https://www.medrxiv.org/content/10.1101/2021.04.16.21255606v1), four files were prepared, each running the experiment for one of the considered states.
- Hamburg: `"run_simulation_experiment_HH.py"`
- Baden-Wuerttemberg: `"run_simulation_experiment_BW.py"`
- Bavaria: `"run_simulation_experiment_BY.py"`
- Saarland: `"run_simulation_experiment_SL.py"`

The number of replications per scenario is preconfigured to a value of 60, which could lead to a total runtime of several days if executed on a single core.
Therefore it is recommended to change the parameter `parallel` from `False` to `True` in order to parallelize one simulation experiment on up to 10 cores (*please note that if running the simulation under windows, the attempt to parallelize might fail*).

## Update
We are currently working on a major update which will improve modularity, flexibilty, and efficancy of the simulation model. It will be released in November 2021.
