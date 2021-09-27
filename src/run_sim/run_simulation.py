from pathlib import Path

import seaborn as sns

import src
from src.misc.timetables import *
from src.run_sim.def_get_params import get_spotpy_params
from src.sim.sim import Sim


##################################################################################
# parameter setting
##################################################################################

# set a state code (2 = Hamburg, 8 = Baden-Wuerttemberg, 9 = Bavaria, 10 = Saarland) 
STATE = 9

# set a NPI-timetable
# (possible options: timetable_default, timetable_no_reduction_of_work,timetable_no_homeoffice, timetable_no_quarantine, timetable_open_kitas, timetable_open_schools, timetable_open_universities, timetable_open_schools_kitas, timetable_open_education)
TIMETABLE = timetable_default

# set the number of agents
N = 1000

# set the number of initially infected agents
N_INITIAL_INFECTIONS = 50

# set the number of replications
N_INTERNAL_RUNS = 10

# set a name for the simulation
NAME_OF_RUN = "baseline_scenario_bavaria"


##################################################################################
# model setup and execution (do not touch)
##################################################################################

assert STATE in (2, 8, 9, 10), "STATE has to be one of the following integers: 2, 8, 9, 10"

if STATE == 2:
    spotpy_params = get_spotpy_params(Path.joinpath(src.PATH, "important_outputs", "params", "LHS_HH_2021_01_22.csv"))
elif STATE == 8:
    spotpy_params = get_spotpy_params(Path.joinpath(src.PATH, "important_outputs", "params", "LHS_BW_2021_01_20.csv"))
elif STATE == 9:
    spotpy_params = get_spotpy_params(Path.joinpath(src.PATH, "important_outputs", "params", "LHS_BY_2021_01_14.csv"))
elif STATE == 10:
    spotpy_params = get_spotpy_params(Path.joinpath(src.PATH, "important_outputs", "params", "LHS_SL_2021_01_20.csv"))

INFECTION_PROB = spotpy_params["infection_prob"]
N_TICKS_TO_QUARANTINE = spotpy_params["ticks_to_quarantine"]
N_RANDOM_INFECTIONS = 0
DISPLAY_SIMULATION = False
SAVE_OUTPUT = True

params = [
     INFECTION_PROB,
     N_INITIAL_INFECTIONS,
     N,
     N_RANDOM_INFECTIONS,
     TIMETABLE,
     N_TICKS_TO_QUARANTINE,
     N_INTERNAL_RUNS,
     NAME_OF_RUN,
     SAVE_OUTPUT,
     DISPLAY_SIMULATION,
    ]

model = Sim(STATE)
output = model.run(params)


##################################################################################
# simple plot
##################################################################################

