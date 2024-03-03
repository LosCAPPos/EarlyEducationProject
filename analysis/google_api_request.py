import googlemaps
from datetime import datetime


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
    each census tract centroid to the latitude and longitude columns defined
    in "lat_comparison_column" and "lon_comparison_column".
    """
    # Connect and define options for API
    gmaps = googlemaps.Client(key=user_api_key)
    arrival_time = datetime(2024, 4, 11, 9, 0)

    # Create empty columns to be filled
    df[new_km_distance_column] = 0.0
    df[new_min_distance_column] = 0.0

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
        )  # latitude and longitude comparison

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
