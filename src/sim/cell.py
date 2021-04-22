from src.sim.helper import *
from src.sim.world import *
from src.sim.visualizer import *
from src.sim.agent import *
from src.sim.cell import *


class Cell:
    """
    Cells sind die Felder auf dem Grid.
    Sie verlassen niemals ihre Position und können somit immer über ihre Position gefunden werden.
    Sie können Agenten beherbergen.
    """

    def __init__(
            self,
            x_grid_pos,
            y_grid_pos,
            ):

        self.x_grid_pos = x_grid_pos  # Unveränderliche Position auf der X-Achse des Grids
        self.y_grid_pos = y_grid_pos  # Unveränderliche Position auf der Y-Achse des Grids

        self.walkable = True    # gibt an, ob die Zelle begehbar ist für Agenten
        self.resident = False   # agent, who is currently on that cell

        self.dict_of_residents = {}  # agents, who currently are on that cell

        self.neighbor_cells = []  # benachbarte Cells, je nach Definition von Nachbar

    def __repr__(self):
        return f"Cell at grid_pos {self.x_grid_pos} {self.y_grid_pos}"


    def look_around(
            self,
            target_rel_x_grid_pos,
            target_rel_y_grid_pos,
            len_x_grid_dim,
            len_y_grid_dim,
            grid,  # Matrix, auf die per Koordinaten zugegriffen wird
            torus=True,
            ):

        """
        FUNCTION
        Bietet Zugriff auf Cells, die sich auf einer relativen Position zur aktuellen Cell befinden.
        Ist die Torus-Option aktiviert, dann werden Positionen, die über den Rand des Grids hinausgehen mittels
        Modulo-Funktion auf die gegenüberliegende Seite des Grids transferiert.

        INPUT
        rel_x_grid_pos: Relative Ortsangabe über das Ziel auf der X-Achse
        rel_y_grid_pos: Relative Ortsangabe über das Ziel auf der Y-Achse
        len_x_grid_dim: ...
        len_y_grid_dim: ...
        grid: ...
        torus: Gibt an, ob es sich beim Grid um ein Torus handelt

        OUTPUT
        target: Das Objekt, das sich in der Matrix an der berechneten Position befindet.
        Sollte typischerweise eine Cell sein.
        """

        if torus == True:
            target_x_grid_pos = (self.x_grid_pos + target_rel_x_grid_pos) % len_x_grid_dim
            target_y_grid_pos = (self.y_grid_pos + target_rel_y_grid_pos) % len_y_grid_dim

        else:
            target_x_grid_pos = (self.x_grid_pos + target_rel_x_grid_pos)
            target_y_grid_pos = (self.y_grid_pos + target_rel_y_grid_pos)

        # Schlägt fehl, wenn die Position außerhalb des Grids ist und Torus nicht aktiviert ist!
        try:
            target = grid[target_y_grid_pos][target_x_grid_pos]
        except IndexError:
            target = None

        return target

    def find_arounding_cells(
            self,
            rel_pos_neighbors,
            len_x_grid_dim,
            len_y_grid_dim,
            grid,
            torus=True,
    ):
        """
        FUNCTION
        Sucht die Nachbarn einer Cell auf dem Grid. Was als Nachbar zählt wird über
        rel_pos_neighbors definiert. 

        INPUT
        rel_pos_neighbors: Liste mit den relativen Positionen der Nachbarn vom Agent aus gesehen. Eine relative Position
                            besteht aus einer X- und einer Y-Abweichung auf bezüglich des Agenten.
        
        len_x_grid_dim,
        len_y_grid_dim:    Länge der x- und y-Dimensionen des Grids.
        grid:              Das Grid der World im Matrix-Format.

        OUTPUT
        self.neighbors
        """

        # Position Von-Neumann-Nachbarn (Relativ)
        rel_pos_neumann_neighbors = [
            (0, -1),
            (1, 0),
            (0, 1),
            (-1, 0),
        ]
        # Position Moore-Nachbarn (Relativ)
        rel_pos_moore_neighbors = [
            (-1, -1),
            (0, -1),
            (1, -1),
            (1, 0),
            (1, 1),
            (0, 1),
            (-1, 1),
            (-1, 0),
        ]


        if rel_pos_neighbors == "neumann":
            rel_pos_neighbors = rel_pos_neumann_neighbors
        elif rel_pos_neighbors == "moore":
            rel_pos_neighbors = rel_pos_moore_neighbors

        arounding_cells = []

        for rel_pos in rel_pos_neighbors:
            arounding_cells.append(self.look_around(rel_pos[0],
                                                        rel_pos[1],
                                                        len_x_grid_dim,
                                                        len_y_grid_dim,
                                                        grid,
                                                        torus,
                                                        )
                                       )

        return arounding_cells


    def count_attribute_values_of_neighbor_cells(self, attribute_name, attribute_value):
        return sum( [1 for neigh in self.neighbor_cells if getattr(neigh, attribute_name) == attribute_value] )

