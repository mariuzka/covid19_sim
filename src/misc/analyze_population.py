from pathlib import Path
import random
import time

import pandas as pd
import seaborn as sns

import src 
from src.sim.sim import Sim


def desc_agent_pop(state, n_agents, n_internal_runs):
    
    dfs = []
    for rep in range(n_internal_runs):
        start_time = time.time()
        
        print(round((rep/n_internal_runs)*100),"%")
        model = Sim(state)

        population = model.create_soep_population(
            N = n_agents,
            agent_class = Corona_Agent,
            )

        data = []
        for i, hh in enumerate(population):
            hh_size = len(hh)
            hh_id = i
            
            for i, agent in enumerate(hh):
                
                # kindergarten kid?
                if agent.age in range(0, 6):
                    
                    care_rate = (model.care_rate_data.loc[model.fed_states[agent.federal_state], "0_bis_2"] 
                    if agent.age <= 2 else model.care_rate_data.loc[model.fed_states[agent.federal_state], "3_bis_5"]
                    )
                    
                    assert 0 <= care_rate <= 1, "care_rate has to be within 0 - 1"
                    
                    if random.random() < care_rate:
                        agent.kindergarten = 1
                    else:
                        agent.kindergarten = 0
                else:
                    agent.kindergarten = 0
                    
                    
                data.append(
                    {"hh_id" : hh_id,
                     "agent_id" : i,
                     "gender": agent.gender,
                     "age": agent.age,
                     "nace2_long": agent.nace2,
                     "nace2_short": agent.nace2_short,
                     "hh_size": hh_size,
                     "student": agent.student,
                     "kindergarten": agent.kindergarten,
                     "pupil": (1 if agent.age in range(6,20) else 0),
                     "work_hours": agent.work_hours_day_in_ticks,
                 }
                    )
    
        df = pd.DataFrame.from_records(data)
        dfs.append(df)
        
        duration_min = (time.time() - start_time) / 60
        print(duration_min, "minutes")
    df = pd.concat(dfs)
    df["state"] = state
    return df

def recode_state(state):
    if state == 2:
        return "Hamburg"
    elif state == 8:
        return "Baden-Wuerttemberg"
    elif state == 9:
        return "Bayern"
    elif state == 10:
        return "Saarland"

def freq_table(col, df, to_latex = True):
    freq_table = (
        df
        .groupby(["state", col])
        .percentage
        .sum()
        .round(2)
        .reset_index()
        )
    if to_latex:
        return freq_table.to_latex()
    else:
        return freq_table

def mean_table(col, df, to_latex = True):
    mean_table = (
        df
        .groupby("state")
        [col]
        .mean()
        .reset_index()
        )
    if to_latex:
        return mean_table.to_latex()
    else:
        return mean_table
    
    
REPS = 1
N_AGENTS = 1000

dfs = [
       desc_agent_pop(2, N_AGENTS, REPS),
       desc_agent_pop(8, N_AGENTS, REPS),
       desc_agent_pop(9, N_AGENTS, REPS),
       desc_agent_pop(10, N_AGENTS, REPS),
       ]

for df in dfs:
    df["n"] = len(df)
    
df = pd.concat(dfs)

df.state = df.state.apply(lambda x: recode_state(x))
df.gender = df.gender.apply(lambda x: ("m" if x == 1 else "w"))

df["tnik"] = 0
for i in df.index:
    if df.loc[i, "age"] < 6 and df.loc[i, "kindergarten"] != 1:
        df.loc[i, "tnik"] = 1
        
df["tnik"].value_counts()
        

wfh_data = pd.read_csv(Path.joinpath(src.PATH, "data", "germany", "Alipouretal_WFH_Germany-master", "wfh_nace2.csv")

df = df.merge(wfh_data, how="left", left_on="nace2_long", right_on="nace2")

mean_wfh_feas = (df
 [df.work_hours > 0]
 .groupby("state")
 ["wfh_feas"]
 .mean()
 .reset_index()
 )

mean_wfh_freq = (df
 [df.work_hours > 0]
 .groupby("state")
 ["wfh_freq"]
 .mean()
 .reset_index()
 )

df_mean_wfh = pd.merge(mean_wfh_feas, mean_wfh_freq, on="state")
df_mean_wfh["change"] = df_mean_wfh.wfh_feas - df_mean_wfh.wfh_freq
df_mean_wfh.columns = ["state", "max_homeoffice", "pre_corona_homeoffice", "change"]

mean_wfh_diff = mean_wfh_feas - mean_wfh_freq

mean_wfh_diff.plot.bar()

(df
 [df.work_hours > 0]
 .groupby("state")
 .work_hours
 .mean()
 )

###############################################################################

# create Latex-Tables


df["percentage"] = 1
df.percentage = (df.percentage / df.n) * 100

# create Latex-Tables
categorial_vars = [
    "nace2_short",
    "gender",
    "pupil",
    "kindergarten",
    "student",
    ]
freq_tables = "\n\n".join([freq_table(col, df) for col in categorial_vars])

numeric_vars = [
    "age",
    "hh_size",
    "work_hours",
    ]
mean_tables = "\n\n".join([mean_table(col, df) for col in numeric_vars])

