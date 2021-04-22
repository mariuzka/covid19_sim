from pathlib import Path

import src
from src.run_sim.def_run_simulation_experiment import run_simulation_experiment
from src.run_sim.def_get_params import get_spotpy_params


spotpy_params = get_spotpy_params(Path.joinpath(src.PATH, "important_outputs", "params", "LHS_BY_2021_01_14.csv"))

results = run_simulation_experiment(
    state = 9,
    infection_prob = spotpy_params["infection_prob"],
    n_ticks_to_quarantine = spotpy_params["ticks_to_quarantine"],
    parallel = False,
    )