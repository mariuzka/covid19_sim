import math
import numpy as np
import pygame
from pygame.locals import DOUBLEBUF

from src.sim.agent import *
from src.sim.cell import *
from src.sim.helper import *
from src.sim.visualizer import *
from src.sim.world import *


import time

"""
Die Visualizer-Klasse dient der graphischen Darstellung von Agentenbasierten Simulationen.

Zunächst muss eine Instanz der Visualizerklasse erstellt werden. Dazu müssen die Größe der Zellen (in Pixel) auf dem Grid,
und die Größe des Grids (in Zellen) auf der X- und Y-Dimension angegeben werden.

Pro Simulationsdarstellung kann es genau ein Grid geben und die Anzahl der Zellen auf dem Grid bleibt für immer gleich.

Wenn die Instanz mit den genannten Grundeinstellungen erstellt wurde, kann mithilfe der draw_population-Funktionen
jeweils eine Gruppe von Objekten/Agenten/Cells dargestellt werden.

Mit der control()-Funktion können während der Simulation Parameter geändert werden (nur die, auf die während der Simulation
auch zugegriffen wird, sonst macht es keinen Unterschied, diese zu verändern).

Mit der plot()-Funktion können beliebige Werte während der Simulation geplottet werden.

Zuletzt muss noch die update_screen()-Funktion aufgerufen werden, um die Darstellung zu aktualisieren.
"""

