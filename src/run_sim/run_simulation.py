from pathlib import Path

import src
from src.misc.timetables import *
from src.run_sim.def_get_params import get_spotpy_params
from src.sim.sim import Sim


params_hh = get_spotpy_params(Path.joinpath(src.PATH, "important_outputs", "params", "LHS_BW_2021_01_20.csv"))

STATE = 8
TIMETABLE = timetable_default
INFECTION_PROB = params_hh["infection_prob"]
N_INITIAL_INFECTIONS = 50
N = 1000
N_RANDOM_INFECTIONS = 0
N_TICKS_TO_QUARANTINE = params_hh["ticks_to_quarantine"]
N_INTERNAL_RUNS = 1
NAME_OF_RUN = "test12345"
SAVE_OUTPUT = False
DISPLAY_SIMULATION = True

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