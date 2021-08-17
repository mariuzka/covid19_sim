import datetime
import math
import random
from typing import List

def dates_between(date1: datetime.date, date2: datetime.date) -> List[datetime.date]:
    """
    FUNCTION
    Returns all dates between the given dates incl. the given dates
    
    INPUT
    date1: start date (object type: datetime.date)
    date2: end date (object type: datetime.date)
    
    OUTPUT
    dates: list of dates between the given dates incl. the given dates
    """
    day_diff = (date2 - date1).days
    dates = [date1 + datetime.timedelta(days = i) for i in range(day_diff + 1)]
    return dates


# translates one scale into another scale
def rescale(val, min1, max1, min2, max2):
    if min1 != max1:
        rescaled_val = (((val - min1) / (max1 - min1)) * (max2 - min2)) + min2

        if rescaled_val > max2:
            return max2
        elif rescaled_val < min2:
            return min2
        else:
            return rescaled_val
    else:
        return val

def random_color(*args):
    r = random.randint(5, 250)
    g = random.randint(5, 250)
    b = random.randint(5, 250)
    color = (r, g, b)
    return color

def squared_distance(dim_pos1, dim_pos2):
    return (dim_pos1 - dim_pos2) ** 2

def squared_distance_via_edge(dim_pos1, dim_pos2, dim_len):
    return subtract_via_edge(dim_pos1, dim_pos2, dim_len) ** 2

def squared_distance_on_torus(dim_pos1, dim_pos2, dim_len):
    return min([squared_distance(dim_pos1,dim_pos2),                     # "Direkte" Distanz
                squared_distance_via_edge(dim_pos1, dim_pos2, dim_len),  # "Indirekte" Distanz über Rand
                ])

def euclidian_distance(x_pos1, y_pos1, x_pos2, y_pos2, x_dim_len, y_dim_len, torus = True):
    if torus:
        return math.sqrt(squared_distance_on_torus(x_pos1, x_pos2, x_dim_len) + squared_distance_on_torus(y_pos1, y_pos2, y_dim_len))
    else:
        return math.sqrt((x_pos1 - x_pos2) ** 2 + (y_pos1 - y_pos2) ** 2)


def subtract_via_edge(dim_pos1, dim_pos2, dim_len):
    if dim_pos1 > dim_pos2:                      # Wenn dim_pos1 "rechts" von dim_pos2
        return (dim_len - dim_pos1) + dim_pos2   # Distanz/Differenz über rechten Rand berechnen

    else:                                        # Wenn dim_pos1 "links" von dim_pos2
        return (dim_pos2 - dim_len) - dim_pos1   # Distanz/Differenz über linken Rand berechnen



def shortest_distance_to_target(
        my_dim_pos,
        target_dim_pos,
        dim_len,
        torus = True,
        ):
    """
    Berechnet, die kürzeste Distanz zu einem Ziel.
    Wenn die Distanz rechtsherum kürzer ist, dann ist das Ziel rechts.
    Wenn die Distanz linksherum kürzer ist, dann ist das Ziel links.

    Die Distanz kann positiv oder negativ sein!
    Eine positive Distanz heißt, das Ziel ist "rechts" von mir.
    Eine negative Distanz heißt, das Ziel ist "linkes" von mir.
    """

    # Direkte Distanz "vornerum" (d.h. nicht über den Rand)
    direct_distance = target_dim_pos - my_dim_pos

    if torus:
        if my_dim_pos >= target_dim_pos:
            edge_distance = target_dim_pos + dim_len - my_dim_pos
        else:
            edge_distance = -(my_dim_pos + dim_len - target_dim_pos)

        if abs(direct_distance) <= abs(edge_distance):
            return direct_distance
        else:
            return edge_distance

    else:
        return direct_distance




def direction_to_target(my_dim_pos, target_dim_pos, dim_len, torus=True):

    """
    Berechnet die Richtung zu einem Ziel auf einer Dimension.
    Wenn das Ziel "rechts" von einem ist, dann ist die Richtung positiv d.h. Richtung = 1.
    Wenn das Ziel "links" von einem ist, dann ist die Richtung negativ d.h. Richtung = -1.
    Wenn das Ziel gleich meiner eigenen Position ist, dann ist die Richtung = 0.
    """
    if target_dim_pos == my_dim_pos:  # Wenn man eh schon auf derselben Position auf der X-Dimension ist,
        return 0  # dann muss man auf dieser Dimensionen keinen Schritt machen
    else:
        # Den "Richtungsvektor" berechnen
        direction = shortest_distance_to_target(my_dim_pos, target_dim_pos, dim_len, torus)

        # Wenn die Richtung positiv ist (nach "rechts"), dann mache einen positiven Schritt,
        # wenn die Richtung negativ ist (nach "links"), dann einen negativen Schritt
        return (1 if direction > 0 else -1)
