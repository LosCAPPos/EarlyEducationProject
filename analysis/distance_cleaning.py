import pandas as pd


def clean_distance_data(test=""):
    """
    This function imputates values to the distance in minutes variable. This is
    done because the Google API provides weird results in some cases. Thus, we
    correct cases where the distance in km provided by the API is much higher
    than the haversine distance. Specifically, we use the (haversine distance /
    API distance) to 'discount' the distance in minutes.
    """

    # Open data as pandas
    ct_three_ccc = pd.read_csv("data/census_ccc_joined_backup.csv")

    # Generate distance ratio
    ct_three_ccc["distance_km"] = pd.to_numeric(
        ct_three_ccc["distance_km"], errors="coerce"
    )
    ct_three_ccc["distance_ratio"] = (
        ct_three_ccc["distance_km"] / ct_three_ccc["hdistance"]
    )

    # Check results with histogram --> Graph in ipynb
    # We will use the 90 percentile, only for those cases where hdistance > 0.5 km
    filter_hdistance500 = ct_three_ccc[ct_three_ccc["hdistance"] > 0.5]
    quantile90 = filter_hdistance500["distance_ratio"].quantile(0.90)

    # Imputate values to distance_minutes to correct weird results from Google API
    # Reset index to avoid duplicated index bugs
    ct_three_ccc = ct_three_ccc.reset_index(drop=True)
    # First imputation (only for cases where hdistance is not too small)
    # Define conditions
    conditions1 = (ct_three_ccc["distance_ratio"] > quantile90) & (
        ct_three_ccc["hdistance"] > 0.5
    )
    ct_three_ccc["imputation"] = 0  # Indicator variable to identify imputations
    ct_three_ccc.loc[conditions1, "imputation"] = 1  # Identify imputation cases
    ct_three_ccc["distance_minutes_imp"] = ct_three_ccc["distance_minutes"].copy()
    # Imputate
    ct_three_ccc.loc[conditions1, "distance_minutes_imp"] = (
        ct_three_ccc["hdistance"] / ct_three_ccc["distance_km"]
    ) * ct_three_ccc["distance_minutes"]

    # Second imputation (only for cases where distance_km is not too small)
    # Define conditions
    conditions2 = (ct_three_ccc["distance_ratio"] > quantile90) & (
        ct_three_ccc["distance_km"] > 0.5
    )
    ct_three_ccc.loc[conditions2, "imputation"] = 1  # Identify imputation cases
    # Imputate
    ct_three_ccc.loc[conditions2, "distance_minutes_imp"] = (
        ct_three_ccc["hdistance"] / ct_three_ccc["distance_km"]
    ) * ct_three_ccc["distance_minutes"]

    # Save data as csv
    ct_three_ccc.to_csv(test + "data/census_ccc_joined.csv", index=True)


def aggregate_at_ct(test=""):
    """
    This function aggregates the data at the census tract level, getting the min
    and mean for the distance variables, the sum of the capacity of the childcare
    centers, and keeps other key variables that already are at the tract level.
    """

    # Open data as pandas
    ct_three_ccc = pd.read_csv("data/census_ccc_joined.csv")

    # Prepare data for aggregation
    ct_three_ccc["distance_minutes_imp"] = pd.to_numeric(
        ct_three_ccc["distance_minutes_imp"], errors="coerce"
    )
    ct_three_ccc = ct_three_ccc.sort_values(by=["GEOID", "hdistance"])
    ct_three_ccc = ct_three_ccc.rename(
        columns={
            "distance_minutes": "distance_min",
            "hdistance": "hdistance_min",
            "distance_minutes_imp": "distance_min_imp",
        }
    )

    ct_three_ccc["distance_mean_imp"] = ct_three_ccc["distance_min_imp"].copy()
    ct_three_ccc["hdistance_mean"] = ct_three_ccc["hdistance_min"].copy()

    # Define statistics to get for each variable
    agg_stats = {
        "distance_min_imp": "min",
        "distance_mean_imp": "mean",
        "hdistance_min": "min",
        "hdistance_mean": "mean",
        "centroid_lat": "first",
        "centroid_lon": "first",
        "STATEFP": "first",
        "COUNTYFP": "first",
        "TRACTCE": "first",
        "population": "sum",
    }

    # Aggregate data at census tract level
    pre_merge = ct_three_ccc.groupby("GEOID").agg(agg_stats).reset_index()

    # Save data as csv
    pre_merge.to_csv(test + "data/data_pre_merge.csv", index=True)


def socioeconomic_merge(test=""):
    """
    This function merges the joined census tract and childcare center data (from
    the aggregate_at_ct function) with socioeconomic census cleaned data. Instead
    of returning the dataframe, it saves it as a csv. This data is an input for
    visualizations and optimization.
    """
    # Load joined ct and ccc data (already aggregated at the ct level)
    pre_merge = pd.read_csv("data/data_pre_merge.csv")

    # Load cleaned socioeconomic census data
    census_clean_data = pd.read_csv("data/Census_data.csv")

    # Change variable types to use them as keys
    pre_merge["COUNTYFP"] = pd.to_numeric(pre_merge["COUNTYFP"])
    pre_merge["TRACTCE"] = pd.to_numeric(pre_merge["TRACTCE"])

    # Merge data
    final_data_merged = pd.merge(
        pre_merge,
        census_clean_data,
        left_on=["COUNTYFP", "TRACTCE"],
        right_on=["county_code", "tract_code"],
        how="inner",
    )

    # Save data as csv (will be used in visualizations and simulations)
    final_data_merged.to_csv(test + "data/final_data_merged.csv", index=True)