class Visualizer:

    # RGB-Farbpalette
    colors = {
        "black": (0, 0, 0),
        "white": (255, 255, 255),
        "gainsboro": (220, 220, 220),
        "Gray": (128,128,128),
        "navy": (0, 0, 128),
        "dark red": (139,0,0),
        "green": (0, 255, 0),
        "gold": (255,215,0),
        "white smoke": (245,245,245),
        "dim gray": (105, 105, 105),
        "royal blue": (65,105,225),
        "red": (255,0,0),
        "blue": (0,0,255),
        "sea green":(46, 139, 87),
        "dodger blue": (30,144,255),
        "deep sky blue":(0,191,255),
        "chocolate": (210,105,30),
        "rosy brown":(188,143,143),
        "slate gray" :(112,128,144),
        "pink":(255,192,203),
        "forest green": (34,139,34),
        "orange": (255,165,0),
    }

    # Farben für die Plot-Linien, falls mehrere in einem Graphen dargestellt werden sollen
    plot_colors = [
        colors["black"],
        colors["blue"],
        colors["red"],
        colors["green"],
        colors["gold"],
    ]

    COLOR_EDGES = colors["black"]
    CHANGE_VALUE_BUTTON_COLOR = "Gray"

    BACKGROUND_COLOR = colors["white smoke"]

    DOUBLECLICKTIME = 250

    def __init__(
            self,
            len_x_grid_dim,
            len_y_grid_dim,
            display_speed = 100,
            simulation_window_width = 700,
            plotting_window_width = 400,
            controlling_window_width = 200,
            screen_height=700,
            pause_if_mouse_in_controlling_window = True,
    ):

        ######################################################
        # Fenster-Eigenschaften
        ######################################################

        # Pixel-Größe eines öfter verwendeten Platzhalters/Abstandes zwischen Widgets
        self.screen_gap = 30

        # Breite der Fenster
        self.simulation_window_width = simulation_window_width
        self.plotting_window_width = plotting_window_width
        self.controlling_window_width = controlling_window_width

        # Höhe der Fenster
        self.simulation_window_height = simulation_window_width
        self.plotting_window_height = screen_height
        self.controlling_window_height = screen_height

        # Größe des Gesamtfensters
        self.screen_width = self.plotting_window_width + self.simulation_window_width + self.controlling_window_width + self.screen_gap * 6
        self.screen_height = screen_height + self.screen_gap * 2

        # Koordinaten-Ursprung des Plotting-Fensters
        self.plotting_window_x_origin = 0 + self.screen_gap
        self.plotting_window_y_origin = 0 + self.screen_gap

        # Koordinaten-Ursprung des Simulations-Fensters
        self.simulation_window_x_origin = self.plotting_window_width + self.screen_gap * 3
        self.simulation_window_y_origin = 0 + self.screen_gap

        # Koordinaten-Ursprung des Controlling-Fensters
        self.controlling_window_x_origin = self.plotting_window_width + self.simulation_window_width + self.screen_gap * 5
        self.controlling_window_y_origin = 0 + self.screen_gap

        # Anzahl der Zellen auf einer Dimension des Grids
        self.len_x_grid_dim = len_x_grid_dim  # Größe des Grids auf der X-Dimension
        self.len_y_grid_dim = len_y_grid_dim  # Größe des Grids auf der Y-Dimension

        # Pixel-Zellengrößen der Zellen auf dem Grid im Simulationswindow berechnen
        self.cell_width = int(self.simulation_window_width / self.len_x_grid_dim)
        self.cell_height = int(self.simulation_window_height / self.len_y_grid_dim)

        # Anzahl der im Controller angezeigten Skalenschritte
        self.n_displayed_steps = 100


        ######################################################
        # PYGAME STUFF
        ######################################################

        flags = DOUBLEBUF
        #screen = pygame.display.set_mode(resolution, flags, bpp)

        pygame.init()
        pygame.font.init()
        self.clock = pygame.time.Clock()

        # Display initialisieren
        self.screen = pygame.display.set_mode([self.screen_width, self.screen_height], flags)
        self.screen.set_alpha(None)
        self.screen.fill(self.BACKGROUND_COLOR)

        # Font-Größen
        self.font_small_height = self.screen_height // 70
        self.font_medium_height = self.screen_height // 50

        # Fonts / Schriftarten
        self.font1 = pygame.font.SysFont("Calibri", int(self.screen_gap / 1.75))
        self.font_small = pygame.font.SysFont("Calibri", self.font_small_height)
        self.font_medium = pygame.font.SysFont("Calibri", self.font_medium_height)

        # Framerate
        self.display_speed = display_speed

        # Zeitmesser für Doppelklick
        self.dbclock = pygame.time.Clock()

        ######################################################
        # DICTS
        ######################################################

        # Plotting
        self.graphs = {}

        # Controllers
        self.controllers = {}

        # Tasten
        self.mouse_to_rescaled_current_value_distance = float
        self.buttons = {
            "mouse_left": "up",
            "mouse_right": "up",
            "mouse_x_screen_pos": pygame.mouse.get_pos()[0],
            "mouse_y_screen_pos": pygame.mouse.get_pos()[1],
        }

        # wenn die Jitteroption aktiviert ist, dann wird für jeden Agenten eine Abweichung hier eingespeichert
        self.jitter_deviations_dict = {}

        ######################################################
        # Tick
        ######################################################
        self.tick = 0
        self.ticks_per_second = 0
        self.time_t0 = time.process_time()

        ######################################################
        # Sonstiges
        ######################################################
        self.pause_if_mouse_in_controlling_window = pause_if_mouse_in_controlling_window
        self.pause = False

    ####################################################################################################################
    # Funktionen
    ####################################################################################################################

    def update_pygame_events(self):

        # Maustasten in Ursprungszustand setzen
        self.buttons["mouse_left"] = "up"
        self.buttons["mouse_right"] = "up"

        # Mausposition erfragen und in Dict einspeichern
        self.buttons["mouse_x_screen_pos"], self.buttons["mouse_y_screen_pos"] = pygame.mouse.get_pos()

        # Pygame-Events abfragen
        pygame_events = pygame.event.get()

        # Für alle aufgetretenen Events
        for event in pygame_events:

            # Rechtsklick?
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                self.buttons["mouse_right"] = "down"
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                self.buttons["mouse_right"] = "up"

            # Linksklick?
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.buttons["mouse_left"] = "down"
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.dbclock.tick() < self.DOUBLECLICKTIME:
                    self.buttons["mouse_left"] = "double_click"
                else:
                    self.buttons["mouse_left"] = "single_click"

            # Pygame schließen?
            elif event.type == pygame.QUIT:
                pygame.display.quit()
                pygame.quit()

    ####################################################################################################################
    # Simulation malen
    ####################################################################################################################

    def draw_agent_base_function(
            self,
            agent,
            color_or_color_func,
            agent_as_color_func_argument = True,
            agent_relative_width=0,
            agent_relative_height=0,
            x_grid_pos_attr_name="x_grid_pos",
            y_grid_pos_attr_name="y_grid_pos",
            draw_outline=True,
            outline_color = "black",
            jitter=False
    ):
        # Farbe berechnen, indem einer eingegebenen Color-Funktion der Agent übergeben wird
        if agent_as_color_func_argument:
            color = color_or_color_func(agent)
        else:
            color = color_or_color_func()

        # Grid-Position des Objekts erfragen
        x_grid_pos = getattr(agent, x_grid_pos_attr_name)
        y_grid_pos = getattr(agent, y_grid_pos_attr_name)

        # Zellen-Position berechnen
        cell_x_screen_pos = self.simulation_window_x_origin + x_grid_pos * self.cell_width
        cell_y_screen_pos = self.simulation_window_y_origin + y_grid_pos * self.cell_height

        agent_width = self.cell_width + agent_relative_width
        agent_height = self.cell_height + agent_relative_height

        # Wenn die Jitterfunktion aktiviert ist
        if jitter:

            # Wenn für den Agenten noch kein Jitter-Wert im Dict abgelegt ist
            if id(agent) not in self.jitter_deviations_dict:

                # Jitter-Wert für X- und Y-Dimension einspeichern
                self.jitter_deviations_dict.update({
                    id(agent): (random.randint(0, round(self.cell_width - agent_width)),
                                random.randint(0, round(self.cell_width - agent_width)),
                                )
                })

            # Screen-Position mit Jitter-Wert berechnen
            x_screen_pos = cell_x_screen_pos + self.jitter_deviations_dict[id(agent)][0]
            y_screen_pos = cell_y_screen_pos + self.jitter_deviations_dict[id(agent)][1]

        else:
            # Positionsabweichung zu Cell-Screen-Position berechnen, die aufgrund von Größenunterschied zur Cell entsteht
            x_shift = -agent_relative_width / 2
            y_shift = -agent_relative_height / 2

            # Position auf Bildschirm berechnen
            x_screen_pos = cell_x_screen_pos + x_shift
            y_screen_pos = cell_y_screen_pos + y_shift


        # Rechtecks-Maße des zu malenden Agenten
        rect = (
        x_screen_pos,                               # agent's x-pos on screen
        y_screen_pos,                               # agent's y-pos on screen
        agent_width,     # agent's width on screen
        agent_height,   # agents's height on screen
        )


        # Quadrat malen
        pygame.draw.rect(
            self.screen,
            color,
            rect,
        )

        if draw_outline:
            # Umrandung für Quadrat malen
            pygame.draw.rect(
                self.screen,
                self.colors[outline_color],
                rect,
                1,
            )

    def draw_population_base_function(
        self,
        population,
        color_or_color_func,
        agent_as_color_func_argument = True,
        agent_relative_width = 0,
        agent_relative_height = 0,
        x_grid_pos_attr_name = "x_grid_pos",
        y_grid_pos_attr_name = "y_grid_pos",
        draw_outline = True,
        outline_color = "black",
        jitter=False,
    ):
        for pop_member in population:
            self.draw_agent_base_function(
                pop_member,
                color_or_color_func,
                agent_as_color_func_argument=agent_as_color_func_argument,
                agent_relative_width=agent_relative_width,
                agent_relative_height=agent_relative_height,
                x_grid_pos_attr_name=x_grid_pos_attr_name,
                y_grid_pos_attr_name=y_grid_pos_attr_name,
                draw_outline=draw_outline,
                outline_color = outline_color,
                jitter = jitter,
            )

    def draw_population_with_immutable_color(
            self,
            population,
            color,
            agent_relative_width=0,
            agent_relative_height=0,
            x_grid_pos_attr_name="x_grid_pos",
            y_grid_pos_attr_name="y_grid_pos",
            draw_outline=True,
            outline_color = "black",
    ):
        self.draw_population_base_function(
            population,
            lambda: color,
            agent_as_color_func_argument=False,
            agent_relative_width=agent_relative_width,
            agent_relative_height=agent_relative_height,
            x_grid_pos_attr_name=x_grid_pos_attr_name,
            y_grid_pos_attr_name=y_grid_pos_attr_name,
            draw_outline=draw_outline,
            outline_color = outline_color,
        )

    def draw_population_with_categorial_attributes(
            self,
            population,
            attribute_name,
            attribute_states_and_colors_dict,
            agent_relative_width=0,
            agent_relative_height=0,
            x_grid_pos_attr_name="x_grid_pos",
            y_grid_pos_attr_name="y_grid_pos",
            draw_outline = True,
            outline_color = "black",
            jitter=False,
    ):
        """
        Stellt die Agenten je nach Wert des eingegebenen Attributs in der entsprechenden Farbe dar.
        """

        def look_up_color(agent):
            return attribute_states_and_colors_dict[getattr(agent, attribute_name)]

        self.draw_population_base_function(
            population,
            look_up_color,
            agent_relative_width=agent_relative_width,
            agent_relative_height=agent_relative_height,
            draw_outline=draw_outline,
            outline_color=outline_color,
            jitter=jitter,
        )

    def draw_population_with_dynamic_color(
            self,
            population,
            attribute_name,
            attribute_min,
            attribute_max,
            agent_relative_width=0,
            agent_relative_height=0,
            x_grid_pos_attr_name="x_grid_pos",
            y_grid_pos_attr_name="y_grid_pos",
            draw_outline=True,
            outline_color = "black",

    ):

        def calculate_dynamic_color(agent):
            rescaled_attribute = rescale(
                getattr(agent, attribute_name),
                attribute_min,
                attribute_max,
                -255,
                255,
            )
            if rescaled_attribute > 0:
                r = 255
                g = 255 - rescaled_attribute
                b = 255 - rescaled_attribute

            elif rescaled_attribute < 0:
                r = 255 - abs(rescaled_attribute)
                g = 255 - abs(rescaled_attribute)
                b = 255

            else:
                r = 255
                g = 255
                b = 255

            return r, g, b

        self.draw_population_base_function(
            population,
            calculate_dynamic_color,
            agent_as_color_func_argument= True,
            agent_relative_width=agent_relative_width,
            agent_relative_height=agent_relative_height,
            x_grid_pos_attr_name = x_grid_pos_attr_name,
            y_grid_pos_attr_name = y_grid_pos_attr_name,
            draw_outline = draw_outline,
            outline_color = outline_color,

        )



    ####################################################################################################################
    # Plot-Funktionen
    ####################################################################################################################

    def plot(
            self,
            graph_name,
            value_dict,
            compress = True,
            plotting_interval = 1,
            summary_method = sum,
            line_colors = "standard",
    ):

        ############################################################################################################
        # initialize graph
        ############################################################################################################

        # checken, ob es den Graphen noch nicht gibt
        if not graph_name in self.graphs:
            # Neues Dict für Graphen im Graphen-Dict anlegen
            self.graphs.update(
                {
                    graph_name: {
                        "min_value": 0,
                        "max_value": 0,
                    },

                }
            )

        # checken, ob bereits ein Graphen-Index für den Graphen eingespeichert wurde
        if not "graph_index" in self.graphs[graph_name]:
            # Graphen-Position einspeichern
            self.graphs[graph_name]["graph_index"] = len(self.graphs) - 1


        # für jeden Wert im übergebenen Werte-Dict
        for value_name in value_dict.keys():

            # checken, ob es für den Value noch keinen Speicher im Graphen gibt
            if not value_name in self.graphs[graph_name]:
                # Datenliste für Value anlegen
                self.graphs[graph_name].update(
                    {value_name:[]}
                )
                # Falls das Plotting-Intervall größer 1 ist und daher Werte zwischengespeichert werden müssen
                if plotting_interval > 1:
                    self.graphs[graph_name].update(
                        {value_name + "_temp": []}
                    )


            ############################################################################################################
            # update graph
            ############################################################################################################

            # Value an entsprechende Datenliste anhängen
            if plotting_interval > 1:
                self.graphs[graph_name][value_name + "_temp"].append(round(value_dict[value_name]))
                if len(self.graphs[graph_name][value_name + "_temp"]) >= plotting_interval:
                    plotting_interval_value = summary_method(self.graphs[graph_name][value_name + "_temp"])
                    self.graphs[graph_name][value_name].append(plotting_interval_value)
                    self.graphs[graph_name][value_name + "_temp"] = []
            else:
                self.graphs[graph_name][value_name].append(value_dict[value_name])


            # Minimum und Maximum bestimmen
            if value_dict[value_name] < self.graphs[graph_name]["min_value"]:
                self.graphs[graph_name]["min_value"] = value_dict[value_name]
            elif value_dict[value_name] > self.graphs[graph_name]["max_value"]:
                self.graphs[graph_name]["max_value"] = value_dict[value_name]



        # Länge und Breite des Graphen berechnen
        graph_width = self.plotting_window_width
        graph_height = self.plotting_window_height // len(self.graphs)

        # Graphen-Screen-Ursprung berechnen
        graph_x_origin = self.plotting_window_x_origin
        graph_y_origin = self.plotting_window_y_origin + self.graphs[graph_name]["graph_index"] * graph_height

        # Länge und Breite der Plotting-Area (der Teil des Graphen, indem auch geplottet wird) berechnen
        GRAPH_PLOT_X_GAP = graph_width // 5
        GRAPH_PLOT_Y_GAP = graph_height // 5
        plot_width = graph_width - GRAPH_PLOT_X_GAP
        plot_height = graph_height - GRAPH_PLOT_Y_GAP

        # Plotting-Area-Ursprung berechnen
        plot_x_origin = graph_x_origin + GRAPH_PLOT_X_GAP
        plot_y_origin = graph_y_origin + GRAPH_PLOT_Y_GAP // 2

        pygame.draw.rect(
            self.screen,
            self.colors["dim gray"],
            (plot_x_origin, plot_y_origin, plot_width, plot_height),
            1,
        )

        # Graph-Bezeichnung einzeichnen
        self.draw_text_new(
            graph_name,
            graph_x_origin + 5,
            graph_y_origin + 5,
            self.font_medium,
            "black",
        )
        # Abgrenzung zwischen Plot- und Simulations-Window malen
        pygame.draw.line(
            self.screen,
            self.COLOR_EDGES,
            (self.simulation_window_x_origin - self.screen_gap, 0),
            (self.simulation_window_x_origin - self.screen_gap, self.screen_height),
            1,
        )

        # Graphen-Tick-Minimum einzeichnen
        self.draw_text_new(
            str(0),
            plot_x_origin,
            plot_y_origin + plot_height + 2,
            self.font_small,
            "dim gray",
        )
        # Graphen-Tick-Maximum einzeichnen
        self.draw_text_new(
            str(len(self.graphs[graph_name][value_name])),
            plot_x_origin + plot_width - 10,
            plot_y_origin + plot_height + 2,
            self.font_small,
            "dim gray",
        )

        # Farben für Linien holen
        line_colors = (self.plot_colors if line_colors == "standard" else line_colors)

        for i, value_name in enumerate(value_dict.keys()):

            # für bessere Lesbarkeit die Datenliste unter anderem Namen abspeichern
            value_list = self.graphs[graph_name][value_name]

            # Wenn es zu plottende Daten gibt
            if len(value_list) >= 2:

                # Minimum und Maximum der Datenlisten aller Datenlisten im Graph heraussuchen
                # Die 0 ist immer mit in der Auswahl
                min_value = math.floor(self.graphs[graph_name]["min_value"])
                max_value = math.ceil(self.graphs[graph_name]["max_value"])


                pointlist = [
                    (round(plot_x_origin + rescale(i, 0, len(value_list) - 1, 0, plot_width)),

                     round(plot_y_origin + plot_height - rescale(value, min_value, max_value, 0, plot_height))
                     )
                    for i, value in enumerate(value_list)
                ]

                # Graphen-Linie zeichnen
                pygame.draw.aalines(
                    self.screen,
                    line_colors[i],
                    False,
                    pointlist)

                # Graphen-Linien-Ende mit Punkt zeichnen
                # pygame.draw.circle(
                #     self.screen,
                #     line_colors[i],
                #     pointlist[-1],
                #     3,
                # )

                # Graphen-Y-Minimum einzeichnen
                self.draw_text_new(
                    str(min_value),
                    graph_x_origin,
                    plot_y_origin + plot_height - self.font_small_height,
                    self.font_small,
                    "dim gray",
                )
                # Graphen-Y-Maximum einzeichnen
                self.draw_text_new(
                    str(max_value),
                    graph_x_origin,
                    plot_y_origin ,
                    self.font_small,
                    "dim gray",
                )



        for i, value_name in enumerate(value_dict.keys()):

            y_pos = plot_y_origin + plot_height // 2 + self.font_small_height * i * 2 - self.font_small_height * (
                            len(value_dict) // 2)

            # Werte-Label in Legende malen
            self.draw_text_new(
                value_name,
                graph_x_origin,
                y_pos,
                self.font_small,
                line_colors[i],
            )
            if len(self.graphs[graph_name][value_name]) > 0:
                self.draw_text_new(
                    str(self.graphs[graph_name][value_name][-1]),
                    graph_x_origin,
                    y_pos + self.font_small_height,
                    self.font_small,
                    line_colors[i],
                )





    ####################################################################################################################
    # Controller-Funktionen
    ####################################################################################################################

    def control(
            self,
            controller_name,
            instance_or_class,
            attribute_name,
            attribute_min,
            attribute_max,
            increment = 1,
    ):

        ################################################################################################################
        # DIE ERSTEN ZWEI TICKS
        ################################################################################################################
        # INITALISIERUNG DES CONTROLLERS
        ################################################################################################################
        if self.tick < 2:
            # checken, ob der Kontroller bereits existiert
            if not controller_name in self.controllers:
                self.controllers.update({
                    controller_name : {
                        "controlled_object": instance_or_class,
                        "attribute_name": attribute_name,
                        "attribute_min": attribute_min,
                        "attribute_max": attribute_max,
                        "current_value" : getattr(instance_or_class, attribute_name),
                        "sweep_value_y_screen_pos" : None,
                        "sweep_value": None
                    }
                }
            )

            # checken, ob bereits ein Kontroller-Index für den Controller eingespeichert wurde
            if not "controller_index" in self.controllers[controller_name]:
                # Graphen-Position einspeichern
                self.controllers[controller_name]["controller_index"] = len(self.controllers) - 1


            ############################################################################################################
            # Konstante Controller-Werte berechnen
            ############################################################################################################

            # Skalenschritte berechnen
            values_on_scale = np.arange(attribute_min, attribute_max + increment, increment)

            # Länge und Breite des Controlers berechnen
            controller_width = self.controlling_window_width // len(self.controllers)
            controller_height = self.controlling_window_height

            # Ursprung dieses Controllers berechnen
            controller_x_origin = self.controlling_window_x_origin + controller_width * self.controllers[controller_name]["controller_index"]
            controller_x_end = controller_x_origin + controller_width

            controller_y_origin = self.controlling_window_y_origin
            controller_y_end = controller_y_origin + controller_height

            # Slider-Properties berechnen
            slider_height = controller_height // 2
            slider_y_origin = controller_y_origin + controller_height // 4
            slider_y_end = slider_y_origin + slider_height

            # Plätze ÜBER Slider berechnen
            n_rows_above_slider = 4
            above_slider_height = slider_y_origin - controller_y_origin
            above_slider_row_height = above_slider_height / n_rows_above_slider

            # Plätze UNTER Slider berechnen
            n_rows_beneath_slider = 4
            beneath_slider_height = controller_y_end - slider_y_end
            beneath_slider_row_height = beneath_slider_height / n_rows_beneath_slider

            # Attribut-Wert in Slider-Wert übersetzen
            rescaled_current_value = rescale(
                self.controllers[controller_name]["current_value"],
                attribute_min,
                attribute_max,
                slider_y_origin,
                slider_y_end,
                )

            # Button-Properties
            button_width = controller_width // 2
            button_height = self.screen_height // 18
            button_x_screen_pos = controller_x_origin + controller_width // 2 - button_width // 2
            button_y_screen_pos = rescaled_current_value - button_height // 2

            # Größe der angezeigten Skalenschritte/-Linien berechnen
            displayed_step_size = (attribute_max - attribute_min) / self.n_displayed_steps
            displayed_steps = [round(displayed_step_size * i, 4) for i in
                               range(self.n_displayed_steps + 1)]
            displayed_step_y_screen_positions = [rescale(displayed_step,attribute_min,attribute_max,slider_y_origin,slider_y_origin + slider_height) for displayed_step in displayed_steps]


            # Verschiedene Rechtecke berechnen
            rect_button_value_up = (
                button_x_screen_pos + button_width // 2,
                slider_y_end + beneath_slider_row_height * 2,
                button_width // 2,
                button_height // 2,
            )
            rect_button_value_down = (
                button_x_screen_pos,
                slider_y_end + beneath_slider_row_height * 2,
                button_width // 2,
                button_height // 2,
            )
            rect_button_sweep_value_up = (
                button_x_screen_pos + button_width // 2,
                slider_y_end + beneath_slider_row_height * 3,
                button_width // 2,
                button_height // 2,
            )
            rect_button_sweep_value_down = (
                button_x_screen_pos,
                slider_y_end + beneath_slider_row_height * 3,
                button_width // 2,
                button_height // 2,
            )
            rect_controller = (
                controller_x_origin,
                controller_y_origin,
                controller_width,
                controller_height,
            )
            rect_slider = (
                controller_x_origin,
                slider_y_origin,
                controller_width,
                slider_height,
            )
            rect_slider_button = (
                button_x_screen_pos,
                button_y_screen_pos,
                button_width,
                button_height,
            )
            rect_controlling_window = (
                self.controlling_window_x_origin,
                self.controlling_window_y_origin,
                self.controlling_window_width,
                self.controlling_window_height,
            )

            self.controllers[controller_name].update({
                "values_on_scale": values_on_scale,
                "increment": increment,
                "controller_width": controller_width,
                "controller_height": controller_height,
                "controller_x_origin": controller_x_origin,
                "controller_x_end": controller_x_end,
                "controller_y_origin": controller_y_origin,
                "controller_y_end": controller_y_end,
                "slider_height": slider_height,
                "slider_y_origin": slider_y_origin,
                "slider_y_end": slider_y_end,
                "n_rows_above_slider": n_rows_above_slider,
                "above_slider_height": above_slider_height,
                "above_slider_row_height": above_slider_row_height,
                "n_rows_beneath_slider": n_rows_beneath_slider,
                "beneath_slider_height": beneath_slider_height,
                "beneath_slider_row_height": beneath_slider_row_height,
                "rescaled_current_value": rescaled_current_value,
                "button_width": button_width,
                "button_height": button_height,
                "button_x_screen_pos": button_x_screen_pos,
                "button_y_screen_pos": button_y_screen_pos,
                "displayed_step_size": displayed_step_size,
                "displayed_steps": displayed_steps,
                "displayed_step_y_screen_positions": displayed_step_y_screen_positions,
                "rect_button_value_up": rect_button_value_up,
                "rect_button_value_down": rect_button_value_down,
                "rect_button_sweep_value_up": rect_button_sweep_value_up,
                "rect_button_sweep_value_down":  rect_button_sweep_value_down,
                "rect_controller": rect_controller,
                "rect_slider": rect_slider,
                "rect_slider_button": rect_slider_button,
                "rect_controlling_window": rect_controlling_window,
            })

        ################################################################################################################
        # JEDE RUNDE
        ################################################################################################################
        # Konstante Werte des Controllers holen
        ################################################################################################################

        # Dict holen und zur besseren Lesbarkeit unter "d" abspeichern
        d = self.controllers[controller_name]

        # Konstante Werte des Controllers holen
        values_on_scale = d["values_on_scale"]
        increment = d["increment"]
        controller_width = d["controller_width"]
        controller_height = d["controller_height"]
        controller_x_origin = d["controller_x_origin"]
        controller_x_end = d["controller_x_end"]
        controller_y_origin = d["controller_y_origin"]
        controller_y_end = d["controller_y_end"]
        slider_height = d["slider_height"]
        slider_y_origin = d["slider_y_origin"]
        slider_y_end = d["slider_y_end"]
        n_rows_above_slider = d["n_rows_above_slider"]
        above_slider_height = d["above_slider_height"]
        above_slider_row_height = d["above_slider_row_height"]
        n_rows_beneath_slider = d["n_rows_beneath_slider"]
        beneath_slider_height = d["beneath_slider_height"]
        beneath_slider_row_height = d["beneath_slider_row_height"]
        button_width = d["button_width"]
        button_height = d["button_height"]
        button_x_screen_pos = d["button_x_screen_pos"]
        button_y_screen_pos = d["button_y_screen_pos"]
        displayed_step_size = d["displayed_step_size"]
        displayed_steps = d["displayed_steps"]
        displayed_step_y_screen_positions = d["displayed_step_y_screen_positions"]
        rect_button_value_up = d["rect_button_value_up"]
        rect_button_value_down = d["rect_button_value_down"]
        rect_button_sweep_value_up = d["rect_button_sweep_value_up"]
        rect_button_sweep_value_down = d["rect_button_sweep_value_down"]
        rect_controller = d["rect_controller"]
        rect_slider = d["rect_slider"]
        rect_controlling_window = d["rect_controlling_window"]

        ################################################################################################################
        # Variable Werte des Controllers berechnen
        ################################################################################################################

        # Attribut-Wert in Slider-Wert übersetzen
        rescaled_current_value = rescale(
            self.controllers[controller_name]["current_value"],
            attribute_min,
            attribute_max,
            slider_y_origin,
            slider_y_end,
            )

        # Slider-Button-Y-Position berechnen
        button_y_screen_pos = rescaled_current_value - button_height // 2

        # Slider-Button-Rechteck definieren
        rect_slider_button = (
                button_x_screen_pos,
                button_y_screen_pos,
                button_width,
                button_height,
            )

        ################################################################################################################
        # malen
        ################################################################################################################

        # Controller-Überschrift malen
        self.draw_text_new(
            controller_name,
            controller_x_origin + controller_width // 10,
            controller_y_origin,
            self.font_medium,
        )

        # Aktuellen Wert über Controller malen
        self.draw_text_new(
            str(round(self.controllers[controller_name]["current_value"], 4)),
            controller_x_origin + controller_width // 10,
            controller_y_origin + above_slider_row_height * 1,
            self.font_medium,
        )

        # Aktuellen Sweep-Wert über Controller malen
        if self.controllers[controller_name]["sweep_value"]:
            self.draw_text_new(
                str(round(self.controllers[controller_name]["sweep_value"],4)),
                controller_x_origin + controller_width // 10,
                controller_y_origin + above_slider_row_height * 2,
                self.font_medium,
                color_from_my_colors_dict="dark red"
            )

        # Slider/Attribut-Minimum über Slider anzeigen
        self.draw_text_new(
            str(attribute_min),
            controller_x_origin + controller_width // 10,
            slider_y_origin - self.font_small_height - button_height // 2,
            self.font_small,
            "dim gray",
        )

        # Slider/Attribut-Maximum unter Slider anzeigen
        self.draw_text_new(
            str(attribute_max),
            controller_x_origin + controller_width // 10,
            slider_y_end + button_height // 2,
            self.font_small,
            "dim gray",
        )

        # Skalenschritte einzeichnen
        for i, displayed_step_y_screen_pos in enumerate(displayed_step_y_screen_positions):
            if i % 10 == 0:
                pygame.draw.line(
                    self.screen,
                    self.colors["dim gray"],
                    (controller_x_origin + controller_width // 10, displayed_step_y_screen_pos),
                    (controller_x_origin + controller_width - controller_width // 10, displayed_step_y_screen_pos),
                    1,
                )
            elif i % 5 == 0:
                pygame.draw.line(
                    self.screen,
                    self.colors["dim gray"],
                    (controller_x_origin + controller_width // 6, displayed_step_y_screen_pos),
                    (controller_x_origin + controller_width - controller_width // 6, displayed_step_y_screen_pos),
                    1,
                )
            else:
                # Skalenlinien einzeichnen
                pygame.draw.line(
                    self.screen,
                    self.colors["dim gray"],
                    (controller_x_origin + controller_width // 5, displayed_step_y_screen_pos),
                    (controller_x_origin + controller_width - controller_width // 5, displayed_step_y_screen_pos),
                    1,
                )

        # Poti-Laufschiene malen
        pygame.draw.line(
            self.screen,
            self.colors["black"],
            (controller_x_origin + controller_width // 2, slider_y_origin),
            (controller_x_origin + controller_width // 2, slider_y_end),
            1,
        )

        # Sweep-Value-Linie malen
        if self.controllers[controller_name]["sweep_value"]:
            pygame.draw.line(
                self.screen,
                self.colors["dark red"],
                (controller_x_origin, self.controllers[controller_name]["sweep_value_y_screen_pos"]),
                (controller_x_origin + controller_width, self.controllers[controller_name]["sweep_value_y_screen_pos"]),
                1,
            )

        # Slider-Button malen
        pygame.draw.rect(self.screen, self.colors["dim gray"], rect_slider_button)
        pygame.draw.rect(self.screen, self.colors["black"], rect_slider_button, 1)

        # Mittelline von Slider-Button malen
        pygame.draw.line(
            self.screen,
            self.colors["white smoke"],
            (button_x_screen_pos, rescaled_current_value),
            (button_x_screen_pos + button_width - 1, rescaled_current_value),
            1)


        # Abgrenzung zu Controlling-Window malen
        pygame.draw.line(
            self.screen,
            self.colors["black"],
            (self.controlling_window_x_origin - self.screen_gap, 0),
            (self.controlling_window_x_origin - self.screen_gap, self.screen_height),
            1,
            )

        # Controller-Umrandung links malen
        pygame.draw.line(
            self.screen,
            self.colors["dim gray"],
            (controller_x_origin, controller_y_origin),
            (controller_x_origin, controller_y_end),
            1,
        )

        # Controller-Umrandung rechts malen
        if self.controllers[controller_name]["controller_index"] == len(self.controllers) - 1:
            pygame.draw.line(
                self.screen,
                self.colors["dim gray"],
                (controller_x_end, controller_y_origin),
                (controller_x_end, controller_y_end),
                1,
            )

        # Aktuellen Wert in Slider-Button malen
        self.draw_text_new(
            str(round(self.controllers[controller_name]["current_value"], 4)),
            button_x_screen_pos + 2,
            button_y_screen_pos + 2,
            self.font_small,
            "white",
        )

        # Kleine Knöpfe unter Slider malen
        pygame.draw.rect(self.screen, self.colors[self.CHANGE_VALUE_BUTTON_COLOR], rect_button_value_up)
        pygame.draw.rect(self.screen, self.colors["black"], rect_button_value_up, 1)
        self.draw_text_new(
            "+1",
            rect_button_value_up[0] + 4,
            rect_button_value_up[1] + 3,
            self.font_small,
        )
        pygame.draw.rect(self.screen, self.colors[self.CHANGE_VALUE_BUTTON_COLOR], rect_button_value_down)
        pygame.draw.rect(self.screen, self.colors["black"], rect_button_value_down, 1)
        self.draw_text_new(
            "-1",
            rect_button_value_down[0] + 4,
            rect_button_value_down[1] + 3,
            self.font_small,
        )
        pygame.draw.rect(self.screen, self.colors[self.CHANGE_VALUE_BUTTON_COLOR], rect_button_sweep_value_up)
        pygame.draw.rect(self.screen, self.colors["black"], rect_button_sweep_value_up, 1)
        self.draw_text_new(
            "+1",
            rect_button_sweep_value_up[0] + 4,
            rect_button_sweep_value_up[1] + 3,
            self.font_small,
            "dark red",
        )
        pygame.draw.rect(self.screen, self.colors[self.CHANGE_VALUE_BUTTON_COLOR], rect_button_sweep_value_down)
        pygame.draw.rect(self.screen, self.colors["black"], rect_button_sweep_value_down, 1)
        self.draw_text_new(
            "-1",
            rect_button_sweep_value_down[0] + 4,
            rect_button_sweep_value_down[1] + 3,
            self.font_small,
            "dark red",
        )

        ################################################################################################################
        # User-Interaktionen (Controller-Window)
        ################################################################################################################

        # Maus-Status Position abrufen
        mouse_x_screen_pos, mouse_y_screen_pos = self.buttons["mouse_x_screen_pos"], self.buttons["mouse_y_screen_pos"]

        # Maus im Controller-Window?
        if self.is_mouse_over_rect(rect_controlling_window):

            # Maus über Slider-Knopf?
            if self.is_mouse_over_rect(rect_slider_button):

                # Wenn Maustaste nicht gedrückt wird
                if pygame.mouse.get_pressed()[0] == 0:

                    # Die Distanz zwischen Mausposition und dem kontrollierten Wert berechnen, damit Knopf nicht springt
                    self.mouse_to_rescaled_current_value_distance = mouse_y_screen_pos - rescaled_current_value

                    # Mittelline von Knopf in Farbe malen
                    pygame.draw.line(
                        self.screen,
                        self.colors["navy"],
                        (button_x_screen_pos, rescaled_current_value),
                        (button_x_screen_pos + button_width - 1, rescaled_current_value),
                        1)

                # Wenn Maustaste gedrückt wird
                if pygame.mouse.get_pressed()[0] == 1:
                    # Mittelline von Knopf in Farbe malen
                    pygame.draw.line(
                        self.screen,
                        self.colors["dark red"],
                        (button_x_screen_pos, rescaled_current_value),
                        (button_x_screen_pos + button_width - 1, rescaled_current_value),
                        1)


                    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

                    # Rückübersetzung von Slider-Wert

                    # Knopfposition in urspüngliche Skala bzw. neuen Wert des kontrollierten Attributs übersetzen
                    exact_new_value = rescale(
                        (mouse_y_screen_pos - self.mouse_to_rescaled_current_value_distance),
                        slider_y_origin,
                        slider_y_end,
                        attribute_min,
                        attribute_max,
                    )

                    # Den ähnlichsten Wert auf der Skala finden
                    new_value_on_scale = min(
                        self.controllers[controller_name]["values_on_scale"],
                        key = lambda x: abs(x - exact_new_value),
                    )

                    # Neuen Wert einspeichern
                    self.controllers[controller_name]["current_value"] = new_value_on_scale

                    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!



            # Maus über Slider?
            elif self.is_mouse_over_rect(rect_slider):

                # Aktuellen Wert neben Maus zeichnen
                rescaled_mouse_value = rescale(
                                mouse_y_screen_pos,
                                slider_y_origin,
                                slider_y_end,
                                attribute_min,
                                attribute_max,
                            )
                rescaled_mouse_value = min(
                    self.controllers[controller_name]["values_on_scale"],
                    key = lambda x: abs(x - rescaled_mouse_value),
                )
                self.draw_text_new(
                    str(rescaled_mouse_value),
                    mouse_x_screen_pos - 10,
                    mouse_y_screen_pos - 20,
                    self.font_small,
                )

                # Wenn ein Doppelklick gemacht wird
                if self.buttons["mouse_left"] == "double_click":

                    # Wenn kein Sweeping-Ziel gerade angegeben ist
                    if not self.controllers[controller_name]["sweep_value_y_screen_pos"]:

                        # Sweeping-Ziel einspeichern
                        self.controllers[controller_name]["sweep_value_y_screen_pos"] = mouse_y_screen_pos

                        # Slider-Sweep-Wert in Sweep-Wert auf Original-Skala übersetzen
                        exact_sweep_value = rescale(
                            mouse_y_screen_pos,
                            slider_y_origin,
                            slider_y_end,
                            attribute_min,
                            attribute_max,
                        )

                        # Nächste Zahl dazu auf Skala finden und einspeichern
                        self.controllers[controller_name]["sweep_value"] = min(
                            self.controllers[controller_name]["values_on_scale"],
                            key=lambda x: abs(x-exact_sweep_value),
                        )

                    # Wenn eins Sweeping-Ziel da ist
                    else:
                        # löschen
                        self.controllers[controller_name]["sweep_value_y_screen_pos"] = None
                        self.controllers[controller_name]["sweep_value"] = None

            # Maus über value+1-button?
            elif self.is_mouse_over_rect(rect_button_value_up):
                if self.buttons["mouse_left"] in ["single_click", "double_click"]:
                    self.controllers[controller_name]["current_value"] += increment
                    if self.controllers[controller_name]["current_value"] > attribute_max:
                        self.controllers[controller_name]["current_value"] = attribute_max

            # Maus über value-1-button?
            elif self.is_mouse_over_rect(rect_button_value_down):
                if self.buttons["mouse_left"] in ["single_click", "double_click"]:
                    self.controllers[controller_name]["current_value"] -= increment
                    if self.controllers[controller_name]["current_value"] < attribute_min:
                        self.controllers[controller_name]["current_value"] = attribute_min

            # Maus über sweepvalue+1-button?
            elif self.is_mouse_over_rect(rect_button_sweep_value_down):
                if self.buttons["mouse_left"] in ["single_click", "double_click"]:
                    if self.controllers[controller_name]["sweep_value"] != None:
                        self.controllers[controller_name]["sweep_value"] -= increment


            # Maus über sweepvalue-1-button?
            elif self.is_mouse_over_rect(rect_button_sweep_value_up):
                if self.buttons["mouse_left"] in ["single_click", "double_click"]:
                    if self.controllers[controller_name]["sweep_value"] != None:
                        self.controllers[controller_name]["sweep_value"] += increment

            # Sweep-Wert in Slider-Wert übersetzen
            if self.controllers[controller_name]["sweep_value"] != None:
                self.controllers[controller_name]["sweep_value_y_screen_pos"] = rescale(
                    self.controllers[controller_name]["sweep_value"],
                    attribute_min,
                    attribute_max,
                    slider_y_origin,
                    slider_y_end,
                )

            # neuen Attribut-Wert dem kontrollierten Objekt übermitteln
            setattr(instance_or_class, attribute_name, self.controllers[controller_name]["current_value"])


        ################################################################################################################
        # Automatisierung der Slider (Sweep-Values)
        ################################################################################################################

        # Wenn ein Sweep-Value eingegeben wurde
        if self.controllers[controller_name]["sweep_value"]:
            # Wenn die Maus nicht im Controlling-Window ist
            if not self.is_mouse_in_controlling_window():
                if abs(self.controllers[controller_name]["current_value"] - self.controllers[controller_name]["sweep_value"]) <= increment:
                    self.controllers[controller_name]["current_value"] = self.controllers[controller_name]["sweep_value"]
                    self.controllers[controller_name]["sweep_value"] = None
                    self.controllers[controller_name]["sweep_value_y_scren_pos"] = None

                elif self.controllers[controller_name]["sweep_value"] > self.controllers[controller_name]["current_value"]:
                    self.controllers[controller_name]["current_value"] += increment
                elif self.controllers[controller_name]["sweep_value"] < self.controllers[controller_name]["current_value"]:
                    self.controllers[controller_name]["current_value"] -= increment
                else:
                    self.controllers[controller_name]["sweep_value"] = None
                    self.controllers[controller_name]["sweep_value_y_scren_pos"] = None

            # neuen Attribut-Wert dem kontrollierten Objekt übermitteln
            setattr(instance_or_class, attribute_name, self.controllers[controller_name]["current_value"])

    ####################################################################################################################
    # Pygame-Hilfsfunktionen
    ####################################################################################################################

    def is_mouse_over_rect(self, rect):
        """
        Überprüft, ob sich die Maus aktuell im Bereich des eingegebenen Rechteckes befindet.
        Die Informationen über das Rechteck haben die typischen Pygame-Struktur: (x-pos, y-pos, x-len, y-len)
        """
        rect_x_pos, rect_y_pos, rect_width, rect_height = rect[0], rect[1], rect[2], rect[3]
        mouse_x_screen_pos, mouse_y_screen_pos = pygame.mouse.get_pos()
        if rect_x_pos <= mouse_x_screen_pos <= rect_x_pos + rect_width:
            if rect_y_pos <= mouse_y_screen_pos <= rect_y_pos + rect_height:
                return True
            else:
                return False
        else:
            return False

    def is_mouse_in_controlling_window(self):
        return self.is_mouse_over_rect((
            self.controlling_window_x_origin - self.screen_gap,
            0,
            self.controlling_window_width + self.screen_gap * 2,
            self.screen_height,
        )
        )

    def draw_text(
            self,
            text,
            x_screen_pos,
            y_screen_pos,
            color_from_my_colors_dict = "black",
    ):
        text = self.font1.render(text, False, self.colors[color_from_my_colors_dict])
        self.screen.blit(text, (x_screen_pos, y_screen_pos))

    def draw_text_new(
            self,
            text,
            x_screen_pos,
            y_screen_pos,
            font,
            color_from_my_colors_dict = "black",
    ):
        if type(color_from_my_colors_dict) == str:
            color = self.colors[color_from_my_colors_dict]
        else:
            color = color_from_my_colors_dict

        text_surface = font.render(text, True, color)
        #text_rect = text_surface.get_rect()
        self.screen.blit(text_surface, (x_screen_pos, y_screen_pos))

    ####################################################################################################################
    # Update
    ####################################################################################################################

    def update_screen(self):

        self.update_pygame_events()

        ################################################################################################################
        # Solange Maus im Controlling-Window ist

        mouse_in_controlling_window = self.is_mouse_in_controlling_window()

        while mouse_in_controlling_window or self.display_speed <= 0:

            # Pygame-Events checken
            self.update_pygame_events()
            mouse_in_controlling_window = self.is_mouse_in_controlling_window()



            # Controlling-Window füllen
            self.screen.fill(
                self.BACKGROUND_COLOR,
                (self.controlling_window_x_origin - self.screen_gap,
                 0,
                 self.controlling_window_width + self.screen_gap * 2,
                 self.screen_height,
                 )
            )

            # Controller aktualisieren/malen (obwohl alles außer dem Controller-Window still steht)
            for controller_name in self.controllers:
                self.control(
                    controller_name,
                    self.controllers[controller_name]["controlled_object"],
                    self.controllers[controller_name]["attribute_name"],
                    self.controllers[controller_name]["attribute_min"],
                    self.controllers[controller_name]["attribute_max"],
                )

            self.draw_text_new(
                "PAUSE",
                self.simulation_window_x_origin + self.simulation_window_width // 2,
                0 + self.screen_gap // 4,
                self.font_medium,
            )

            # Tick-darstellen
            self.draw_text_new(
            "tick: " + str(self.tick),
            self.simulation_window_x_origin,
            0 + self.screen_gap // 4,
            self.font_medium,
            )

            # Screen aktualisieren
            pygame.display.flip()
            self.clock.tick(10000)


        ################################################################################################################
        # Wenn Maus außerhalb des Controller-Windows ist


        # Tick-darstellen
        self.draw_text_new(
            "tick: " + str(self.tick),
            self.simulation_window_x_origin,
            0 + self.screen_gap // 4,
            self.font_medium,
        )

        # Tick aktualisieren
        self.tick += 1

        # Screen aktualisieren
        pygame.display.flip()

        # Gesamtes Fenster füllen
        self.screen.fill(self.BACKGROUND_COLOR)

        self.clock.tick(self.display_speed)