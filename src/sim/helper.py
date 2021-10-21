import datetime
import math
import random
from typing import List, Optional

import pandas as pd


def dates_between(date1: datetime.date, date2: datetime.date) -> List[datetime.date]:
    day_diff = (date2 - date1).days
    dates = [date1 + datetime.timedelta(days = i) for i in range(day_diff + 1)]
    return dates


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