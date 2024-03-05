#!/usr/bin/env python3
# Data Visualization

import webbrowser
import dash
from dash import html, dcc, Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pandas as pd
import geopandas as gpd
import json
from analysis.optimization import create_several_child_centers


file_path = "data/final_data_merged.csv"
gdf_path = "data/tl_2023_17_tract/tl_2023_17_tract.shp"

df_final = pd.read_csv(file_path)
df_final["GEOID"] = df_final["GEOID"].astype(str)

# Reads the shapefile data into a GeoDataFrame based on GEOID. 
# Loads and merges with DataFrame to associate it with the geographic locations
gdf = gpd.read_file(gdf_path)
gdf["GEOID"] = gdf["GEOID"].astype(str)
gdf = gdf.merge(
    df_final[["GEOID", "pop_under5", "distance_min_imp", "distance_mean_imp"]],
    on="GEOID",
    how="left",)

# Generates hover text and combines data points for each geographic unit
gdf["hover_text"] = gdf.apply(
    lambda row: (
        f'Census Tract Code: {row["GEOID"]}<br>'
        f'County Codes of Illinois: {row.get("COUNTYFP", "N/A")}<br>'
        f'Population of Children Under 5: {row.get("pop_under5", "N/A"):.2f}<br>'
        f'Distance to Closest ECC (min): {row.get("distance_min_imp", "N/A"):.2f}<br>'
        f'Average Distance to Closest 3 ECC (min): {row.get("distance_mean_imp", "N/A"):.2f}'
    ),
    axis=1,)

geojson = json.loads(gdf.to_json())     # Converts to GEOJSON for plotting

# Maps from column values to more "human-readable" category names
race_mapping = {"majority_white": "Majority White",
    "majority_black": "Majority Black",
    "majority_asian": "Majority Asian",
    "majority_hispanic": "Majority Hispanic",}
for race_col, race_name in race_mapping.items():
    df_final.loc[df_final[race_col] == 1, "race_category"] = race_name

# Categorizes homeowner rate and education level into bins for analysis
df_final["housing_category"] = pd.cut(df_final["homeowner_rate"],
    bins=[-1, 0.5, 1],
    labels=["Lower Homeownership", "Higher Homeownership"])
df_final["education_category"] = pd.cut(
    df_final["higher_education_rate"],
    bins=[-1, 0.5, 1],
    labels=["Lower Education", "Higher Education"])


def create_us_map():
    """
    Creates a Choropleth map of the United States highlighting Early Childhood
    Care (ECC) desert percentages by state.
    
    Returns:
        fig: A Plotly Figure object representing the Choropleth map.
    """
    df = pd.DataFrame({
        "State": ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
                  "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
                  "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
                  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
                  "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"],
                  # Data of ECC retrieved from https://childcaredeserts.org 
        "Deserts": [60, 61, 48, 35, 60, 61, 51, 44, 38, 44,
                              68, 49, 58, 55, 23, 44, 50, 42, 22, 51,
                              53, 44, 26, 48, 54, 60, 28, 72, 46, 46,
                              53, 64, 44, 24, 39, 55, 60, 57, 47, 42,
                              43, 48, 48, 77, 35, 47, 63, 64, 54, 34,]})

    # Adds hover text for each state with ECC Desert Percentage
    df["hover_text"] = df.apply(
        lambda row: f'State: {row["State"]}<br>ECC Desert: {row["Deserts"]}%',
        axis=1,)

    # Creates choropleth map using Plotly with States' ECC desert percentage
    fig = go.Figure(
        data=go.Choropleth(locations=df["State"],
            z=df["Deserts"].astype(float), # Criteria for color coding
            locationmode="USA-states",
            colorscale="Blues",
            text=df['hover_text'], 
            hoverinfo="text",  # Only shows the hover text
            showscale=True,
            marker_line_color="white",  # Color for borders
            marker_line_width=0.5,))

    fig.update_layout(geo=dict(
            scope="usa",
            projection=go.layout.geo.Projection(type="albers usa"),
            showlakes=True,
            lakecolor="rgb(255, 255, 255)",),
        margin=dict(l=0, r=0, t=0, b=0),)
    return fig


