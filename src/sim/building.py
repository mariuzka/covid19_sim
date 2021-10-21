import random
from typing import List, Optional
from src.sim.cell import Cell

class Building:
    def __init__(
            self,
            building_type: str,
            n_cells_x_dim: int = 1,
            n_cells_y_dim: int = 1,
    ):
        # type of building / location
        self.building_type = building_type
        
        # cell length on x-dimension
        self.n_cells_x_dim = n_cells_x_dim  
        
        # cell length on y-dimension
        self.n_cells_y_dim = n_cells_y_dim
        
        # cells occupied by the building
        self.cells: Optional[Cell] = []                    


    def build_it(
            self,
            building_x_origin: int,
            building_y_origin: int,
            grid_as_matrix: List[List[Cell]],

    ):
        # for each cell of the building ground
        for y in range(building_y_origin, building_y_origin + self.n_cells_y_dim):
            for x in range(building_x_origin, building_x_origin + self.n_cells_x_dim):

                # build the building on cell
                grid_as_matrix[y][x].walkable = False
                grid_as_matrix[y][x].building = self
                grid_as_matrix[y][x].cell_type = self.building_type

                self.cells.append(grid_as_matrix[y][x])


    def build_it_on_random_position(
            self,
            grid_as_flat_list: List[Cell],
            grid_as_matrix: List[List[Cell]],
    ):
        vacant_ground = [
            cell
            for cell in grid_as_flat_list
            if cell.cell_type == "street"
            ]
        
        building_ground = random.choice(vacant_ground)
        
        self.build_it(
            building_ground.x_grid_pos, 
            building_ground.y_grid_pos, 
            grid_as_matrix,
            )