import pandas as pd
import googlemaps
from datetime import datetime
from analysis.google_api_request import get_google_distances


def get_google_api():
    """
    This function gets the Google API key from Google_distance_API_key.txt file.
    Google_distance_API_key.txt has to contain the key that will be used
    Returns:
        user_api_key (str): Google Distance Matrix API key
    """
    GoogleAPI_fn = "Google_distance_API_key.txt"
    with open(GoogleAPI_fn, "r") as file:
        user_api_key = file.readline().strip()
    return user_api_key


def get_distance_data(test=""):
    """
    This function calls get_google_distances to use Google Distance Matrix API
    and get the distance in km and time (minutes) from each census tract centroid
    to each of its assigned chilcare centers. Then, saves the data into a csv
    file
    """
    # Open data as pandas
    ct_three_ccc = pd.read_csv("data/intermediate_data_backup.csv")

    # Get Google Distance Matrix API key
    user_api_key = get_google_api()

    # Get distance variables and add them to the dataframe
    get_google_distances(
        ct_three_ccc,
        "distance_km",
        "distance_minutes",
        "latitude",
        "longitude",
        user_api_key,
    )

    # Save data as csv
    ct_three_ccc.to_csv(test + "data/census_ccc_joined_backup.csv", index=True)
