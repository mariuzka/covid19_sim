from matplotlib import pyplot as plt
import pandas as pd
from pathlib import Path
import seaborn as sns

import src

def recode_state(state):
    if state == 2:
        return "Hamburg"
    elif state == 8:
        return "Baden-Wuerttemberg"
    elif state == 9:
        return "Bavaria"
    elif state == 10:
        return "Saarland"
    
def sens_check_box(params, df):
    for p in params:
        
        sns.set_style("whitegrid")
        #plt.style.use('ggplot')
        
        g = sns.FacetGrid(
            df[(df["parameter"] == p) & (df["day"] == 99)], 
            col="state",
            margin_titles=True,
            #aspect = 5,
            height = 4,
            col_wrap=2,
        )
        g.map(
            sns.boxplot,
            "parameter_value", 
            "adj_cumulative_cases/100k",
            #color="white",
        )
        
        x_label = p.replace("_", " ").capitalize()
        #g.fig.suptitle(x_label)
        #g.set_titles("test123")
        g.set_axis_labels(x_var=x_label, y_var="COVID-19 cases/100000")
        
        g.set(ylim=(0, None))
        g.fig.tight_layout()
        #g.set(xlabel=x_label)
        g.savefig("output_data/sens_box_" + p + ".pdf")

df = pd.concat([
    pd.read_csv(src.PATH("output_data", "sens_8.csv")),
    pd.read_csv(src.PATH("output_data", "sens_9.csv")),
    pd.read_csv(src.PATH("output_data", "sens_2.csv")),
    pd.read_csv(src.PATH("output_data", "sens_10.csv")),
])

df["state"] = df.group.apply(lambda x: recode_state(x))
df["parameter"] = df.tested_parameter.apply(lambda x: x.split("=")[0].strip("_"))
df["parameter_value"] = df.tested_parameter.apply(lambda x: int(x.split("=")[1].replace("_","")))

params = [
    "hours_at_kindergarten",
    "hours_at_school",
    "hours_at_university",
    "n_colleagues",
    "students_per_university",
]

sens_check_box(params, df)





