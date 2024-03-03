from analysis import census_api, census_clean, child_centers_clean
from analysis import distance_matrix_api
from analysis import distance_cleaning, spatial_join
from analysis import app
import click
import warnings
import webbrowser

@click.command()
@click.option("--googleapi", default=False, help="Run Google Distance API", type=bool)
@click.option("--gather_data", default=True, help="Run data clean and gather", type=bool)
@click.option("--test", default=True, help="Run data clean and gather", type=bool)


def main(gather_data, googleapi, test):
    """
    Runs the retrieval and cleaning of the data in this order:
    1. Census Data (retreive and clean)
    2. Childcare Center (just clean)
    3. Distance w/ Google API and tract shapefiles (usually skip this step)

    Then the optimization function and lastly the visualization (app.py)

    Input:
        googleapi (bool): Option to run the distance calculator (time and money costly)
        gather_data (bool): Option to gather data (it's already saved in our data folder)
        test (str): Save data to test folder or regular
    
    Returns:
        Graphs
    """
    warnings.filterwarnings("ignore")
    if test:
        test = "test/"
    if gather_data:
        print("Retreiving Census Data")
        census_api.retreive_census_data(test=test)
        print("Cleaning Census Data")
        census_clean.clean_census_data(test=test)
        
        print("Cleaning Child Center Data")
        child_centers_clean.clean_child_centers(test=test)
    
        if googleapi:
            print("Calculating Tract x Child Center Distance")
            distance_matrix_api.get_distance_data(test=test)
        # cleaning takes 3 steps
        print("Cleaning Child Center Distance Data")
        distance_cleaning.clean_distance_data(test=test)
        distance_cleaning.aggregate_at_ct(test=test)
        distance_cleaning.socioeconomic_merge(test=test)
        
        print("Merging Child Center and Census Data")
        spatial_join.assign_ccc_to_ct(test=test)

    print("Visualizing Data")
    app_serv = app.early_education_dash()
    url = "http://127.0.0.1:8000"
    webbrowser.open_new(url)
    app_serv.run_server(debug=True, port=8000, use_reloader=False)

if __name__ == "__main__":
    main()