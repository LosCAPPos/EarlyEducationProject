import pandas as pd


def clean_child_centers(test=""):
    """
    Load the data from "data/Child_Care_Centers.csv", eliminate the columns
    that will not be used in the analysis, and save a clean pandas dataframe in
    "data/Child_Care_Centers_clean.csv".

    Return: None
    """
    # import child center dataframe
    child_centers_df = pd.read_csv("data/Child_Care_Centers.csv")

    # keep only the data for Illinois
    child_centers_df = child_centers_df[child_centers_df["STATE"] == "IL"]

    # keep only the useful columns for the project
    child_centers_df = child_centers_df[
        [
            "OBJECTID",
            "NAME",
            "ADDRESS",
            "CITY",
            "STATE",
            "ZIP",
            "POPULATION",
            "COUNTY",
            "COUNTYFIPS",
            "LATITUDE",
            "LONGITUDE",
            "NAICS_DESC",
        ]
    ]

    # lowercase headers and dataframe
    child_centers_df.columns = [x.lower() for x in child_centers_df.columns]

    # save the clean dataframe
    child_centers_df.to_csv(test + "data/Child_Care_Centers_clean2.csv", index=False)
