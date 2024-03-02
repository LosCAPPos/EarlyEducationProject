from analysis.hav_distance import haversine_distance
from analysis.google_api_request import get_google_distances
import numpy as np


"""
from analysis.hav_distance import haversine_distance
from analysis.google_api_request import get_google_distances
import numpy as np
import pandas as pd

attribute = 'distance_min'
n_child_center = 1
#df = pd.read_csv("data/census_ccc_joined.csv")
df = pd.read_csv("data/data_pre_merge.csv")

new_km_distance_column = "new_km_distance"
new_min_distance_column = "new_min_distance"
lat_comparison_column = "new_center_latitude"
lon_comparison_column = "new_center_longitude"

df[df["to_analyze"]]

trial = google_distances(
    df,
    new_km_distance_column,
    new_min_distance_column,
    lat_comparison_column,
    lon_comparison_column,
    limit_analysis=True,
)

"""


def new_center_first_in_table(df, n_child_center, user_api_key):
    """
    Takes a child center dataframe "df" that has data at a census tract level
    and a column related to distance in minutes for each census tract.
    Having distance in minutes as a reference, assigns a child center to the
    census tract that has the less access in the dataframe, and recalculates the
    distance in kilometers and minutes to the closest child center for each
    census tract (because they can be benefited by the new child center).
    """
    # return variables: impact in reduced kilometers and reduced minutes
    total_impact_km = 0
    total_impact_min = 0
    benefited_census_tracts = []

    # sort the dataframe by census tract and distance in minutes
    df = df.sort_values(
        by=["TRACTCE", "distance_min_imp"], ascending=[True, True], na_position="last"
    )
    # keep the reference for the n_child_center
    df = df.groupby("TRACTCE").apply(
        lambda x: x.iloc[n_child_center - 1], include_groups=False
    )
    # sort the dataframe by lowest access and reset index
    df = df.sort_values(by=["distance_min_imp"], ascending=[False])
    df = df.reset_index(drop=True)

    # generate comparison columns with coordinates of the census tract with
    # highest distance in minutes
    lat_comparison_column = "new_center_latitude"
    lon_comparison_column = "new_center_longitude"
    df[lat_comparison_column], df[lon_comparison_column] = (
        df["centroid_lat"][0],
        df["centroid_lon"][0],
    )

    # calculate (haverstine) distance from each census tract to the new center
    df = df.assign(
        hdistance_new_center=haversine_distance(
            df["centroid_lat"].astype(float),
            df["centroid_lon"].astype(float),
            df["new_center_latitude"].astype(float),
            df["new_center_longitude"].astype(float),
        )
    )

    # if distance to the new center less than 1.5 respect to current maximum
    # distance, analyze it. Otherwise, assume that the new center will not be
    # the closest center. This is due to limits of google requests.
    df["to_analyze"] = df["hdistance_new_center"] < 1.5 * df["hdistance_min"]

    # don't analyze with google maps first census tract (there will be a child
    # center there) and refresh child center parameters for that census tract
    df.loc[0, "to_analyze"] = False
    benefited_census_tracts.append(df.loc[0, "GEOID"])
    total_impact_km += df.loc[0, "hdistance_min"] - 0.1
    total_impact_min += df.loc[0, "distance_min_imp"] - 1
    df.loc[0, "hdistance_min"] = 0.1
    df.loc[0, "distance_min_imp"] = 1
    df.loc[0, "population"] += 50

    # define name of new columns and apply distance request in googlemaps
    new_km_distance_column = "new_km_distance"
    new_min_distance_column = "new_min_distance"
    get_google_distances(
        df,
        new_km_distance_column,
        new_min_distance_column,
        lat_comparison_column,
        lon_comparison_column,
        user_api_key,
        limit_analysis=True,
    )

    # for each analyzed census tract, if new time is lower than current value
    # assign new center as closest center
    for index, row in df.iterrows():
        if row["to_analyze"] and row["new_min_distance"] < row["distance_min_imp"]:
            benefited_census_tracts.append(df.loc[index, "GEOID"])
            total_impact_km += (
                df.loc[index, "hdistance_min"] - row["hdistance_new_center"]
            )
            total_impact_min += df.loc[0, "distance_min_imp"] - row["new_min_distance"]
            df.loc[index, "hdistance_min"] = row["hdistance_new_center"]
            df.loc[index, "distance_min_imp"] = row["new_min_distance"]

    return df, benefited_census_tracts, total_impact_km, total_impact_min


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
