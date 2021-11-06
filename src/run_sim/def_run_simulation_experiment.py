import datetime as dt
import math
import os
import time
from typing import Union

from joblib import Parallel, delayed
from matplotlib import pyplot as plt
import seaborn as sns

from src.sim.sim import Sim
from src.misc.timetables import *


def run_simulation_experiment(
        state: int,
        infection_prob: float,
        n_ticks_to_quarantine: Union[int, float],
        n_cores: int = 1,
        n_internal_runs: int = 60,
        n_initial_infections: int = 50,
        n: int = 100000,
        n_random_infections: Union[int, float] = 0,
        save_output: bool = True,
        display_simulation: bool = False,
    ):

    # list of all timetables + a scenario name
    timetables = [
        (timetable_default, "baseline"),
        (timetable_no_homeoffice, "no_homeoffice"),
        (timetable_no_reduction_of_work, "no_reduction_of_work"),
        (timetable_no_quarantine, "no_quarantine"),
        (timetable_open_kitas, "open_kitas"),
        (timetable_open_schools, "open_schools"),
        (timetable_open_schools_kitas, "open_schools_kitas"),
        (timetable_open_universities, "open_universities"),
        (timetable_open_education, "open_education"),
        ]
    
    # a list of lists with parameter settings for each timetable/scenario
    params_experiment = [
        [
         infection_prob,
         n_initial_infections,
         n,
         n_random_infections,
         timetable[0],
         n_ticks_to_quarantine,
         n_internal_runs,
         timetable[1] + "_" + str(state), # name of scenario/run
         save_output,
         display_simulation,
        ] for timetable in timetables]
    
    # create state-specific simulation model
    model = Sim(state=state, n_cores=n_cores)

    # run scenarios step by step
    results = [model.run(params) for params in params_experiment]
    
    return results