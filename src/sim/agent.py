from src.sim.helper import *
from src.sim.world import *
from src.sim.visualizer import *
from src.sim.agent import *
from src.sim.cell import *


class Agent:

    """
    Ein Agent kann sich auf dem Grid bewegen und befindet sich dabei zu jedem Zeitpunkt auf einer Zelle.
    """
    def __init__(self):
        self.name = id(self)
        self.residence_cell = Cell # Aktueller Aufenthaltsort. Typischerweise eine Zelle auf dem Grid.
        self.x_grid_pos = int # Aktuelle Position/Koordinaten. Müssen eigentlich immer gleich der Position des Aufenthaltsortes sein
        self.y_grid_pos = int
        self.population = list # Die Populationsliste einer Welt, in der der Agent "existiert"/eingespeichert ist


    def move_in(self, new_residence_cell):
        """ Eine neue Zelle beziehen"""
        self.residence_cell = new_residence_cell                        # neuen Aufenthaltsort einspeichern
        self.residence_cell.dict_of_residents.update({self.name: self}) # Bei Zelle anmelden
        self.x_grid_pos = self.residence_cell.x_grid_pos    # Koordinaten des neuen Aufenthaltsortes übernehmen
        self.y_grid_pos = self.residence_cell.y_grid_pos


    def move_out(self):
        """ Ordnungsgemäßes Verlassen einer Zelle"""
        del(self.residence_cell.dict_of_residents[self.name]) # sich selbst aus Dict löschen
        self.residence_cell = False             # Zelle als Aufenthaltsort entfernen
        self.x_grid_pos = None                  # X-Position entfernen
        self.y_grid_pos = None                  # Y-Position entfernen


    def move_to_this_cell(self, new_residence_cell):
        """
        FUNCTION
        Aus der aktuellen Zelle ausziehen und zugleich bei einer neuen Zelle einziehen,

        INPUT
        Neue Zelle
        """
        self.move_out()                     # ausziehen
        self.move_in(new_residence_cell)    # einziehen

    def die(self, heaven):
        """
        Lässt den Agenten sterben, indem er von der Zelle entfernt wird und nicht wieder auf dem Grid platziert wird,
        sondern in einer externen Liste (heaven)
        """
        assert self in self.population                      # Sichergehen, dass man überhaupt selbst in der Population ist

        self.move_out()                                     # aus Zelle ausziehen
        del(self.population[self.population.index(self)])   # Sich selbst aus Populationsliste löschen
        heaven.append(self)                                 # Sich selbst in den Himmel begeben

    def get_agents_like_me(self, attribute_name, population):
        """Gibt eine Liste zurück, in der alle Agenten/Objekte sind,
        die auf einem bestimmten Attributen gleich sind wie der Agent."""
        assert type(attribute_name) == str
        return [ agent for agent in population if getattr(agent, attribute_name) == getattr(self, attribute_name) ]







