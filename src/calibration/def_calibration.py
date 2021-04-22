import time

import pandas as pd
import spotpy

from src.sim.sim import Sim


def state_calibration(
        state,
        n_initial_infections,
        n,
        timetable,
        n_internal_runs,
        n_calibration_runs,
        output_file_path,
        name_of_run,
        parallel,
        ):
    
    start_time = time.time()
    results=[]
    sampler = spotpy.algorithms.lhs(
        SpotSetup(
            state,
            timetable,
            output_file_path,
            name_of_run,
            n_initial_infections,
            n,
            n_internal_runs,
            n_calibration_runs,
            ),
        dbname=output_file_path, 
        dbformat='csv',
        parallel=('mpi' if parallel == True else "seq"),
        )
    sampler.sample(n_calibration_runs)
    results.append(sampler.getdata())
    
    end_time = time.time()
    duration_time = end_time - start_time
    print("duration time:", duration_time)
    return sampler
    
    
    

class SpotSetup(object):
    
    def __init__(
            self,
            state,
            timetable,
            output_file_path,
            name_of_run,
            n_initial_infections,
            n,
            n_internal_runs,
            n_calibration_runs,
            ):
        
        self.state = state
        self.timetable = timetable
        self.output_file_path = output_file_path
        self.name_of_run = name_of_run
        self.n_initial_infections = n_initial_infections
        self.n = n
        self.save_output = False
        self.n_internal_runs = n_internal_runs
        self.n_calibration_runs = n_calibration_runs
        
        self.params = [
            spotpy.parameter.Uniform("infection_prob", 0.045, 0.07 , 0.001, 0.06),
            #spotpy.parameter.Uniform("n_random_infections", 0, 0.02 , 0.001, 0.002625),
            spotpy.parameter.Uniform("n_ticks_to_quarantine", 10, 30, 1, 15),
            ]
        self.model = Sim(state = self.state)
        self.evaluation_data = self.model.eval_data
        pd.Series(self.evaluation_data).to_csv(self.output_file_path + "_eval_data.csv", index = False)
        
    def parameters(self):
        return spotpy.parameter.generate(self.params)
    
    def simulation(self, vector):
        infection_prob = vector[0]
        n_random_infections = 0 
        n_ticks_to_quarantine = vector[1]
        
        display_simulation = False
        
        p = [
            infection_prob,
            self.n_initial_infections,
            self.n,
            n_random_infections,
            self.timetable,
            n_ticks_to_quarantine,
            self.n_internal_runs,
            self.name_of_run,
            self.save_output,
            display_simulation
            ]
        
        simulation_output = self.model.run(p)
        
        return simulation_output["calibration_data"]
    
    def evaluation(self):
        return self.evaluation_data
    
    def objectivefunction(self,simulation,evaluation):
        objectivefunction= -spotpy.objectivefunctions.rmse(
            evaluation,
            simulation,
            )
        return objectivefunction