import pathlib
import pandas as pd


def clean_child_centers():
    """
    Load the data from data/Child_Care_Centers.csv, eliminate the colums
    that will not be used in the analysis, and return a clean pandas dataframe.

    Returns:
        A pandas dataframe
    """
    parent_path = pathlib.Path(__file__).parent
    child_centers_df = pd.read_csv(
        parent_path.joinpath("data/Child_Care_Centers.csv.csv"), dtype=str
    )
    child_centers_df = child_centers_df[
        [
            "X",
            "Y",
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

    return child_centers_df
