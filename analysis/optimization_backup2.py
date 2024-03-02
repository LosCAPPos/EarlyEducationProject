import pandas as pd
from analysis.hav_distance import haversine_distance
from analysis.optimization import create_new_center
from analysis.google_api_request import get_google_distances
import numpy as np
import googlemaps
from datetime import datetime


user_api_key = "insert_your_user_api_key"
df = pd.read_csv("data/final_data_merged.csv")
new_centers = 3
total_benefited_ct = []
total_impact_km = 0
total_impact_min = 0
for i in range(new_centers):
    df, benefited_ct, impact_km, impact_min = create_new_center(df, user_api_key, True)
    total_benefited_ct.append(benefited_ct)
    total_impact_km += impact_km
    total_impact_min += impact_min
    print(i)
    print("\n")
    print("benefited ct: ", benefited_ct)
    print("singular impact km: ", impact_km)
    print("singular impact min: ", impact_min)
    print("\n")
    print("total benefited ct: ", total_benefited_ct)
    print("total impact km: ", total_impact_km)
    print("total impact min: ", total_impact_min)
    print("\n")
    print("\n")


###
###
###


gmaps = googlemaps.Client(key=user_api_key)
arrival_time = datetime(2024, 4, 11, 9, 0)
origin = (42.11659, -90.05662)  # Census tract centroid
destination = (42.07957, -90.12149)  # CCC coordinates
result1 = gmaps.distance_matrix(
    origin, destination, mode="driving", arrival_time=arrival_time
)

gmaps = googlemaps.Client(key=user_api_key)
arrival_time = datetime(2024, 4, 11, 9, 0)
origin = (42.11659, -90.05662)  # Census tract centroid
destination = (42.10057, -89.82681)  # CCC coordinates
result2 = gmaps.distance_matrix(
    origin, destination, mode="driving", arrival_time=arrival_time
)


####
####
####

df = pd.read_csv("data/census_ccc_joined_backup.csv")
df = df.iloc[:100]
print("distance original: \n", df["distance_km"].mean())
print("haversine distance original: \n", df["hdistance"].mean())

GoogleAPI_fn = "Google_distance_API_key.txt"
with open(GoogleAPI_fn, "r") as file:
    api_key = file.readline().strip()

gmaps = googlemaps.Client(key=user_api_key)
arrival_time = datetime(2024, 4, 11, 9, 0)

# Create empty coluns to be filled
df["distance_km"] = 0.0
df["distance_minutes"] = 0.0

for i, row in df.iterrows():
    # Specify origin and destination coordinates
    origin = (row["centroid_lat"], row["centroid_lon"])  # Census tract centroid
    destination = (row["latitude"], row["longitude"])  # CCC coordinates

    # Make distance matrix request
    result = gmaps.distance_matrix(
        origin, destination, mode="driving", arrival_time=arrival_time
    )

    if result["rows"][0]["elements"][0]["status"] == "OK":
        # Extract the distance value in meters
        distance_in_meters = result["rows"][0]["elements"][0]["distance"]["value"]
        # Extract the distance value in time
        duration_in_seconds = result["rows"][0]["elements"][0]["duration"]["value"]

        # Convert distance to kilometers
        df.loc[i, "distance_km"] = distance_in_meters / 1000
        # Convert duration to minutes
        df.loc[i, "distance_minutes"] = duration_in_seconds / 60
    else:
        df.loc[i, "distance_km"] = "NaN"
        df.loc[i, "distance_minutes"] = "NaN"

# Check results
print("distance actualizada: \n", df["distance_km"].mean())
print("haversine distance original: \n", df["hdistance"].mean())

# last_rows = df["distance_km"].tail(10)
# print(last_rows)

# Save data as backup
df.to_csv("data/census_ccc_joined_backup_2.csv", index=True)
