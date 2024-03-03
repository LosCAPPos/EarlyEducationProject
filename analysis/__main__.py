from analysis import census_api, census_clean, child_centers_clean
from analysis import distance_matrix_api
from analysis import distance_cleaning, spatial_join
from analysis import app
import click
import warnings

warnings.filterwarnings("ignore")


@click.command()
@click.option("--googleapi", default=False, help="Run Google Distance API", type=bool)
@click.option("--gather_data", default=True, help="Run data clean and gather", type=bool)


def main(gather_data, googleapi):
    """
    Runs the retrieval and cleaning of the data in this order:
    1. Census Data (retreive and clean)
    2. Childcare Center (just clean)
    3. Distance w/ Google API and tract shapefiles (usually skip this step)

    Then the optimization function and lastly the visualization (app.py)

    Input:
        GoogleAPI (bool): Option to run the distance calculator (time and money costly)
    
    Returns:
        Graphs
    """
    if gather_data:
        census_api
        census_clean
    
        child_centers_clean
    
        if googleapi:
            distance_matrix_api
        distance_cleaning
    
        spatial_join
    
    app

if __name__ == "__main__":
    main()