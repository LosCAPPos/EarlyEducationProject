# Import libraries
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from analysis.hav_distance import haversine_distance


def prepare_data():
    """
    This function loads and prepares the census tract (ct) shapefile and
    childcare center (ccc) data for the spatial join. This implies turning both
    of them in GeoPandas, creating centroids and getting the coordinates for the
    ct shapefile, and setting a common CRS for both GeoPandas dataframes.

    Returns:
        ct (GeoPandas): prepared census tract data
        ccc_il_gpd (GeoPandas): prepared childcare centers data
    """
    # Read and prepare data
    ct = gpd.read_file(
        "data/tl_2023_17_tract/tl_2023_17_tract.shp"
    )  # Census Tracts (ct)
    ccc_il = pd.read_csv("data/Child_Care_Centers_clean.csv")  # ChilCareCenters (ccc)

    # Calculate centroids and add coordinates as new columns to the original
    # census tract Geo DataFrame
    ct["centroid"] = ct.geometry.centroid
    ct["centroid_lat"] = ct["centroid"].to_crs(epsg = 4326).y
    ct["centroid_lon"] = ct["centroid"].to_crs(epsg = 4326).x

    # Set CRS to avoid spatial issues later
    ct.crs = "EPSG:4326"

    # As ccc came from a csv, it needs to be transformed into a Geo DataFrame
    ccc_il_gpd = gpd.GeoDataFrame(
        ccc_il, geometry=gpd.points_from_xy(ccc_il["longitude"], ccc_il["latitude"])
    )

    # Set CRS to avoid spatial issues
    ccc_il_gpd.crs = "EPSG:4326"

    return ct, ccc_il_gpd


## Intermediate analysis: Assign each CCC to the census tract it belongs to ##
# See results in .ipynb


def assign_ccc_to_ct():
    """
    This function performs the spatial join between ct and ccc data using
    spatial buffers for the ct centroids. A large buffer size (45km) is used to
    make sure most ct are assigned at least 3 ccc. Then, haversine distance is
    used to filter the three closest ccc for each ct. Resulting data is saved as
    .csv, so the function does not return anything.

    Inputs:
        ct_gpd (GeoPandas): census tract data
        ccc_gpd (GeoPandas): childcare centers data
    """
    # Call prepare_data to get GeoDataFrames
    ct_gpd, ccc_gpd = prepare_data()

    # Generate Geo DataFrame with centroids and selected variables (needed for 
    # further analysis)
    selected_ct_columns = [
        "STATEFP",
        "COUNTYFP",
        "TRACTCE",
        "GEOID",
        "centroid",
        "centroid_lon",
        "centroid_lat",
    ]
    ct_buffer = gpd.GeoDataFrame(
        ct_gpd[selected_ct_columns], geometry="centroid"
    ).copy()

    # Generate a 45km buffer for each centroid
    ct_buffer["buffer_45"] = ct_buffer["centroid"].buffer(0.008983 * 45)

    # Set the geometry column (to avoid bugs)
    ct_buffer = ct_buffer.set_geometry("buffer_45")

    # Perform spatial join between buffers and CCC points
    buffer_ccc = gpd.sjoin(
        ccc_gpd,
        ct_buffer[
            [
                "STATEFP",
                "COUNTYFP",
                "TRACTCE",
                "buffer_45",
                "GEOID",
                "centroid_lat",
                "centroid_lon",
            ]
        ],
        how = "left",
        op = "within",
    )

    # Calculate haversine distance for each pair of census tract centroid - CCC
    # Filter the three closest for each census tract
    buffer_ccc["hdistance"] = buffer_ccc.apply(
        lambda row: haversine_distance(
            row["latitude"],
            row["longitude"],
            row["centroid_lat"],
            row["centroid_lon"],
        ),
        axis=1,
    )

    # Keep only three closest ccc for each census tract
    buffer_ccc = buffer_ccc.sort_values(by="hdistance")
    ct_three_ccc = buffer_ccc.groupby("GEOID").head(3)

    # Save data as csv
    ct_three_ccc.to_csv("data/intermediate_data_backup.csv", index=True)
