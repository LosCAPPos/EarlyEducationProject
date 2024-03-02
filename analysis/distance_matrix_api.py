import pandas as pd
import googlemaps
from datetime import datetime

"""
Use Google Directions API to get the distance in km and time (minutes) from
each census tract centroid to each of its assigned chilcare centers
"""
# Open data as pandas (just in case)
ct_three_ccc = pd.read_csv('../data/intermediate_data_backup.csv')

"""
# Read api_key from .txt (needs to be filled)
GoogleAPI_fn = "Google_distance_API_key.txt"
with open(GoogleAPI_fn, "r") as file:
    user_api_key = file.readline().strip()
"""

# Create empty coluns to be filled
ct_three_ccc['distance_km'] = 0.0
ct_three_ccc['distance_minutes'] = 0.0

gmaps = googlemaps.Client(key = user_api_key)
arrival_time = datetime(2024, 4, 11, 9, 0)

# Set additional counter as an additional stop condition
counter = 0

for i, row in ct_three_ccc.iterrows():
    # Specify origin and destination coordinates
    origin = (row['centroid_lat'], row['centroid_lon'])  # Census tract centroid
    destination = (row['latitude'], row['longitude'])  # CCC coordinates

    # Make distance matrix request
    result = gmaps.distance_matrix(origin, destination, mode = 'driving', arrival_time = arrival_time)

    if result['rows'][0]['elements'][0]['status'] == 'OK':
        # Extract the distance value in meters
        distance_in_meters = result['rows'][0]['elements'][0]['distance']['value']
        # Extract the distance value in time
        duration_in_seconds = result['rows'][0]['elements'][0]['duration']['value']

        # Convert distance to kilometers
        ct_three_ccc.loc[i, 'distance_km'] = distance_in_meters / 1000
        # Convert duration to minutes
        ct_three_ccc.loc[i, 'distance_minutes'] = duration_in_seconds / 60
    else:
        ct_three_ccc.loc[i, 'distance_km'] = 'NaN'
        ct_three_ccc.loc[i, 'distance_minutes'] = 'NaN'

    # Update counter
    counter += 1

    if counter == len(ct_three_ccc):
        break

# Save data as csv
ct_three_ccc.to_csv('../data/census_ccc_joined_backup.csv', index = True)