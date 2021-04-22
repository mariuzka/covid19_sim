from src.sim.agent import *
from src.sim.cell import *
from src.sim.helper import *
from src.sim.visualizer import *
from src.sim.world import *

class World:
    """
    Eine Welt hat genau ein Grid.
    Sie kann jedoch mehrere Populationen von Agenten beherbergen.
    """

    def __init__(self,
                 len_x_grid_dim,
                 len_y_grid_dim,
                 ):

        self.len_x_grid_dim = len_x_grid_dim
        self.len_y_grid_dim = len_y_grid_dim

        self.half_x_grid_dim = int(self.len_x_grid_dim / 2)
        self.half_y_grid_dim = int(self.len_y_grid_dim / 2)

        self.grid_as_matrix = [[]]
        self.grid_as_flat_list = []

        self.NW_grid_as_flat_list = []
        self.NE_grid_as_flat_list = []
        self.SW_grid_as_flat_list = []
        self.SE_grid_as_flat_list = []

        self.agents = {}

        self.heaven = []



    def create_grid(self, cell_class = "standard"):

        self.grid_as_matrix = []
        self.grid_as_flat_list = []

        for y in range(self.len_y_grid_dim):
            row = []

            for x in range(self.len_x_grid_dim):

                if cell_class == "standard":
                    cell = Cell(x, y)
                else:
                    cell = cell_class(x, y) # Jede Zellenklasse muss als erste Eingabeparameter die X- und Y-Position haben

                row.append(cell)

                self.grid_as_flat_list.append(cell)

                # Zellen auch zu den 4 Quadranten hinzufügen
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


    # returns a list of empty cells in own grid
    def get_empty_cells(self):
        empty_cells = [cell for cell in self.grid_as_flat_list if len(cell.residents) == 0]
        return empty_cells


    def place_agents_on_grid(
            self,
            population,
            rule = "random_on_empty_cells",
    ):
        # Das Grid muss groß genug für die Population sein
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
