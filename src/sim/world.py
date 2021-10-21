from src.sim.cell import Cell
from src.sim.helper import *

class World:
    def __init__(
        self,
        len_x_grid_dim: int,
        len_y_grid_dim: int,
        ):

        self.len_x_grid_dim = len_x_grid_dim
        self.len_y_grid_dim = len_y_grid_dim

        self.half_x_grid_dim = int(self.len_x_grid_dim / 2)
        self.half_y_grid_dim = int(self.len_y_grid_dim / 2)

        self.grid_as_matrix: List[List[Cell]] = [[]]
        self.grid_as_flat_list: List[Cell] = []

        self.NW_grid_as_flat_list: List[Cell] = []
        self.NE_grid_as_flat_list: List[Cell] = []
        self.SW_grid_as_flat_list: List[Cell] = []
        self.SE_grid_as_flat_list: List[Cell] = []

        self.agents: dict = {}


    def create_grid(self, cell_class: int = "standard"):

        self.grid_as_matrix = []
        self.grid_as_flat_list = []

        for y in range(self.len_y_grid_dim):
            row = []

            for x in range(self.len_x_grid_dim):

                if cell_class == "standard":
                    cell = Cell(x, y)
                else:
                    cell = cell_class(x, y)

                row.append(cell)

                self.grid_as_flat_list.append(cell)

                if x < self.half_x_grid_dim:
                    if y < self.half_y_grid_dim:
                        self.NW_grid_as_flat_list.append(cell)
                    else:
                        self.SW_grid_as_flat_list.append(cell)
                else:
                    if y < self.half_y_grid_dim:
                        self.NE_grid_as_flat_list.append(cell)
                    else:
                        self.SE_grid_as_flat_list.append(cell)


            self.grid_as_matrix.append(row)


    def get_empty_cells(self):
        empty_cells = [cell for cell in self.grid_as_flat_list if len(cell.residents) == 0]
        return empty_cells


    def place_agents_on_grid(
            self,
            population,
            rule = "random_on_empty_cells",
    ):
        
        assert len(self.grid_as_flat_list) >= len(population)

        if rule == "random_on_empty_cells":

            assert len(self.get_empty_cells()) >= len(population)

            for agent in population:
                new_residence_cell = random.choice(self.get_empty_cells())
                agent.move_out()
                agent.move_in(new_residence_cell)

        else:
            pass


    def create_agents(self, population_name, agent_class, number_of_agents, overwrite = True):
        if overwrite:
            self.agents.update({population_name: []})

        for i in range(number_of_agents):
            name = population_name + "_" + str(i)
            agent = agent_class(name)
            agent.population = self.agents[population_name]
            self.agents[population_name].append(agent)
