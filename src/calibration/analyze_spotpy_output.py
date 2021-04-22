import os
from pathlib import Path
import time

from matplotlib import pyplot as plt
import pandas as pd
import spotpy
import seaborn as sns

import src
from src.sim.sim import Sim


plt.style.use("ggplot")

def analyze_spotpy_output(state, dataset_path):
    model = Sim(state = state)
    df = pd.read_csv(dataset_path)
    df = df.sort_values("like1", ascending = False).reset_index(drop = True)
    best_df = df.iloc[0:1,:]
    best_df["rank"] = best_df.index
    best_df = pd.wide_to_long(best_df, ["simulation_"], i = "rank", j = "time")
    best_df = best_df.reset_index()
    best_df["time"] = best_df["time"]
    plt.plot(
        model.eval_data, 
        marker="o", 
        label = "emp. " + str(state),
        color = "green", 
        alpha = 0.2,
        )
    sns.lineplot(
        x="time", 
        y="simulation_", 
        data = best_df, 
        legend = "full", 
        label = "sim. " + str(state), 
        color = "yellow",
        hue = "rank",
        )
    plt.show()
    return best_df


# best_df8 = analyze_spotpy_output(8, Path.joinpath(src.PATH, "output_data", "LHS_BW_2021_01_20.csv"))
# best_df2 = analyze_spotpy_output(2, Path.joinpath(src.PATH, "output_data", "LHS_HH_2021_01_22.csv"))
# best_df10 = analyze_spotpy_output(10, Path.joinpath(src.PATH, "output_data", "LHS_SAAR_2021_01_20.csv"))
# best_df9 = analyze_spotpy_output(9, Path.joinpath(src.PATH, "output_data", "LHS_BY_2020_01_14.csv"))