def create_il_map():
    """
    Generates a Choropleth map for Illinois using GeoJSON data to visualize
    the distance to the closest Early Childcare Centers (ECC) across different
    census tracts. 
    
    Returns:
        fig_il: A Plotly graph object figure containing the configured map.
    """
    fig_il = go.Figure(
        data=go.Choropleth(geojson=geojson,
            featureidkey="properties.GEOID",
            locations=gdf["GEOID"],  # Uses the GEOID for mapping each tract
            z=gdf["distance_min_imp"],  # Minimum distance for color coding
            text=gdf["hover_text"],
            hoverinfo="text",
            colorscale="Blues",  
            colorbar_title="Distance to ECC<br>(min)", 
            marker_line_color="white",
            marker_line_width=0.1))

    # Sets the map bounds to the extent of the GeoJSON data
    fig_il.update_geos(visible=True,projection_scale=3,  
        center=dict(lat=39.8, lon=-89.6), fitbounds="locations")

    fig_il.update_layout(
        title_text="Exploring Distances to Closest Early Childcare Centers",
        geo=dict(
            # Hides irrelevant features such as coast, neighbouring States, ...
            showframe=False, showcoastlines=False, showcountries=False,
            showland=False,landcolor="rgba(255, 255, 255, 0)"),
        margin=dict(l=0, r=0, t=40, b=0))
    return fig_il


