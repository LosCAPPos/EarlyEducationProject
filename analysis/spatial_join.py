#!pip install geopandas
#!pip install shapely
#!pip install geopy
#!pip install -U googlemaps

# Import libraries
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from hav_distance import haversine_distance
import googlemaps
from datetime import datetime

# Read and prepare data
ct = gpd.read_file('../data/tl_2023_17_tract/tl_2023_17_tract.shp') # Census Tracts in IL (ct)
ccc_il = pd.read_csv('../data/Child_Care_Centers_clean.csv.csv') # ChilCareCenters in IL (ccc)

# Calculate centroids and add coordinates as new columns to the original 
# census tract Geo DataFrame
ct['centroid'] = ct.geometry.centroid
ct['centroid_lat'] = ct['centroid'].to_crs(epsg=4326).y
ct['centroid_lon'] = ct['centroid'].to_crs(epsg=4326).x
ct['ccc_sum'] = 0

# Set CRS to avoid spatial issues later
ct.crs = 'EPSG:4326'

"""
# Plot results to check centroids were adequately created --> available in ipynb
# Plot the original shapefile
ct.boundary.plot(edgecolor='black', linewidth=0.5)

# Plot the centroids on top
ct['centroid'].plot(marker='o', color='red', markersize=2, ax=plt.gca())

plt.show()
"""

# As ccc came from a csv, it needs to be transformed into a Geo DataFrame
ccc_il_gpd = gpd.GeoDataFrame(ccc_il, geometry=gpd.points_from_xy(ccc_il['longitude'], ccc_il['latitude']))

# Set CRS to avoid spatial issues
ccc_il_gpd.crs = 'EPSG:4326'


## First analysis: Assign each CCC to the census tract it belongs to ##
# Perform a spatial join 
ct_ccc = gpd.sjoin(ccc_il_gpd, ct, how='right', op='within')

# Check results
no_ccc = ct_ccc['objectid'].isna().sum() # How many census tracts don't have any CCC
#print(len(ct_ccc))
#print(no_ccc)
"""
Joined dataframe (ct_ccc) has 4412 obs, including 1522 census tracts that do
not contain any childcare center. Thus, this mechanism may not be the best to 
assign CCC to census tracts.

We will draw a buffer from each census tract centroid and use it to assign CCC
to census tracts. The objective is to identify the three closest CCC to each
census tract centroid. Thus, in case the buffer captures more than three CCC,
haversine_distance will be used to filter the closest three.

A large buffer (45km) was selected to make sure most census tract buffers' would
capture at least three CCC
"""


## Second mechanism: Assign CCC to census tracts using spatial buffers  ##
# Generate Geo DataFrame with centroids and selected variables (needed for further analysis)
selected_ct_columns = ['GEOID', 'centroid', 'centroid_lon', 'centroid_lat']
ct_buffer = gpd.GeoDataFrame(ct[selected_ct_columns], geometry='centroid').copy()

# Generate a 45km buffer for each centroid
ct_buffer['buffer_45'] = ct_buffer['centroid'].buffer(0.008983 * 45)

# Set the geometry column explicitly
ct_buffer = ct_buffer.set_geometry('buffer_45')

# Perform spatial join between buffers and CCC points
buffer_ccc = gpd.sjoin(ccc_il_gpd, ct_buffer[['buffer_45', 'GEOID',
                                              'centroid_lat', 'centroid_lon']],
                                              how = 'left', op = 'within')

# Check results
#print(buffer_ccc['GEOID'].nunique())
#print(len(buffer_ccc))
# All census tracts are included (3265)
# Large data because of large buffer size (2471246)

# Calculate haversine distance for each pair of census tract centroid - CCC
# Filter the three closest for each census tract
buffer_ccc['hdistance'] = buffer_ccc.apply(lambda row: 
                                           haversine_distance(row['latitude'], 
                                                              row['longitude'],
                                                              row['centroid_lat'], 
                                                              row['centroid_lon'],), 
                                                              axis=1)

# Keep only three closest ccc for each census tract
buffer_ccc = buffer_ccc.sort_values(by = 'hdistance')
ct_three_ccc = buffer_ccc.groupby('GEOID').head(3)

# Check results
ccc_count = ct_three_ccc.groupby('GEOID').size().reset_index(name = 'ccc_count')
summary_table = ccc_count['ccc_count'].value_counts().reset_index()
summary_table.columns = ['Number of Points Joined', 'Number of Polygons']
#print(summary_table)


## Google distance matrix API ##
"""
Use Google Directions API to get the distance in km and time (minutes) from
each census tract centroid to each of its assigned chilcare centers
"""
GoogleAPI_fn = "Google_distance_API_key.txt"

with open(GoogleAPI_fn, "r") as file:
    api_key = file.readline().strip()

# Create empty coluns to be filled
ct_three_ccc['distance_km'] = 0.0
ct_three_ccc['distance_min'] = 0.0

gmaps = googlemaps.Client(key = api_key)
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
        ct_three_ccc.loc[i, 'distance_min'] = duration_in_seconds / 60
    else:
        ct_three_ccc.loc[i, 'distance_km'] = 'NaN'
        ct_three_ccc.loc[i, 'distance_min'] = 'NaN'

    # Update counter
    counter += 1

    if counter == len(ct_three_ccc):
        break

# Save data as csv
ct_three_ccc.to_csv('../data/census_ccc_joined.csv', index = True)





