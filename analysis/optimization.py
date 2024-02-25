# import pandas as pd
from analysis.hav_distance import haversine_distance
import numpy as np


def new_center_first_in_table(df, attribute):
    """
    Takes a child center dataframe "df" that has data at a census tract level
    and (at least) a column "attribute" for each census tract. Having
    "attribute" as a reference, assigns a child center to the census tract that
    has the highest value for "attribute" in the dataframe, and recalculates the
    "attribute" in the dataframe for each census tract that is close to that new
    child center.
    """
    # sort the dataframe and reset index
    df = df.sort_values(attribute, ascending=False)
    df = df.reset_index(drop=True)

    # generate columns X, Y with coordinates of the census tract with highest
    # "attribute"
    df["new_center_latitude"], df["new_center_longitude"] = (
        df["latitude"][0],
        df["longitude"][0],
    )

    # calculate (haverstine) distance from each census tract to the new center
    df = df.assign(
        distance_new_center=haversine_distance(
            df["latitude"].astype(float),
            df["longitude"].astype(float),
            df["new_center_latitude"].astype(float),
            df["new_center_longitude"].astype(float),
        )
    )

    # if distance to the new center less than 1.5 respect to current maximum
    # distance, analyze it. Otherwise, assume that the new center will not be
    # the closest center. This is due to limits of google requests.
    # NOTE: CHANGE "new_center_latitude"
    df["to_analyze"] = df["distance_new_center"] < 1.5 * df["new_center_latitude"]

    # (i) apply request of time in googlemaps
    # (ii) for each census tract, if new time is lower than current value
    # assign new time to closest center and replace center


def optimization_new_center_distance_overall_impact(df, attribute):
    """ """
    # sort the dataframe and reset index
    df = df.sort_values(attribute, ascending=False)
    df = df.reset_index(drop=True)

    # check what is the census tract that would have the biggest overall impact
    # reducing the distance if it has a new child center.
    optimum_row_index = 0
    aux_highest_impact = 0
    # for effiency, just check in the first 20 census tracts (highest
    # probability to have a higher impact)
    for row_index in range(20):
        impact = new_center_distance_overall_impact(df, attribute, row_index)
        if impact > aux_highest_impact:
            aux_highest_impact = impact
            optimum_row_index = row_index

    return optimum_row_index


def new_center_distance_overall_impact(df, attribute, row_index):
    """ """
    # generate columns X, Y with coordinates of census tract in row row_index
    df["new_center_latitude"], df["new_center_longitude"] = (
        df["latitude"][row_index],
        df["longitude"][row_index],
    )

    # calculate (haverstine) distance from each census tract to potential new
    # center
    df = df.assign(
        distance_new_center=haversine_distance(
            df["latitude"],
            df["longitude"],
            df["new_center_latitude"],
            df["new_center_longitude"],
        )
    )

    # potential changes in distance to closest center for each census tract
    # NOTE: CHANGE "new_center_latitude"
    df["reduced_distance"] = np.where(
        df["new_center_latitude"] - df["distance_new_center"] > 0,
        df["new_center_latitude"] - df["distance_new_center"],
        0,
    )

    # return average reduced distance
    return df["reduced_distance"].mean()
