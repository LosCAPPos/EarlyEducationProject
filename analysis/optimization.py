from analysis.hav_distance import haversine_distance
from analysis.google_api_request import get_google_distances
from analysis.distance_matrix_api import get_google_api
import numpy as np
import pandas as pd


def create_several_child_centers(user_api_key, number_child_centers, optimized):
    """
    Establishes where to put a defined number of child centers (number of
    iterations) in Illinois using the distance in minutes between the centroid
    of the census tract and the closest child center as a reference.

    Inputs:
        user_api_key (str): key of google distance matrix API
        number_child_centers (int): number of new child centers to allocate
        optimized (bool): if False, allocate the new child center in the census
            tract with less access. if True, allocate the new child center in
            the census tract that has the higher estimated impact in the
            dataframe as a whole

    Returns (tuple): a tuple with 6 variables:
        ranking_lst (lst): List with the ranking value (int) of the census
            tracts related to their previous distance to closest child
            center
        single_impact_km (lst): List with the impact in reduced kilometers
            (float) to the closest child center for each new child center
            in the whole dataframe
        single_impact_min (lst): List with the impact in reduced minutes (float)
            to the closest child center for each child center in the
            whole dataframe
        total_benefited_ct (lst): List with the benefited census tracts (list of
            integers) related to each new child center
        total_impact_km (float): total impact in reduced kilometers (float) to
            the closest child center related to the new child centers
        total_impact_min (float): total impact in reduced minutes (float) to the
            closest child center related to the new child centers
    """
    # import database
    df = pd.read_csv("data/final_data_merged.csv")
    
    if user_api_key == "API_KEY":
        user_api_key = get_google_api()

        # auxiliar variables to return
    total_benefited_ct = []
    single_impact_km = []
    single_impact_min = []
    ranking_lst = []
    total_impact_km = 0
    total_impact_min = 0

    # iteration to allocate each new child center
    for _ in range(number_child_centers):
        df, benefited_ct, impact_km, impact_min, ranking = create_new_center(
            df, user_api_key, optimized
        )
        ranking_lst.append(ranking + 1)
        total_benefited_ct.append(benefited_ct)
        single_impact_km.append(impact_km)
        single_impact_min.append(impact_min)
        total_impact_km += impact_km
        total_impact_min += impact_min

    return (
        ranking_lst,
        single_impact_km,
        single_impact_min,
        total_benefited_ct,
        total_impact_km,
        total_impact_min,
    )


