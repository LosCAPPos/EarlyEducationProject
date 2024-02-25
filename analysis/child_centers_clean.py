import pathlib
import pandas as pd


def clean_child_centers():
    """
    Load the data from "data/Child_Care_Centers.csv", eliminate the columns
    that will not be used in the analysis, and save a clean pandas dataframe in
    "data/Child_Care_Centers_clean.csv".

    Return: None
    """
    # import child center dataframe
    parent_path = pathlib.Path(__file__).parent
    child_centers_df = pd.read_csv(parent_path.joinpath("data/Child_Care_Centers.csv"))

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
    child_centers_df = child_centers_df.apply(
        lambda x: x.str.lower() if x.dtype == "object" else x
    )

    # save the clean dataframe
    child_centers_df.to_csv("data/Child_Care_Centers_clean.csv", index=False)
