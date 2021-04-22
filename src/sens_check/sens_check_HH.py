from pathlib import Path

import src
from src.def_sens_check import sens_check

sens_check(
    state = 2,
    spotpy_output_data_path = Path.joinpath(src.PATH, "important_outputs", "params", "LHS_HH_2021_01_22.csv"), 
    )