def early_education_dash():
    """
    Initializes and configures the Dash app for visualizing early childhcare 
    data, focusing on Early Childcare Center (ECC) accessibility in Illinois.
    
    Returns:
        A Dash app configured with the layout and callbacks necessary for the
        visualization and interaction with the early education data.
    """
    # External stylesheet for Dash app better aesthetics
    external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    app.layout = html.Div(
        children=[
            html.H1(
                children='''Bridging the Gap: Enhancing Early Childhood 
                Education Access in Illinois''',
                style={
                    "font-size": "2.5em",
                    "text-align": "center",
                    "margin-bottom": "20px",},
            ),
            html.Div(
                children="""
            Early childhood education (ECE) is a fundamental component of young 
            children's educational and developmental paths in the United States 
            and, of course, across the world. Nevertheless, despite its 
            acknowledged significance, there are still large differences in ECE 
            enrollment and accessibility, which have an impact on a wide range 
            of communities across the country. In this regard, Illinois stands 
            out due to having one of the highest rates of capacity utilization 
            and accessibility for early childhood centers (ECCs). Still, the low 
            enrollment rate of 45 percent for children between the ages of one 
            and five in early childhood education (ECE) programmes indicates 
            that the state has issues, highlighting a significant disparity, 
            even in environments with relatively advanced infrastructures. 
            To try to address this issue, the "Bridging the Gap: Enhancing Early
            Childhood Education Access in Illinois" project will carry out a 
            thorough research of the ways in which the proximity of ECE centers 
            affects the attendance rates. This study offers a paradigm for 
            comprehending and resolving such inequities across the country in 
            addition to mapping the accessibility of ECE facilities in Illinois 
            as of right now. Our goal is to provide stakeholders with the 
            resources they need to plan strategic increases in ECE access so 
            that every kid, regardless of zip code, race, or of other 
            demographic characteristics, may take advantage of these vital 
            learning opportunities.
        """,
                style={"font-size": "1.2em", "margin-bottom": "20px"},
            ),
            html.H2(
                children="Early Childcare Center Deserts in The United States",
                style={"text-align": "center", "margin-bottom": "10px"},
            ),
            dcc.Graph(
                id="us-map", config={"displayModeBar": False}, 
                figure=create_us_map()
            ),
            html.Div(
                children="""
            Childcare deserts are regions where the demand for licenced 
            childcare spaces cannot be met by the available capacity. The idea 
            that certain places are known as “deserts” is a serious problem that
            affects families all around the country. The troubling aspect is 
            that these areas are not just desolate patches of sand; rather, they 
            are regions characterised by extreme lack of easily accessible ECC 
            alternatives, impacting rural, low- to middle-class, and Hispanic 
            populations. 
        """,
                style={"margin-top": "20px", "font-size": "1.2em"},
            ),
            html.H2(
                children="Census Tract Map of the State of Illinois",
                style={
                    "text-align": "center",
                    "margin-top": "40px",
                    "margin-bottom": "10px",},
            ),
            dcc.Graph(
                id="il-map", config={"displayModeBar": False}, 
                figure=create_il_map()
            ),
            html.Div(
                children="""
            Census tracts are statistical subdivisions of a county, small and 
            generally permanent, with the purpose of representing neighborhoods. 
            They are essential to resource allocation and urban planning as they 
            offer a standardized geographic unit for statistical data display. 
            This map of Illinois provides a detailed visual representation of 
            childcare facility distribution across the State's census tracts. 
            It serves for better understanding and identifying the different 
            census tracts considered in this study where, for example, childcare 
            services are most needed and assessing the State's capacity to meet 
            the demand at the County level. The map color codes each tract based 
            on the minimum distance to an ECC, providing insights into 
            accessibility and potential childcare deserts within this State. 
        """,
                style={"margin-top": "20px", "font-size": "1.2em"},
            ),
            html.H2(
                "Demographic Dynamics", style={"text-align": "center", 
                                               "margin-top": "40px"}),
            dcc.Dropdown(
                id="socioeconomic-factor-dropdown_1",
                options=["Race", "Housing", "Education", "Income"],
                value="Race Analysis",
            ),
            dcc.Graph(id="race-bar-graph"),
            html.P(
                children="""
            In order to understand child care demands and barriers, it is 
            important to examine different demographics especially in the 
            context of ECE accessibility. The graph clarifies the makeup of the 
            regions that child care facilities serve, highlighting inequalities 
            in access. When taken as a whole, the socio-economic variables of 
            race, education, housing, and poverty rates constitute more than 
            just data; they are the lived reality of families in Illinois 
            and their children, determining whether or not they have easy access 
            to early childhood education resources.
            """,
                style={"margin-top": "20px", "font-size": "1.2em"},
            ),
            html.H2(
                "Early Education Accessibility",
                style={"text-align": "center", "margin-top": "40px"},
            ),
            dcc.Dropdown(
                id="socioeconomic-factor-dropdown",
                options=[
                    {"label": "Race", "value": "race_category"},
                    {"label": "Housing", "value": "housing_category"},
                    {"label": "Education", "value": "education_category"},],
                value="race_category",
            ),
            html.Br(),
            dcc.Dropdown(
                id="socioeconomic-factor-y-dropdown",
                options=[
                    {"label": "Average Distance in Time to Closest 3 ECCs", 
                     "value": "distance_mean_imp"},
                    {"label": "Average Haversine Distance to Closest 3 ECCs", 
                     "value": "hdistance_mean"},
                    {"label": "Minimum Distance in Time to Closest ECC", 
                     "value": "distance_min_imp"},
                    {"label": "Minimum Haversine Distance to Closest ECC", 
                     "value": "hdistance_min"},
                ],
                value="distance_mean_imp",
            ),
            dcc.Graph(id="correlation-graph"),
            html.P(
                children="""
            The graphs present a visual narrative on the disparities in early 
            childhood education accessibility among different socioeconomic 
            groups in Illinois. It is evident that communities with lower 
            educational attainment and homeownership rates face greater 
            challenges in accessing nearby childcare facilities, with 
            significantly higher average travel times to the closest ECCs. 
            Racial demographics also reveal disparities;  particularly those 
            that are majority Black or Hispanic, experience greater distances to 
            these essential services compared to majority White or Asian areas. 
            These insights are relevant and congruent with our understanding 
            that indeed ECE accessibility in Illinois is influenced by a complex 
            interplay of a variety of socioeconomic factors.
            """,
                style={"margin-top": "20px", "font-size": "1.2em"},
            ),
            html.H2("Model Simulation", style={"text-align": "center", 
                                               "margin-top": "40px"}),
            html.P(children="""
            The proposed simulation model will enable us to forecast the effects 
            of introducing more ECCs, particularly in underserved areas. By 
            integrating this model, we can dynamically update our database, 
            refining the accuracy of our accessibility metrics across different 
            census tracts. Ultimately, the goal of our research is to shed light 
            on the ways in which more inclusive child care infrastructures may 
            be positioned, creating settings in which every family has a better
            chance to prosper. It is now up to you to experiment and learn more 
            about this through our platform!  
            """),
            html.Br(),
            html.Label("Number of Child Centers"),
            dcc.Input(id="centers_input", type="number", value=1),
            html.Br(),
            html.Label("Do you want to optimize?"),
            dcc.Dropdown(
                id="optimized_dropdown",
                options=[
                    {"label": "Yes", "value": "Yes"},
                    {"label": "No", "value": "No"}
                ],
                value="True",
            ),
            html.Button('Run Simulation', id='run-simulation-button'),
            html.Div(id="model_output"),])


    # Callback for updating the Demographic Dynamics graph
    @app.callback(
        Output("race-bar-graph", "figure"),
        [Input("socioeconomic-factor-dropdown_1", "value")],
    )
    def update_race_bar_graph(value):
        """
        Updates and returns the race bar graph figure based on the selected 
        analysis category. 
        """
        default_analysis = ["majority_white", "majority_black",
                "majority_hispanic", "majority_asian",]
        default_labels = ["Majority White", "Majority Black",
                "Majority Hispanic", "Majority Asian",]
        
        # Determines analysis category and data based on user selection
        if value == "Race Analysis":
            current_analysis = default_analysis
            current_analysis_labels = default_labels
        elif value == "Housing":
            current_analysis = ["homeowner_rate", "mobility_rate"]
            current_analysis_labels = ["Homeowner Rate", "Mobility Rate"]
        elif value == "Education":
            current_analysis = ["less_than_hs_rate", "higher_education_rate"]
            current_analysis_labels = ["Less Than High School Rate",
                "Higher Education Rate"]
        elif value == "Income":
            current_analysis = ["below_poverty_rate"]
            current_analysis_labels = ["Below Poverty Rate"]
        else:
            value = "Race Analysis"
            current_analysis = default_analysis
            current_analysis_labels = default_labels

        if value != "Race Analysis":
            race_percentages = df_final.groupby("race_category")[current_analysis].mean().reset_index()
            long_race = pd.melt(race_percentages, id_vars=['race_category'], value_vars=current_analysis)
            custom_labels = [f"Mean {current_analysis_labels[current_analysis.index(row['variable'])]} for {row['race_category']} Tracts" \
                             for _, row in long_race.iterrows()]
            y_val = 100*long_race["value"]
            text_val = [f"{val:.2f}%" for val in 100*long_race["value"].astype(float)]
        else:
            majority_counts = df_final[current_analysis].sum()
            total_tracts = len(df_final)
            race_percentages = (majority_counts / total_tracts) * 100
            custom_labels = current_analysis_labels
            y_val = race_percentages
            text_val = [f"{val:.2f}%" for val in race_percentages.values]
            
        # Define a color palette with 8 colors
        palette = plt.cm.get_cmap('Blues', 8)
        # Convert RGB colors to hexadecimal format
        hex_colors = [mcolors.to_hex(color) for color in palette(range(8))]
        
        race_bar_graph_figure = go.Figure(
            [
                go.Bar(
                    x = custom_labels,
                    y=y_val,
                    text = text_val,
                    textposition="auto",
                    marker_color=hex_colors,
                )
            ]
        )

        race_bar_graph_figure.update_layout(
            title_text="Demographic Analysis Across Census Tracts",
            xaxis_title="Demographic Factor",
            yaxis_title="Percentage",
            yaxis=dict(ticksuffix="%"),
        )

        return race_bar_graph_figure


    # Callback for updating the Early Education Accessibility graph
    @app.callback(
        Output("correlation-graph", "figure"),
        [
            Input("socioeconomic-factor-dropdown", "value"),
            Input("socioeconomic-factor-y-dropdown", "value"),
        ],
    )
    def update_graph(selected_factor, y_col):
        """
        Updates and returns the correlation graph figure based on selected 
        socioeconomic factors and the chosen measurement for distance to ECCs.
        """
        fig = px.box(
            df_final,
            x=selected_factor,
            y=y_col,
            labels={"distance_mean_imp": "Distance to Closest ECCs"},
            notched=True,   # Visual indication of median's confidence interval
        )

        fig.update_traces(marker_color="#1f77b4")
        fig.update_layout(
            title="""Average Distance to Nearest Childcare Centers Among Different Socioeconomic Groups""",
            yaxis_title="Distance to Closest ECCs",
            xaxis_title=selected_factor.replace("_", " ").title(),
            boxmode="group",
        )

        return fig


    # Callback for updating Model Simulation
    @app.callback(
        Output("model_output", "children"),
        [Input("run-simulation-button", "n_clicks")],
        [State("centers_input", "value"), State("optimized_dropdown", "value")],
    )

    def update_model_output(n_clicks, centers_input, optimized_dropdown):
        '''
        Updates the model output text based on simulation button clicks,
        number of child centers, and optimization choice. Invokes the simulation 
        to determine optimal locations for establishing early childcare centers 
        based on user inputs and utilizing the `create_several_child_centers` 
        function from the `analysis.optimization` module.
        
        Inputs:
            n_clicks (int): Number of times simulation button has been clicked.
            centers_input (int): Number of ECC to consider in simulation.
            optimized_dropdown (str): User's choice on whether to optimize.
            
        Returns:
            dash.html.Div: A Dash HTML Div element containing the simulation 
                textual output. 
        '''
        if n_clicks is None or centers_input is None:
            return ""
        
        # Convert dropdown selection to boolean for optimization parameter
        optimized = True if optimized_dropdown == 'Yes' else False

        # In order for simulation to work, change with own API_KEY
        (
            ranking_lst,
            single_impact_km,
            single_impact_min,
            total_benefited_ct,
            total_impact_km,
            total_impact_min,
        ) = create_several_child_centers("API_KEY", centers_input, optimized)
        output = html.Div(
            [
                html.Div(
                    [html.H5("Ranking List of Census Tracts: "), ", \
                     ".join(str(v) for v in ranking_lst)]
                ),
                html.Div(
                    [
                        html.H5("Singular Impact in KM for Each New ECC: "),
                        ", ".join(str(v) for v in single_impact_km),
                    ]
                ),
                html.Div(
                    [
                        html.H5("Singular Impact in Min for Each New ECC: "),
                        ", ".join(str(v) for v in single_impact_min),
                    ]
                ),
                html.Div(
                    [
                        html.H5("List of All Benefited Census Tracts: "),
                        ", ".join(str(v) for v in total_benefited_ct),
                    ]
                ),
                html.Div([html.H5("Total Impact in KM: "), str(total_impact_km)
                          ]),
                html.Div(
                    [html.H5("Total Impact in Minutes: "), str(total_impact_min)
                     ]
                ),
            ]
        )
        return output
    return app


if __name__ == "__main__":
    app = early_education_dash()
    url = "http://127.0.0.1:8000"
    webbrowser.open_new(url)
    app.run_server(debug=True, port=8000, use_reloader=False)


# REFERENCES: 
    # https://plotly.com/python/bar-charts/
    # https://plotly.com/python/county-choropleth/
    # https://jen-hsuan-hsieh.gitbook.io/python/chapter-2courses/21python-for-data-science-and-machine-learning-bootcamp/dsad/2191chropleth-maps-usa