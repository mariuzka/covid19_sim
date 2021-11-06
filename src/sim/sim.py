import datetime as dt
from pathlib import Path
import random
import time
from typing import List

import numpy as np
import pandas as pd
import seaborn as sns
from mpire import WorkerPool

import src
from src.sim.agent import Agent
from src.sim.world import World
from src.sim.cell import Cell
from src.sim.building import Building
from src.sim.helper import dates_between

pd.options.mode.chained_assignment = None


class Sim:
    """
    This class creates a simulation model for a specific federal state in germany.
    By creating an instance of this class the simulations model for the given federal state
    is prepared.
    After creating an instance one can run the simulation model by executing the
    run()-method. The run()-method expects a list of input-values, which determine
    certain properties of the model run (infection probability, number of runs etc.).
    """

    def __init__(
            self, 
            state: int,
            n_simulated_days: int = 100,
            n_cores: int = 1,
            ):
        


        assert state in [2,8,9,10]
        
        self.n_cores = n_cores

        self.state = state
        
        self.fed_states = {
            2:  "Hamburg",
            8:  "Baden-Wuerttemberg",
            9:  "Bavaria",
            10: "Saarland",
        }
        
        self.fed_states_german = {
            2:  "Hamburg",
            8:  "Baden-Württemberg",
            9:  "Bayern",
            10: "Saarland",
        }
        
        # load school data
        school_data = pd.read_excel(Path.joinpath(src.PATH, "data", "germany", "schools.xlsx"))
        school_data["pupils/school"] = school_data["pupils"] // school_data["schools"]
        school_data["pupils/class"] = school_data["pupils"] // school_data["classes"]
        school_data["classes/school"] = school_data["classes"] // school_data["schools"]
        school_data = school_data.set_index(school_data["state"])
        self.school_data: pd.DataFrame = school_data
        
        # load kindergarten data        
        kids_per_kindergarten = pd.read_excel(Path.joinpath(src.PATH, "data", "germany", "kindergarten_group_size.xlsx"))
        kids_per_kindergarten = kids_per_kindergarten.set_index("state")
        kids_per_kindergarten = int(kids_per_kindergarten.loc[self.fed_states[state], "kindergarten_group_size"])
        
        # load homeoffice data
        wfh_data = pd.read_csv(Path.joinpath(src.PATH, "data", "germany", "wfh_nace2.csv"))
        wfh_data = wfh_data.set_index("nace2")
        wfh_data["wfh_freq"] = wfh_data["wfh_freq"] / 100
        wfh_data["wfh_feas"] = wfh_data["wfh_feas"] / 100
        self.wfh_data: pd.DataFrame = wfh_data
        
        # load data on closed workplaces
        nace2_lockdown_data = pd.read_csv(Path.joinpath(src.PATH, "data", "germany", "nace2_lockdown.csv"))
        nace2_lockdown_data = nace2_lockdown_data.set_index("nace2_short")
        self.nace2_lockdown_data: pd.DataFrame = nace2_lockdown_data
        
        # load data on reduced work hours
        nace2_short_reduction_of_workhours = pd.read_excel(Path.joinpath(src.PATH, "data", "germany", "nace2_short_reduction_of_workhours.xlsx"))
        nace2_short_reduction_of_workhours["quarter2"] = nace2_short_reduction_of_workhours["quarter2"] / (-100)
        nace2_short_reduction_of_workhours = nace2_short_reduction_of_workhours.set_index("nace2_short")
        self.nace2_short_reduction_of_workhours = nace2_short_reduction_of_workhours
        
        # load soep-data 
        soep = pd.read_csv(Path.joinpath(src.PATH, "data", "soep4sim", "soep_for_corona_simulation.csv"))
        self.soep: pd.DataFrame = soep[soep["federal_state"] == state]
        
        # average number of possible contacts / colleagues at work
        self.n_colleagues: int = 10
        
        # average number per kindergarten-group (variable name is misleading)
        self.kids_per_kindergarten: int = kids_per_kindergarten
        
        # maximum number of students per university
        self.students_per_university: int = 100000
        
        # number of hours kids visit kindergarten
        self.hours_at_kindergarten: int = 5
        
        # number of hours pupils visit school
        self.hours_at_school: int = 5
        
        # number of hours students visit university
        self.hours_at_university: int = 4
        
        # number of cells on x-axis (deprecated)
        self.grid_x_len: int = 100
        
        # number of cells on y-axis (deprecated)
        self.grid_y_len: int = 100
        
        # is the world a torus? (deprecated)
        self.torus: bool = True
        
        # skipped hours at night
        self.n_hours_timetravel = 6
        
        # simulated hours per day
        self.n_hours_per_day = 24 - self.n_hours_timetravel  
        
        # simulated time steps per hour
        self.n_ticks_per_hour = 1  
        
        # time steps per day
        self.n_ticks_per_day = self.n_ticks_per_hour * self.n_hours_per_day  
        
        # time when agents can leave the house
        self.day_time = range(8, 22)  
        
        # time steps per day
        self.n_ticks_per_day = self.n_ticks_per_hour * self.n_hours_per_day
        
        # time steps per school visit
        self.n_ticks_at_school = self.n_ticks_per_hour * self.hours_at_school
        
        # time steps per kindergarten visit
        self.n_ticks_at_kindergarten = self.n_ticks_per_hour * self.hours_at_kindergarten
        
        # time steps per university visit
        self.n_ticks_at_university = self.n_ticks_per_hour * self.hours_at_university
        
        # School age (6 - 19)
        self.school_age = range(6, 20)
        
        # Average number of pupils in a school
        self.pupils_per_school = self.school_data.loc[self.fed_states[self.state], "pupils/school"]
        
        # Average number of pupils in a school class
        self.pupils_per_class = self.school_data.loc[self.fed_states[self.state], "pupils/class"]
       
        # Kindergarten age (0 - 5)
        self.kindergarten_age = range(0, 6)
        
        # Number of agents per supermarket / store
        self.agents_per_supermarket = 1000
        
        # Number of supermarkets / stores an agent visits
        self.n_fav_supermarkets = 2
        
        # duration time of different infection states (from COVASIM (Kerr et al. 2020: 4))
        self.log_normal_duration_parameters = {
            "s": (4.6, 4.8),    
            "i": (1, 1),
            "r_a": (8, 2),
            "r_m": (8, 2),
            "r_s": (14, 2.4),
            "r_c": (14, 2.4),
            }
        
        # Age-dependent propability of developing symptoms during infection (from COVASIM (Kerr et al. 2020: 5))
        self.p_sym = {
            "0-9"  : 0.50,
            "10-19": 0.55,
            "20-29": 0.60,
            "30-39": 0.65,
            "40-49": 0.70,
            "50-59": 0.75,
            "60-69": 0.80,
            "70-79": 0.85,
            "80+"  : 0.90,
            }
        
        # storage for output data
        self.dict_of_output_data = {}
        self.latest_output_data = None
        

        ### data on infections & simulated dates & evaluation data for model calibration ###
        
        # load data on population size
        population_data = pd.read_excel(Path.joinpath(src.PATH, "data", "germany", "population_data.xlsx"))
        population_data["scale_to_100k"] = 100000 / population_data["population"]
        self.population_data = population_data.set_index("state")
        
        # load data on infections & merge with data on population
        df = pd.read_csv(Path.joinpath(src.PATH, "data", "germany", "RKI_COVID19_neu.csv"))
        df = pd.merge(df, population_data, how = "left", left_on = "Bundesland", right_on = "state_german")
        
        # filter by state ("dfs" = "df_state")
        dfs = df[df["Bundesland"] == self.fed_states_german[state]]
        
        # get datetime
        dfs["Meldedatum"] = pd.to_datetime(dfs["Meldedatum"])
        
        
        # get daily infections
        dfs = (dfs
               [["Meldedatum", "Bundesland", "AnzahlFall"]]
               .groupby(["Meldedatum", "Bundesland"])
               .sum()
               .reset_index()
               )
        
        # get daily cumulative cases
        dfs["cumulative_cases"] = dfs["AnzahlFall"].cumsum()
        
        # get date from datetime
        dfs["date"] = dfs["Meldedatum"].apply(lambda x: x.date())
        
        # create a list of dates within the relevant period of time
        dates = dates_between(dt.date(2020,3,1), dt.date(2020,9,15))
        
        # create a new dataframe with the list of dates
        dfs_eval = pd.DataFrame({"date": dates})
        
        # merge with data on infections and data on population size
        dfs_eval = pd.merge(
            dfs_eval, 
            dfs, 
            how="left", 
            on = "date",
            )
        dfs_eval = pd.merge(
            dfs_eval, 
            population_data, 
            how = "left", 
            left_on = "Bundesland", 
            right_on = "state_german",
            )
        
        # replace missing data by interpolation
        dfs_eval[["cumulative_cases", "scale_to_100k"]] = dfs_eval[["cumulative_cases", "scale_to_100k"]].interpolate()
        
        # compute empirical cases per 100k inhabitants
        dfs_eval["cumulative_cases/100k"] = dfs_eval["cumulative_cases"] * dfs_eval["scale_to_100k"]
        
        # find the day with approx. 50 infections per 100k inhabitants and set it as start date of the simulation
        dfs_eval["case_diff_to_start_date"] = abs(dfs_eval["cumulative_cases/100k"] - 50) # initial empirical infections
        start_date = (dfs_eval
                      [dfs_eval["case_diff_to_start_date"] == dfs_eval["case_diff_to_start_date"].min()]
                      ["Meldedatum"]
                      .reset_index(drop=True)
                      [0]
                      )
        
        # set end date of the simulation
        end_date = start_date + dt.timedelta(days = n_simulated_days - 1)
        
        # keep only data within the relevant dates
        dfs_eval = dfs_eval[dfs_eval["date"] >= start_date.date()]
        dfs_eval = dfs_eval[dfs_eval["date"] <= end_date.date()]
        dfs_eval = dfs_eval.reset_index()
        
        # create a list of infection data (for calibration)
        self.eval_data = list(dfs_eval["cumulative_cases/100k"])
        
        # create a dataframe of evaluation data with selected columns
        df_eval = dfs_eval[["date", "cumulative_cases", "cumulative_cases/100k"]]
        df_eval.columns = ["date", "empirical_cumulative_cases", "empirical_cumulative_cases/100k"]
        self.df_eval = df_eval
        
        # Date of the first day in the simulation
        self.start_datetime = start_date 
        
        # Date of the last day in the simulation
        self.end_datetime = end_date
    
    
    def build_n_buildings_of_a_certain_type_random_on_screen(
            self, 
            building_type, 
            n,
            world,
            ):
        for i in range(n):
            building = Building(building_type)
            building.build_it_on_random_position(
                world.grid_as_flat_list,
                world.grid_as_matrix,
                )
        

    def run(self, params):
        
        """
        This method runs the simulation model.
        
        INPUT
        list of parameter values
        
        params = [
            infection probability per hour (float),
            number of initial infections (int),
            number of agents (int),
            number of randomly infected agents per day (float or int),
            timetable of measures (dict),
            number of ticks until the household of symptomatic agents will be isolated (int),
            number of repetitions of the model run until the average result is calculated (int),
            name of the run (str),
            save output on disk? (bool),
            display simulation? (bool),
            ]
        
        OUTPUT
        output_dict: dictionary which contains 3 datasets
            df: main output dataframe
            calibration_data: list containg only the cumulative number of infections per day
            age_distributions: list of lists containing the age of all infected agents per internal run
        
        """
        
        start_time = time.time()
        
        # unpack list of parameters
        infection_prob, n_initial_infections, n, n_random_infections, timetable, n_ticks_to_quarantine, n_internal_runs, name_of_run, save_output, display_simulation = params
        
        assert 0 <= infection_prob <= 1
        assert n_initial_infections <= n
        assert type(timetable) == dict
        assert type(name_of_run) == str
        assert type(save_output) == bool
        assert type(display_simulation) == bool
        
        # create name of output file
        output_file_name = "output " + str(dt.datetime.now()).replace(":","-").replace(".","-") + ".csv"
        
        # Infection probabilities for each location type.
        # At the moment, the same probability applies to all locations.
        location_dependend_infection_prob_dict = {
            "home": infection_prob / self.n_ticks_per_hour,
            "street":infection_prob / self.n_ticks_per_hour,
            "supermarket": infection_prob / self.n_ticks_per_hour,
            "school": infection_prob / self.n_ticks_per_hour,
            "university": infection_prob / self.n_ticks_per_hour,
            "kindergarten": infection_prob / self.n_ticks_per_hour,
            "firm": infection_prob / self.n_ticks_per_hour,
            }
        for i in range(1, 22):
            location_dependend_infection_prob_dict.update(
                {"firm"+str(i):location_dependend_infection_prob_dict["firm"]}
                )
        
        # Desired number of agents
        self.N = int(n)
        
        # Population size of federal state
        empirical_population_size = self.population_data.loc[self.fed_states[self.state],"population"]
        
        # Lists for storing outputdata of multiple repetitions of simulation
        list_of_scaled_cum_infections = []
        output_dataframes = []
        age_distributions = []
        
        # run all replications of the simulation
        with WorkerPool(n_jobs=self.n_cores, use_dill=True) as pool:
            output_dicts = pool.map(
                lambda x: self.internal_run(
                    n_agents = self.N,
                    location_dependend_infection_prob_dict = location_dependend_infection_prob_dict,
                    simulation_run = 999,
                    n_initial_infections = int(n_initial_infections),
                    n_random_infections = n_random_infections,
                    timetable = timetable,
                    n_ticks_to_quarantine = n_ticks_to_quarantine,
                    display_simulation=display_simulation,
                    ),
                    range(n_internal_runs)
                )
  
        # calculate average results for calibration purposes
        avg_scaled_cumulative_cases = [sum(t)/len(t) for t in zip(*list_of_scaled_cum_infections)]

        # append df to list
        output_dataframes = [output_dict["cases"] for output_dict in output_dicts]
            
        # append data on adj. cases / 100k as a list to a list (for calibration)
        list_of_scaled_cum_infections = [list(df["adj_cumulative_cases/100k"]) for df in output_dataframes]
            
        # calculate average results for calibration purposes
        avg_scaled_cumulative_cases = [sum(t)/len(t) for t in zip(*list_of_scaled_cum_infections)]


        # create main dataframe
        output_dataframe = pd.concat(output_dataframes)
        output_dataframe["date"] = output_dataframe["datetime"].apply(lambda x: x.date())
        output_dataframe = output_dataframe.merge(self.df_eval, on="date")
        output_dataframe["name_of_run"] = name_of_run
        
        # measure computation time
        end_time = time.time()
        output_dataframe["start_time"] = start_time
        output_dataframe["end_time"] = end_time
        output_dataframe["duration_time"] = end_time - start_time
        
        # save main dataframe as csv & data on age distributions as pickle
        if save_output:
            output_file_name = Path.joinpath(src.PATH, "output_data", "output_" + name_of_run + ".csv")
            output_dataframe.to_csv(output_file_name, index = False)
            # pickle.dump(age_distributions, open("output_data/infagedist_" + name_of_run + ".p", "wb"))
        
        # save results as an attribute of the model
        self.latest_output_data = output_dataframe
        self.dict_of_output_data.update({name_of_run:output_dataframe})
        
        # create a dict containing all outputs
        output_dict = {
            "df": output_dataframe, # main output dataframe
            "calibration_data": avg_scaled_cumulative_cases, # data for calibration
            "age_distributions": age_distributions,
            }

        if save_output:
            # save simple plot
            g = sns.lineplot(data=output_dataframe, x="day", y="adj_cumulative_cases/100k")
            g = g.get_figure()
            g.savefig(Path.joinpath(src.PATH, "output_data", "graph_" + name_of_run + ".pdf"))
    
        return output_dict
    
    
    def internal_run(
            self,
            n_agents,
            location_dependend_infection_prob_dict: dict,
            simulation_run: int,
            n_ticks_to_quarantine,
            n_initial_infections,
            n_random_infections,
            timetable,
            display_simulation,
        ):
        
        """
        This method runs the simulation internally. 
        For each model repetition, this method is executed one time by the method "run()".
        """

        # create population
        agent_population_in_households = self.create_soep_population(
            N = self.N,
            agent_class = Agent,
        )
        
        # Count agents
        population_size = sum([1 for household in agent_population_in_households for agent in household])
        
        # Calculate scaling factor to empirical population size of federal state
        #scale_to_population = empirical_population_size / population_size
        
        # Count pupils
        n_pupils = sum([1 for household in agent_population_in_households for agent in household
                        if agent.age in self.school_age])
        
        # Count kindergarten kids
        n_kindergarten_kids = sum([1 for household in agent_population_in_households for agent in household
                        if agent.age in self.kindergarten_age])
        
        # Count university students
        n_students = sum([1 for household in agent_population_in_households for agent in household
                        if agent.student])
        
        # Calculate number of schools needed
        n_schools = max(n_pupils // self.pupils_per_school, 1)
        
        # Calculate number of supermarkets / stores needed
        n_supermarkets = max(population_size // self.agents_per_supermarket, 1)
        
        # Calculate number of Kindergarten(groups) needed
        n_kindergartens = max(n_kindergarten_kids // self.kids_per_kindergarten, 1)
        
        # Calculate number of universities needed
        n_universities = max(n_students // self.students_per_university, 1)
        
        # Count number of Nace2-sectors in agent population and save it in df
        n_nace2 = [agent.nace2_short for household in agent_population_in_households for agent in household]
        n_nace2 = pd.DataFrame(
            pd.Series(n_nace2).value_counts(), 
            columns = ["freq_in_simpop"]
            )
    
        # create world
        world = World(self.grid_x_len, self.grid_y_len)
        world.create_grid(Cell)
    
        # create agent population
        world.agents.update({"agents": []})
    
        families = agent_population_in_households
        

        #######################################################################
        # build locations
        #######################################################################
        
        """
        In this and the following sections, the locations of the simulated world are created. 
        Each location is a cell on a grid, which itself can have several "rooms". 
        An agent is assigned to a location and a room within the location. 
        This design was once implemented to model realistic traffic flows, 
        e.g. to have many agents travel to the same school but split into different classrooms. 
        However, this version of the simulation does not model movement between places anyway, 
        so this implementation does not really make sense. 
        It is retained, however, in order to reintroduce movement flows if necessary.
        
        """
        
        # build supermarkets
        self.build_n_buildings_of_a_certain_type_random_on_screen("supermarket", n_supermarkets, world)
        
        # build schools
        self.build_n_buildings_of_a_certain_type_random_on_screen("school", n_schools, world)
    
        # build kindergartens (at the moment these are in fact kindergarten groups)
        self.build_n_buildings_of_a_certain_type_random_on_screen("kindergarten", n_kindergartens, world)
        
        # build universities
        self.build_n_buildings_of_a_certain_type_random_on_screen("university", n_universities, world)
        
        # build one firm for each nace2-sector 
        for nace2 in n_nace2.index:
            if nace2 != "-1":
                # Firmen bauen
                self.build_n_buildings_of_a_certain_type_random_on_screen("firm" + str(nace2), 1, world)
        
        # find all cells without buildings
        vacant_ground = [cell
                         for cell in world.grid_as_flat_list
                         if cell.cell_type == "street"]
        
        # build houses/homes
        self.build_n_buildings_of_a_certain_type_random_on_screen(
                "home", 
                len(vacant_ground),
                world,
        )
    
        #######################################################################
        # assign agents to homes
        #######################################################################
        
        # get all homes
        list_of_houses = [cell 
                          for cell in world.grid_as_flat_list
                          if cell.cell_type == "home"]
        
        # for each household
        for family in families:
            
            # get empty homes
            list_of_vacant_houses = [cell 
                                     for cell in world.grid_as_flat_list
                                     if cell.cell_type == "home"
                                     and cell.n_groups == 0]
            
            # if there are any empty homes
            if len(list_of_vacant_houses) > 0:
                
                # randomly assign household to an empty home
                house = random.choice(list_of_vacant_houses)
            
            else:
                
                # randomly assign household to a flat within a multi-family house
                house = random.choice(list_of_houses)
            
            # get flat id
            flat = house.n_groups
                
            # increase number of flats in the house
            house.n_groups += 1
                
            # for each household, move in flat/house
            for agent in family:
                agent.move_in(house)
                agent.home_cell = house
                agent.group_dict.update({"home":flat})
                
                # add household/family members to agent's list of household members
                for family_member in family:
                    if family_member != agent:
                        agent.household_members.append(family_member)
                
                # add each agent to the world's population list
                world.agents["agents"].append(agent)
                
        #######################################################################
        # assign supermarkets to agents
        #######################################################################
        
        # get all supermarkets
        list_of_supermarkets = [cell 
                                for cell in world.grid_as_flat_list
                                if cell.cell_type == "supermarket"]
        
        # randomly assign supermarkets
        for agent in world.agents["agents"]:
            agent.group_dict.update({"supermarket": 0})
            agent.fav_supermarkets = []
            for i in range(self.n_fav_supermarkets):
                agent.fav_supermarkets.append(random.choice(list_of_supermarkets))
            
            
        #######################################################################
        # assign schools/classes to agents
        #######################################################################

        # get all schools
        list_of_schools = [cell 
                           for cell in world.grid_as_flat_list
                           if cell.cell_type == "school"]
        
        # for each pupil
        for agent in world.agents["agents"]:
            if agent.age in self.school_age:
                
                # select random school
                school = random.choice(list_of_schools)
                agent.school = school
                
                # increase number of pupils in this school
                school.n_users += 1
    
    
        # for each school
        for school in list_of_schools:
            
            # calculate number of necessary classes
            school.n_groups = max(school.n_users // self.pupils_per_class, 1)
    
    
        # for each agent
        for agent in world.agents["agents"]:
            
            # if assigned to school 
            if agent.school:
                
                # randomly assign to a class
                agent.group_dict.update({"school": random.choice(range(agent.school.n_groups))})
        
        # This process could be optimized.
        
    
        #######################################################################
        # assign kindergartens
        #######################################################################
        
        """
        One kindergarten building contains only one group/room.
        Thus, a kindergarten is in fact only a kindergarten group.
        This does not matter for the simulation results.
        It would be relevant and should be changed, if the traffic flows
        were modelled.
        """
        
        # select all built kindergartens
        list_of_kindergartens = [cell 
                                 for cell in world.grid_as_flat_list
                                 if cell.cell_type == "kindergarten"]
    
        # for each agent
        for agent in world.agents["agents"]:
    
            # if agent's age is of kindergarten age
            if agent.age in self.kindergarten_age:
                
                # select random kindergarten
                kindergarten = random.choice(list_of_kindergartens)
    
                # save kindergarten as an agent property
                agent.kindergarten = kindergarten
    
                # assign kindergarten group
                agent.group_dict.update({"kindergarten": 0})
    
        #######################################################################
        # assign work places
        #######################################################################
        
        # get all workplaces
        all_firms = [
            cell 
            for cell in world.grid_as_flat_list
            if "firm" in cell.cell_type
            ]
        
        # for each working agents
        for agent in world.agents["agents"]:
            if agent.work_hours_day_in_ticks > 0:
            
                # get all possible workplaces within the agent's nace2-sector
                possible_work_places = [
                    cell 
                    for cell in all_firms
                    if cell.cell_type == "firm" + str(agent.nace2_short)
                    ]
                
                # choose a workplace
                work_place = random.choice(possible_work_places)
                agent.work_place = work_place
                
                # increase number of workers assigned to this workplace
                work_place.n_users += 1
            
                
        # for each workplace
        for firm in all_firms:
            # calculate number of divisions within work place
            firm.n_groups = max(firm.n_users // self.n_colleagues, 1)
    
        # for each agent with a work place
        for agent in world.agents["agents"]:
            if agent.work_place:
               
                # randomly assign division with work place
                agent.group_dict.update(
                    {agent.work_place.cell_type: random.choice(range(agent.work_place.n_groups))}
                    )
                           
        #######################################################################
        # assign universities
        #######################################################################
        
        # get all universities
        list_of_universities = [
            cell 
            for cell in world.grid_as_flat_list
            if cell.cell_type == "university"
            ]
        
        # for each agents
        for agent in world.agents["agents"]:
            # if agent is student
            if agent.student == 1:
                # randomly assign a university
                agent.university = random.choice(list_of_universities)
                agent.group_dict.update({"university": 0})
        
        #######################################################################
        # infection characteristics
        #######################################################################
        
        def get_value_from_lognormal_dist(par1, par2):
                # transform mean and sd
                # (taken from covasim)
                mean  = np.log(par1**2 / np.sqrt(par2 + par1**2)) # Computes the mean of the underlying normal distribution
                sigma = np.sqrt(np.log(par2/par1**2 + 1)) # Computes sigma for the underlying normal distribution
                
                value = np.random.lognormal(mean, sigma) * self.n_ticks_per_day
                return value
        
        # duration of different stages of infection as parameters (m, sd) of a log-normal distribution
        lndp = self.log_normal_duration_parameters
        
        for agent in world.agents["agents"]:
            agent.duration_s = get_value_from_lognormal_dist(lndp["s"][0], lndp["s"][1]) 
            agent.duration_i = get_value_from_lognormal_dist(lndp["i"][0], lndp["i"][1]) 
            agent.duration_r_a = get_value_from_lognormal_dist(lndp["r_a"][0], lndp["r_a"][1])
            agent.duration_r_m = get_value_from_lognormal_dist(lndp["r_m"][0], lndp["r_m"][1]) 
        
            # age-related probabilities of developing symptoms after an infection
            if agent.age in range(0,10):
                agent.p_sym = self.p_sym["0-9"]
            elif agent.age in range(10, 20):
                agent.p_sym = self.p_sym["10-19"]
            elif agent.age in range(20, 30):
                agent.p_sym = self.p_sym["20-29"]
            elif agent.age in range(30, 40):
                agent.p_sym = self.p_sym["30-39"]
            elif agent.age in range(40, 50):
                agent.p_sym = self.p_sym["40-49"]
            elif agent.age in range(50, 60):
                agent.p_sym = self.p_sym["50-59"]
            elif agent.age in range(60, 70):
                agent.p_sym = self.p_sym["60-69"]
            elif agent.age in range(70, 80):
                agent.p_sym = self.p_sym["70-79"]
            elif agent.age >= 80:
                agent.p_sym = self.p_sym["80+"]
        
        
        #######################################################################
        # initial infections & first count
        #######################################################################
        
        new_cases = 0
        cumulative_cases = 0
        new_cases_age = 0
        cumulative_cases_age = 0
        n_inf_age_0_29 = 0
        n_inf_age_30_59 = 0
        n_inf_age_60 = 0        

        # container for storing generated output data
        output_data = []
        
        infected_agents = random.sample(world.agents["agents"], n_initial_infections)
        for agent in infected_agents:
            agent.infection = "i"
            agent.tick_of_infectivity = 0
            agent.tick_of_exposure = 0
            agent.cell_of_infection = random.choice(world.grid_as_flat_list)
            
            new_cases += 1
            cumulative_cases += 1
            
            new_cases_age += agent.age
            cumulative_cases_age += agent.age
            
            if agent.age <= 29:
                n_inf_age_0_29 += 1
            elif 30 <= agent.age <= 59:
                n_inf_age_30_59 += 1
            else:
                n_inf_age_60 += 1
        
        todays_infection_data =  {
            "group": self.state,
             "run": simulation_run,
             "tick": 0,
             "day": 0,
             "datetime": self.start_datetime,
             "new_cases": 50,
             "cumulative_cases": 50,
             "new_cases_age": new_cases_age,
             "cumulative_cases_age": cumulative_cases_age,
             "n_inf_age_0_29" : n_inf_age_0_29,
             "n_inf_age_30_59": n_inf_age_30_59,
             "n_inf_age_60": n_inf_age_60,
             #"scale_to_population": scaling_factor,
             "scale_to_100k": 100000 / len(world.agents["agents"]),
            }
        output_data.append(todays_infection_data)
        
        # reset daily case numbers
        new_cases = 0
        new_cases_age = 0
        
        #######################################################################
        # time
        #######################################################################
        
        tick = 0
        
        # clock time in simulation
        simulation_clock_time = 0
        
        # days passed in simulation since start of simulation
        simulation_day = 0
        
        current_datetime = self.start_datetime
        weekday = current_datetime.weekday()
        
        sim_len = self.end_datetime - self.start_datetime
        days= sim_len.days
        hours = days * self.n_hours_per_day
        max_ticks = hours * self.n_ticks_per_hour
        
        
        # get the current plan of measures (evtl. noch Funktion drauß machen, weil später nochmal verwendet)
        # ACHTUNG BENÖTIGT AKTUELLES PYTHON (>= 3.7), da Dicts geordnet sein müssen
        for datetime_key in timetable:
            if datetime_key <= current_datetime:
                current_measures = timetable[datetime_key]
        
        
        #######################################################################
        # simulation loop
        #######################################################################
        
        simulate = True
        
        # for each time step in simulation
        for tick in range(max_ticks):
            
            # one hour step
            current_datetime_temp = current_datetime
            current_datetime = current_datetime + dt.timedelta(hours = 1)
            
            # when it is 1 a.m.
            if current_datetime.hour == 1:
                # jump forward in time
                current_datetime = current_datetime + dt.timedelta(hours = self.n_hours_timetravel)
                
            
            # set clock time
            simulation_clock_time = current_datetime.hour
            
            # when a new day begins
            if current_datetime_temp.day != current_datetime.day:
                
                # increase day counter
                simulation_day += 1
                
                # set weekday
                weekday = current_datetime.weekday()
                
                # collect data
                todays_infection_data =  {
                    "group": self.state,
                     "run": simulation_run,
                     "tick": tick,
                     "day": simulation_day,
                     "datetime": current_datetime, # today
                     "new_cases": new_cases,
                     "cumulative_cases": cumulative_cases,
                     "new_cases_age": new_cases_age,
                     "cumulative_cases_age": cumulative_cases_age,
                     "n_inf_age_0_29" : n_inf_age_0_29,
                     "n_inf_age_30_59": n_inf_age_30_59,
                     "n_inf_age_60": n_inf_age_60,
                     #"scale_to_population": scaling_factor,
                     "scale_to_100k": 100000 / len(world.agents["agents"]),
                    }
                    
                output_data.append(todays_infection_data)
               
                new_cases = 0
                new_cases_age = 0
                
                infection_states = [agent.infection for agent in world.agents["agents"]]
                n_infectious = (infection_states.count("e") + 
                                infection_states.count("i") + 
                                infection_states.count("a") + 
                                infection_states.count("m")
                                )
                
                # if the virus is dead, stop the simulation
                if n_infectious == 0 and n_random_infections == 0:
                    simulate = False
                
                
                # shuffle list of agents
                random.shuffle(world.agents["agents"])
                
                # empty agents' list of activities done today
                for agent in world.agents["agents"]:
                    agent.activities_done_today = []
                
                # get the current plan of measures
                for datetime_key in timetable:
                    if datetime_key <= current_datetime:
                        current_measures = timetable[datetime_key]
                
                # random infections
                if n_random_infections < 1:
                    temp = (1 if random.random() < n_random_infections else 0)
                else:
                    temp = n_random_infections
                
                for i in range(round(temp)):
                    random_agent = random.choice(world.agents["agents"])
                    if random_agent.infection == "s":
                        random_agent.infection = "e"
                        random_agent.tick_of_exposure = tick
                        random_agent.cell_of_infection = random_agent.residence_cell
                
                            
            #######################################################################    
            # FOR-LOOP AGENTS        
            #######################################################################
            
            if simulate:
            
                # for each agent
                for agent in world.agents["agents"]:
                    
                    # get and temporalily save current status of infection
                    infection_status_temp = agent.infection
                    
                    # internally update agent's status of infection
                    agent.update_status_of_infection(tick)
                    
                    # if the status of infection just changed from not symptomatic/asymptomatic to symptomatic/asympotmatic
                    if infection_status_temp not in ("a", "m") and agent.infection in ("a", "m"):
                        
                        # increase number of (cumulative) cases
                        new_cases += 1
                        cumulative_cases += 1
                        
                        new_cases_age += agent.age
                        cumulative_cases_age += agent.age
                        
                        if agent.age <= 29:
                            n_inf_age_0_29 += 1
                        elif 30 <= agent.age <= 59:
                            n_inf_age_30_59 += 1
                        else:
                            n_inf_age_60 += 1
                        
                    
                    # infect other agents (maybe)
                    agent.infect(tick, location_dependend_infection_prob_dict)
                    
                    # decide whether to stay at home due to symptoms/illness
                    agent.decide_to_stay_at_home(tick, self.n_ticks_per_day)
                    
                    # if household isolation is part of the current action plan
                    if current_measures["quarantine"] == "household":
                        
                        # decide whether to isolate the whole own household due to own symptoms
                        agent.decide_to_isolate_household(tick, n_ticks_to_quarantine)
                    
                    
                    # on workdays
                    if weekday < 5:
                        # if agent does not stay at home
                        if not agent.stay_at_home:
                        
                            # at 8 o'clock
                            if simulation_clock_time == 8:
                                
                                # if agent is a worker
                                if agent.work_hours_day_in_ticks > 0:
                                    
                                    assert 0 <= self.wfh_data[current_measures["wfh"]][agent.nace2] <= 1
                                    assert 0 <= self.nace2_lockdown_data[current_measures["nace2_lockdown"]][agent.nace2_short] <= 1
                                    assert 0 <= self.nace2_short_reduction_of_workhours[current_measures["nace2_reduction_of_workhours"]][agent.nace2_short] <= 1
                                    
                                    # "work at home" if "homeoffice" or "closure of workplace" or "work at home"
                                    if (    # homeoffice?
                                            random.random() < self.wfh_data[
                                                current_measures["wfh"]][agent.nace2] or
                                        
                                            # closure of workplace?
                                            random.random() < self.nace2_lockdown_data[
                                                current_measures["nace2_lockdown"]][agent.nace2_short] or
                                        
                                            # short time work?
                                            random.random() < self.nace2_short_reduction_of_workhours[
                                                current_measures["nace2_reduction_of_workhours"]][agent.nace2_short]
                                        ):
                                        
                                        # work at home
                                        agent.initialize_activity(
                                            "at_work",
                                            agent.home_cell,
                                            agent.work_hours_day_in_ticks,
                                            overwrite=True,
                                        )
                                    
                                    else:
                                        # go to work
                                        agent.initialize_activity(
                                            "at_work",
                                            agent.work_place,
                                            agent.work_hours_day_in_ticks,
                                            overwrite=True,
                                        )
                
                                # if agent is a school kid
                                elif agent.school:
                                    
                                    # if schools are open
                                    if random.random() < current_measures["school"]:
                                        
                                        # go to school
                                        agent.initialize_activity(
                                            "at_school",
                                            agent.school,
                                            self.n_ticks_at_school,
                                            overwrite=True,
                                        )
                                
                                # if agent is a kindergarten kid
                                elif agent.kindergarten:
                                    
                                    # if kindergartens are open
                                    if random.random() < current_measures["kindergartens"]:
                                    
                                        # go to kindergarten
                                        agent.initialize_activity(
                                            "at_kindergarten",
                                            agent.kindergarten,
                                            self.n_ticks_at_kindergarten,
                                            overwrite=True,
                                        )
                            
                            
                            if not agent.activity: 
                                
                                if simulation_clock_time in self.day_time:
                                
                                    # go to university
                                    if agent.student:
                                        if random.random() < current_measures["university"]:
                                            if "at_university" not in agent.activities_done_today:
                                                agent.initialize_activity(
                                                    "at_university",
                                                    agent.university,
                                                    self.n_ticks_at_university,
                                                )
                            
                                    # shopping (from monday to friday)             
                                    if agent.age >= 14:
                                        # if supermarkets are open
                                        if random.random() < current_measures["supermarkets"]:
                                            # if agent has not shopped today
                                            if "shopping" not in agent.activities_done_today:
                                                # go shopping
                                                agent.initialize_activity(
                                                    "shopping",
                                                    random.choice(agent.fav_supermarkets),
                                                    agent.hours_at_supermarket_in_ticks,
                                                )
                                            else:
                                                agent.activities_done_today.append("shopping")
                        
                    # execute initialized activity
                    agent.do_activity(
                        world.len_x_grid_dim,
                        world.len_y_grid_dim,
                        world.grid_as_matrix,
                        self.torus,
                    )
        
        
        # create dataframe containing the simulated data on infections
        df = pd.DataFrame(output_data)
        
        # calculate cases / 100k
        df["cumulative_cases/100k"] = df["cumulative_cases"] * df["scale_to_100k"]
        
        # adjust number of cases so that the first simulated number (50) equals the first empirical number (approx. 50)
        df["adj_cumulative_cases/100k"] = df["cumulative_cases/100k"] - (df["cumulative_cases/100k"][0] - self.eval_data[0])
        

        age_of_infected_agents = [
            agent.age 
            for agent in world.agents["agents"]
            if agent.infection in ("e", "i", "m", "a", "r")
            ]
        
        output_dict = {
            "age_of_infected_agents": age_of_infected_agents,
            "cases": df,
            }


        return output_dict


    def create_soep_population(self, N: int, agent_class: Agent) -> List[List[Agent]]:
        """
        This method creates the population of agents informed by the SOEP.
        """
        
        # all NACE codes
        nace2_codes = [
            1,2,3,5,6,7,8,9,
            10,11,12,13,14,15,16,17,18,19,
            20,21,22,23,24,25,26,27,28,29,
            30,31,32,33,35,36,37,38,39,
            41,42,43,45,46,47,49,
            50,51,52,53,55,56,58,59,
            60,61,62,63,64,65,66,68,69,
            70,71,72,73,74,75,77,78,79,
            80,81,82,84,85,86,87,88,
            90,91,92,93,94,95,96,97,98,99,
            ]

        # get unique household-IDs and corresponding weight
        hids_and_weights = self.soep.drop_duplicates(subset=["hid"]).loc[:, ["hid", "bhhhrf"]]
        
        # list for storing all weighted household-ids
        weighted_hids = []
        
        # for each household
        for i in hids_and_weights.index:
            
            # get household id
            hid = hids_and_weights.loc[i, "hid"]
            
            # get houshold weight
            weight = int(hids_and_weights.loc[i, "bhhhrf"])
            
            # create a list containing the household id "weigth" times
            weighted_hid = [hid] * weight
            
            # add it to the list of all weighted household ids
            weighted_hids.extend(weighted_hid)
            
    
        # list for saving agents in households
        households = []
        
        # population size counter 
        n = 0
        
        # while actual population size is smaller than desired population size
        while n < N:
            
            # choose a random household-ID from the weighted list of IDs
            hid = random.choice(weighted_hids)
    
            # get data of persons living in this household
            household_data = self.soep[self.soep["hid"] == hid].reset_index()
            
            # list for storing agents created below
            household = []
            
            # for each agent/row in household/data
            for i in household_data.index:
                
                # create new agent instance
                agent = agent_class()
    
                # copy attributes from soep to agent
                
                # age
                agent.age = household_data.loc[i, "age"]
                
                # gender
                agent.gender = household_data.loc[i, "gender"]
                
                # NACE2 code
                nace2 = household_data.loc[i, "nace2"]
                # if ambiguous (nace2<=0), choose a random nace2-category
                agent.nace2 = (random.choice(nace2_codes) if nace2 <= 0 else nace2)
                
                # NACE2 section
                nace2_short = household_data.loc[i, "nace2_short"]
                # if ambiguous (nace2<=0), choose a random nace2-short-category
                agent.nace2_short = (random.randint(1, 21) if nace2 <= 0 else nace2_short) 
                
                # work hours
                agent.work_hours_day_in_ticks = household_data.loc[i, "computed_work_hours_day"] * self.n_ticks_per_hour
                
                # shopping hours
                agent.hours_at_supermarket_in_ticks = household_data.loc[i, "hours_shopping_mi"] * self.n_ticks_per_hour
                
                # student status
                agent.student = household_data.loc[i, "student"]
                
                # household id
                agent.hid = household_data.loc[i, "hid"]
                
                # personal id
                agent.pid = household_data.loc[i, "pid"]
                
                # federal state
                agent.federal_state = household_data.loc[i, "federal_state"]
                
                # append Agent to household-list
                household.append(agent)
            
            # append household to list of all households
            households.append(household)
            
            # increase the number of already created instances
            n += len(household)
        
        # return list of households
        return households