def create_new_center(df, user_api_key, optimized):
    """
    Takes a child center dataframe "df" that has data at a census tract level
    and a column related to distance in minutes for each census tract.
    Having distance in minutes as a reference, assigns one child center to a
    census tract, and recalculates the distance in kilometers and minutes to
    the closest child center for each census tract.

    Inputs:
        df (pandas df): the pandas dataframe
        user_api_key (str): key of google distance matrix API
        optimized (bool): if False, allocate the new child center in the census
            tract with less access. if True, allocate the new child center in
            the census tract that has the higher estimated impact in the
            dataframe as a whole

    Returns (tuple): a tuple with 5 variables:
        df (pandas df): pandas dataframe with the new child center on it
        benefited_ct (lst): benefited census tracts (list of
            integers) related to the new child center
        impact_km (float): impact in reduced kilometers (float) that the new
            child center would have in the whole dataframe
        impact_min (float): impact in reduced minutes (float) that the new child
            center would have in the whole dataframe
        ranking (int): ranking value (int) of the census tract related to its
            previous distance to the closest child center
    """
    if user_api_key == "API_KEY":
        user_api_key = get_google_api()
    
    # return variables: impact in reduced kilometers and reduced minutes
    impact_km = 0
    impact_min = 0
    benefited_ct = []

    # sort the dataframe by lowest access and reset index
    df = df.sort_values(by=["distance_min_imp"], ascending=[False])
    df = df.reset_index(drop=True)

    # if optimized, take row (ranking) from the census tract that has the highest
    # expected impact, otherwise, take first row of df (longest distance in minutes)
    if optimized:
        ranking = optimization_new_center_distance_overall_impact(df)
    else:
        ranking = 0

    # generate comparison columns with coordinates of the census tract with
    # highest distance in minutes
    df["new_center_lat"], df["new_center_lon"] = (
        df["centroid_lat"][ranking],
        df["centroid_lon"][ranking],
    )

    # calculate (haverstine) distance from each census tract to the new center
    df = df.assign(
        hdistance_new_center=haversine_distance(
            df["centroid_lat"].astype(float),
            df["centroid_lon"].astype(float),
            df["new_center_lat"].astype(float),
            df["new_center_lon"].astype(float),
        )
    )

    # if distance to the new center less than 1.5 current maximum distance,
    # analyze it. Otherwise, assume that new center will not be closest center.
    # This is done due to limits of google requests.
    df["to_analyze"] = df["hdistance_new_center"] < 1.5 * df["hdistance_min"]

    # don't analyze with google maps first census tract (there will be a child
    # center there) and set child center parameters for that census tract
    df.loc[0, "to_analyze"] = False
    benefited_ct.append(df.loc[0, "GEOID"])
    impact_km += df.loc[0, "hdistance_min"] - 0.1
    impact_min += df.loc[0, "distance_min_imp"] - 1
    df.loc[0, "hdistance_min"] = 0.1
    df.loc[0, "distance_min_imp"] = 1
    df.loc[0, "population"] += 50

    # define name of new columns and apply distance request in googlemaps
    get_google_distances(
        df,
        "new_km_distance",
        "new_min_distance",
        "new_center_lat",
        "new_center_lon",
        user_api_key,
        limit_analysis=True,
    )

    # for each analyzed census tract, if new time is lower than current value
    # assign new center as closest center
    for index, row in df.iterrows():
        if row["to_analyze"] and row["new_min_distance"] < row["distance_min_imp"]:
            benefited_ct.append(df.loc[index, "GEOID"])
            impact_km += df.loc[index, "hdistance_min"] - row["hdistance_new_center"]
            impact_min += df.loc[index, "distance_min_imp"] - row["new_min_distance"]
            df.loc[index, "hdistance_min"] = row["hdistance_new_center"]
            df.loc[index, "distance_min_imp"] = row["new_min_distance"]

    # drop helper columns created by the function
    df = df.drop(
        columns=[
            "new_center_lat",
            "new_center_lon",
            "hdistance_new_center",
            "to_analyze",
            "new_km_distance",
            "new_min_distance",
        ]
    )

    return df, benefited_ct, impact_km, impact_min, ranking


def optimization_new_center_distance_overall_impact(df):
    """
    Takes a pandas dataframe that has data at a census tract level and a column
    related to distance in minutes to closest child center by census tract.
    Estimates in what census tract a new center would have the highest impact
    in the whole dataframe in terms of haversine distance to the
    closest child center.

    Inputs:
        df (pandas df): the pandas dataframe with data at a census tract level

    Returns (int): index of the row of the dataframe that has the
            census tract with the highest impact estimate
    """
    # sort the dataframe and reset index
    df = df.sort_values("distance_min_imp", ascending=False)
    df = df.reset_index(drop=True)

    # check what is the census tract that would have the biggest overall impact
    # reducing the distance if it has a new child center.
    optimum_row_index = 0
    aux_highest_impact = 0
    # for effiency, just check in the first 150 census tracts (highest
    # probability to have a higher impact)
    for row_index in range(150):
        impact = new_center_distance_overall_impact(df, row_index)
        if impact > aux_highest_impact:
            aux_highest_impact = impact
            optimum_row_index = row_index

    return optimum_row_index


def new_center_distance_overall_impact(df, row_index):
    """
    Takes a pandas dataframe that has data at a census tract level and a column
    related to distance in minutes to closest child center by census tract.
    Estimates the impact in haversine distance to the closest child center
    in the whole dataframe of a new center in the census tract in row_index.

    Inputs:
        df (pandas df): the pandas dataframe with data at a census tract level
        row_index (int): row index of the dataframe to be evaluated

    Returns (int): impact in haversine distance in the whole dataframe of a new
        center in the census tract related to row_index
    """
    # generate columns X, Y with coordinates of census tract in row row_index
    df["new_center_lat"], df["new_center_lon"] = (
        df["centroid_lat"][row_index],
        df["centroid_lon"][row_index],
    )

    # calculate (haverstine) distance from each census tract to potential new
    # center
    df = df.assign(
        hdistance_new_center=haversine_distance(
            df["centroid_lat"],
            df["centroid_lon"],
            df["new_center_lat"],
            df["new_center_lon"],
        )
    )

    # potential changes in distance to closest center for each census tract
    df["reduced_distance"] = np.where(
        df["hdistance_min"] - df["hdistance_new_center"] > 0,
        df["hdistance_min"] - df["hdistance_new_center"],
        0,
    )

    # return sum reduced distance
    return df["reduced_distance"].sum()
