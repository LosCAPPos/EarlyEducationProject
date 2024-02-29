from analysis.hav_distance import haversine_distance
from analysis.google_api_request import get_google_distances
import numpy as np
import googlemaps
from datetime import datetime


"""
from analysis.hav_distance import haversine_distance
import numpy as np
import pandas as pd

attribute = 'distance_min'
n_child_center = 1
df = pd.read_csv("data/census_ccc_joined.csv")

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


def new_center_first_in_table(df, attribute, n_child_center):
    """
    Takes a child center dataframe "df" that has data at a census tract level
    and (at least) a column "attribute" for each census tract. Having
    "attribute" as a reference, assigns a child center to the census tract that
    has the highest value for "attribute" in the dataframe, and recalculates the
    "attribute" in the dataframe for each census tract that is close to that new
    child center.
    """
    # sort the dataframe by census tract and "attribute"
    df = df.sort_values(
        by=["GEOID", attribute], ascending=[True, True], na_position="last"
    )
    # keep the reference for the n_child_center
    df = df.groupby("GEOID").apply(
        lambda x: x.iloc[n_child_center - 1], include_groups=False
    )
    # sort the dataframe by lowest access and reset index
    # NOTE: Use this with the variable related to access
    df = df.sort_values(by=[attribute], ascending=[False])
    df = df.reset_index(drop=True)

    # generate comparison columns with coordinates of the census tract with
    # highest "attribute"
    lat_comparison_column = "new_center_latitude"
    lon_comparison_column = "new_center_longitude"
    df[lat_comparison_column], df[lon_comparison_column] = (
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
    df["to_analyze"] = df["distance_new_center"] < 1.5 * df["hdistance"]

    # don't analyze first observation (there will be a child center there)
    df.iloc[0, df.columns.get_loc("to_analyze")] = False

    # (i) define name of new columns and apply distance request in googlemaps
    new_km_distance_column = "new_km_distance"
    new_min_distance_column = "new_min_distance"
    get_google_distances(
        df,
        new_km_distance_column,
        new_min_distance_column,
        lat_comparison_column,
        lon_comparison_column,
        limit_analysis=True,
    )

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


def get_google_distances(
    df,
    new_km_distance_column,
    new_min_distance_column,
    lat_comparison_column,
    lon_comparison_column,
    user_api_key,
    limit_analysis=False,
):
    """
    Use Google Directions API to get the distance in km and time (minutes) from
    each census tract centroid to the latitude and longitude column defined
    in "lat_comparison_column" and "lon_comparison_column".
    """
    GoogleAPI_fn = "Google_distance_API_key.txt"

    with open(GoogleAPI_fn, "r") as file:
        api_key = file.readline().strip()
        api_key = user_api_key

    # Create empty coluns to be filled
    df[new_km_distance_column] = 0.0
    df[new_min_distance_column] = 0.0

    # Define options for google maps
    gmaps = googlemaps.Client(key=api_key)
    arrival_time = datetime(2024, 4, 11, 9, 0)

    # Set counter and maximum count as an additional stop condition
    counter = 0
    if limit_analysis:
        max_count = len(df[df["to_analyze"]])
    else:
        max_count = len(df)

    for i, row in df.iterrows():
        # i. if the analysis limited to just some rows
        if limit_analysis:
            # if it is limited, should we analyze this row specifically
            if not row["to_analyze"]:
                # don't make a request for this row, continue with following row
                df.loc[i, new_km_distance_column] = "NaN"
                df.loc[i, new_min_distance_column] = "NaN"
                continue

        # Update counter of requests
        counter += 1

        # Specify origin and destination coordinates
        origin = (row["centroid_lat"], row["centroid_lon"])  # census tract centroid
        destination = (
            row[lat_comparison_column],
            row[lon_comparison_column],
        )  # comparison latitude and longitude

        # Make distance matrix request
        result = gmaps.distance_matrix(
            origin, destination, mode="driving", arrival_time=arrival_time
        )

        # if the request was a success, get the values
        if result["rows"][0]["elements"][0]["status"] == "OK":
            # Extract distance value in meters and duration value in time
            distance_in_meters = result["rows"][0]["elements"][0]["distance"]["value"]
            duration_in_seconds = result["rows"][0]["elements"][0]["duration"]["value"]
            # Convert distance to kilometers and duration to minutes
            df.loc[i, new_km_distance_column] = distance_in_meters / 1000
            df.loc[i, new_min_distance_column] = duration_in_seconds / 60

        # request was not a success, assign "NaN"
        else:
            df.loc[i, new_km_distance_column] = "NaN"
            df.loc[i, new_min_distance_column] = "NaN"

        if counter == max_count:
            break
