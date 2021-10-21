from typing import Optional, List



class Cell:
    def __init__(
            self,
            x_grid_pos: int,
            y_grid_pos: int,
            ):
        
        # x-coordinate on grid
        self.x_grid_pos: int = x_grid_pos
        
        # y-coordinate on grid
        self.y_grid_pos: int = y_grid_pos

        # Can agents enter this cell? (Does not matter because the modelling of walking has been removed.)
        self.walkable: bool = True

        # agents on that cell
        self.dict_of_residents: dict = {}  

        # type of location
        self.cell_type: str = "street"
        
        # Is there a building on the cell?
        self.building = None
        
        # number of agents use this cell as a location for activities
        self.n_users: int = 0
        
        # number groups/rooms at this location
        self.n_groups: int = 0