from pathlib import Path

import src
from src.run_sim.def_get_params import get_spotpy_params
from src.run_sim.def_run_simulation_parallel import run_simulation_parallel

params_by = get_spotpy_params(Path.joinpath(src.PATH, "important_outputs", "params", "LHS_BY_2021_01_14.csv"))

df = run_simulation_parallel(
    state = 9,
    infection_prob = params_by["infection_prob"],
    n_ticks_to_quarantine = params_by["ticks_to_quarantine"],
    parallel = True,
    timetable = timetable_default,
    name_of_run = "by_60_repr_test",
    save_output = True,
    )