import numpy as np

EARTH_R_MI = 3963

# NOTE: This python file is the one that was used in #PA3 of the course
# (CAPP 30122) but with numpy instead of math to apply formulas to pandas
# dataframes


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points on a sphere (like Earth) in miles.

    https://en.wikipedia.org/wiki/Haversine_formula

    Inputs:
        lat1 (float): latitude of first point
        lon1 (float): longitude of first point
        lat2 (float): latitude of second point
        lon2 (float): longitude of second point

    Return (float): distance in miles
    """
    # conversion of input variables to radians
    lat1, lon1 = np.radians(lat1), np.radians(lon1)
    lat2, lon2 = np.radians(lat2), np.radians(lon2)

    # application of the haversine formula and return
    aux_parenthesis = np.sqrt(
        np.sin((lat2 - lat1) / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    )
    distance = 2 * EARTH_R_MI * np.arcsin(aux_parenthesis) * 1.60934 # in km

    return distance
