import random
from typing import Optional

from src.sim.cell import Cell


class Agent:
    max_agents_on_cell: Optional[int] = None
    moving_prob: Optional[float] = None

    def __init__(self):

        # id
        self.name = id(self)

        # the cell where the agent is at the moment
        self.residence_cell: Optional[Cell] = None
        
        # the agent's position on the grid as coordinates
        self.x_grid_pos: Optional[int] = None
        self.y_grid_pos: Optional[int] = None
        
        # population list
        self.population = list

        # gender
        self.gender: Optional[int] = None
        
        # age
        self.age: Optional[int] = None
        
        # SEIR-state
        self.infection: str = "s"                    
        
        # time step when infection happened
        self.tick_of_exposure: Optional[int] = None             
        
        # time step when agent was cured
        self.tick_of_recovery: Optional[int] = None
        
        # time step of (A-)Symptomaticity
        self.tick_of_symptom_onset: Optional[int] = None
        
        # where the agent lives
        self.home_cell: Optional[Cell] = None
        
        # other locations
        self.work_place = None                  
        self.school = None                      
        self.kindergarten = None                
        self.fav_supermarkets = []

        # location where the infection happend
        self.cell_of_infection = None          
        
        # temporary destinations during activities
        self.target_cell = None           
        
        # name of activity the agent is doing
        self.activity = None
        
        # planned execution time of activity in time steps
        self.activity_len_in_ticks = None
        
        # time steps the agent has executed the activity so far
        self.ticks_doing_this_activity = None
        
        # dictionary of rooms assigned to the agent in certain locations
        # key = location; value = room
        self.group_dict = {"street": 0}
        
        # list of activities an agent has done during the day
        self.activities_done_today = []
        
        # Does the agent leave the house?
        self.stay_at_home = False
        
        # Is the agent in quarantine?
        self.quarantine = False
        
        # list of agents living with the agent
        self.household_members = []
        
        # time spans of stages of infections (in ticks)
        self.duration_s = None 
        self.duration_i = None 
        self.duration_r_a = None 
        self.duration_r_m = None 



    def move_in(self, new_residence_cell):
        self.residence_cell = new_residence_cell                        
        self.residence_cell.dict_of_residents.update({self.name: self}) 
        self.x_grid_pos = self.residence_cell.x_grid_pos   
        self.y_grid_pos = self.residence_cell.y_grid_pos


    def move_out(self):
        del(self.residence_cell.dict_of_residents[self.name]) 
        self.residence_cell = None            
        self.x_grid_pos = None                 
        self.y_grid_pos = None                 


    def move_to_this_cell(self, new_residence_cell):
        self.move_out()                     
        self.move_in(new_residence_cell)   


    def infect(self, tick: int, location_dependend_infection_prob_dict: dict):
        """
        Models the potential tranmission of the virus.
        If this agent is infectious, it randomly chooses another agent that is
        currently in the same room at the same location and infects the chosen agent
        by a certain probability.
        """

        # if agent is in any infectious state and if the agent is not the only one on his cell
        if self.infection in ["i", "a", "m"] and len(self.residence_cell.dict_of_residents) > 1:
            
            # get type of current location
            location = self.residence_cell.cell_type

            # get all agents on my cell in my group/room
            agents_in_my_group = [
                agent
                for agent in list(self.residence_cell.dict_of_residents.values())
                if agent.group_dict[location] == self.group_dict[location] and agent != self
                ]

            # if there are other agents in the same group/room
            if len(agents_in_my_group) > 0:
                
                # pick one agent at random
                random_agent = random.choice(agents_in_my_group)
                
                # if the chosen agent is susceptible
                if random_agent.infection == "s":
                    
                    # expose the selected agent with a certain probability
                    if random.random() < location_dependend_infection_prob_dict[location]:
                        random_agent.infection = "e"
                        random_agent.tick_of_exposure = tick
                        random_agent.cell_of_infection = self.residence_cell
                
                
    def update_status_of_infection(self, tick):
        """
        Updates the status on infection each tick.
        Changes the status on infection
        from exposed (e) 
        to infectious (i)
        to symptomatic infectius (m) or asymptomatic infectious (a)
        to recovered (r).
        """
        
        # if agent has been exposed but is not yet infectious
        if self.infection == "e":
            
            if tick - self.tick_of_exposure >= self.duration_s:
                self.infection = "i"
                self.tick_of_infectivity = tick

        # if agent is currently infectious
        elif self.infection == "i":
            if tick - self.tick_of_infectivity > self.duration_i:
                self.tick_of_symptom_onset = tick
                
                # develop symptoms by an agent specific probability
                if random.random() < self.p_sym:
                    
                    # develop mild symptoms
                    self.infection = "m"
                    
                else:
                    # asymptomatic
                    self.infection = "a"
        
        # if agent is asymptomatic infected
        elif self.infection == "a":
            if tick - self.tick_of_symptom_onset > self.duration_r_a:
                self.infection = "r"
                self.tick_of_recovery = tick
        
        # if agent is infected with mild symptoms
        elif self.infection == "m":
            
            if tick - self.tick_of_symptom_onset > self.duration_r_m:
                self.infection = "r"
                self.tick_of_recovery = tick
            
    
    
    def decide_to_stay_at_home(self, tick, ticks_to_staying_at_home):
        """
        If an Agent has developed symptoms, it decides to stay at home after
        a given time span has passed since the onset of the symptoms. 
        It models the common behavior of people to stay at home when not feeling well.
        """
        
        # if agent has symptoms
        if self.infection in ["m"]:
            
            # wait until the number of ticks since symptom onset is higher than "ticks_to_staying_at_home"
            if tick - self.tick_of_symptom_onset >= ticks_to_staying_at_home:
                self.stay_at_home = True
        
        else:
            self.stay_at_home = False
        
            
    
    
    def decide_to_isolate_household(self, tick, ticks_to_isolate_household):
        """
        If an agent has symptoms for a while, the whole household gets isolated.
        If an agent is in quarantine, it stays at home for 14 days.
        """
        # if one has symptoms and is not yet in quarantine
        if self.infection in ["m"] and not self.quarantine:
            
            # wait until some time has passed since symptom onset
            if tick - self.tick_of_symptom_onset >= ticks_to_isolate_household:
                
                # isolate household
                self.tick_of_quarantine = tick
                self.quarantine = True
                
                for member in self.household_members:
                    member.tick_of_quarantine = tick
                    member.quarantine = True
                    
        
        # if one is already in quarantine 
        if self.quarantine:
            if tick - self.tick_of_quarantine < 252: # 14 days * 18 daily ticks
                self.stay_at_home = True
            else:
                self.stay_at_home = False
                self.quarantine = False
            


    def initialize_activity(
            self,
            name_of_activity,       
            target_cell,            
            activity_len_in_ticks,  
            overwrite = False,

    ):
        """Initializes an activity."""
        
        # if the agent is doing nothing or this activity is allowed to overwrite the current activity
        if (not self.activity) or overwrite:
            self.activity = name_of_activity
            self.target_cell = target_cell
            self.activity_len_in_ticks = activity_len_in_ticks
            self.ticks_doing_this_activity = 0
            
            if name_of_activity not in self.activities_done_today:
                self.activities_done_today.append(name_of_activity)
            
            
    def do_activity(
            self,
            len_x_grid_dim,
            len_y_grid_dim,
            grid_as_matrix,
            torus,
    ):
        """Executes the current activity."""

        # if an activity is intialized
        if self.activity:
            
            # if the agent is not at the right location
            if self.target_cell:
                # go to the location
                self.move_to_this_cell(self.target_cell)
                self.target_cell = None
             
            # if the planned execution time has not been reached
            if self.ticks_doing_this_activity < self.activity_len_in_ticks:
                self.ticks_doing_this_activity += 1

            # if the planned execution time has been reached
            else:
                # stop the activity and go home
                self.move_to_this_cell(self.home_cell)
                self.activity = None
                self.ticks_doing_this_activity = None
                self.activity_len_in_ticks = None