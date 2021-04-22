from pathlib import Path

from build_simulation import *
from def_get_params import *
from timetables import *

from joblib import Parallel, delayed


def sens_check(state, spotpy_output_data_path, parallel = True):
    assert state in (2, 8, 9, 10)
    
    def run_simulation_with(attrname_and_value):
    
        attrname, value = attrname_and_value
        
        cali_params = get_spotpy_params(spotpy_output_data_path)    
        
        TIMETABLE = timetable_default
        INFECTION_PROB = cali_params["infection_prob"]
        N_INITIAL_INFECTIONS = 50
        N = 100000
        N_RANDOM_INFECTIONS = 0
        N_TICKS_TO_QUARANTINE = cali_params["ticks_to_quarantine"]
        N_INTERNAL_RUNS = 60
        NAME_OF_RUN = "robust_" + str(state) + "_" + attrname + "_" + str(value)
        SAVE_OUTPUT = False
        DISPLAY_SIMULATION = False
        
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
        
        model = Sim(state)
        
        if value:
            setattr(model, attrname, value)
        
        output = model.run(params)
        
        df = output["df"]
        
        df["tested_parameter"] = attrname + "_=_" + str(getattr(model, attrname))
        
        return df
    
    
    checked_params = []
    
    checked_params.extend(
        [["n_colleagues", i] for i in (5, None, 15)]
        )
    checked_params.extend(
        [["students_per_university", i] for i in (50, 100, None)]
        )
    checked_params.extend(
        [["hours_at_kindergarten", i] for i in (4, None, 6)]
        )
    checked_params.extend(
        [["hours_at_school", i] for i in (4, None, 6)]
        )
    checked_params.extend(
        [["hours_at_university", i] for i in (3, None, 5)]
        )
    
    if parallel:
        results = Parallel(n_jobs=15)(map(delayed(run_simulation_with), checked_params))
    else:
        results = [run_simulation_with(attrname_and_value) for attrname_and_value in checked_params]
    
    df = pd.concat(results)
    df.to_csv(Path.joinpath(src.PATH, "output_data", "sens_" + str(state) + ".csv"))
    
    return df


