import time
from pathlib import Path

import pandas as pd
import spotpy

import src
from src.calibration.def_calibration import state_calibration
from src.misc.timetables import timetable_default
    
state_calibration(
    state = 8,
    n_initial_infections = 50,
    n = 100000,
    timetable = timetable_default,
    n_internal_runs = 60,
    n_calibration_runs = 180,
    output_file_path = Path.joinpath(src.PATH, "output_data", "LHS_BW_2021_01_20"),
    name_of_run = "kalib_bw",
    parallel = True,
    )