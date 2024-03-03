# Data Visualization

import webbrowser
import dash
from dash import html, dcc, Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import geopandas as gpd
import json
from analysis.optimization import create_several_child_centers


file_path = "data/final_data_merged.csv"
gdf_path = "data/tl_2023_17_tract/tl_2023_17_tract.shp"

df_final = pd.read_csv(file_path)
df_final["GEOID"] = df_final["GEOID"].astype(str)

gdf = gpd.read_file(gdf_path)
gdf["GEOID"] = gdf["GEOID"].astype(str)
gdf = gdf.merge(df_final[["GEOID", "pop_under5", "distance_min_imp", "distance_mean_imp"]], on="GEOID", how="left")
gdf["hover_text"] = gdf.apply(
    lambda row: (
        f'Census Tract Code: {row["GEOID"]}<br>'
        f'County Codes of Illinois: {row.get("COUNTYFP", "N/A")}<br>'
        f'Population of Children Under 5: {row.get("pop_under5", "N/A"):.2f}<br>'
        f'Distance to Closest ECC (min): {row.get("distance_min_imp", "N/A"):.2f}<br>'
        f'Average Distance to Closest 3 ECC (min): {row.get("distance_mean_imp", "N/A"):.2f}'
    ),
    axis=1,
)

geojson = json.loads(gdf.to_json())


race_mapping = {
    "majority_white": "Majority White",
    "majority_black": "Majority Black",
    "majority_asian": "Majority Asian",
    "majority_hispanic": "Majority Hispanic",
}
for race_col, race_name in race_mapping.items():
    df_final.loc[df_final[race_col] == 1, "race_category"] = race_name

df_final["housing_category"] = pd.cut(
    df_final["homeowner_rate"],
    bins=[-1, 0.5, 1],
    labels=["Lower Homeownership", "Higher Homeownership"],
)

df_final["education_category"] = pd.cut(
    df_final["higher_education_rate"],
    bins=[-1, 0.5, 1],
    labels=["Lower Education", "Higher Education"],
)


def create_us_map():
    df = pd.DataFrame({
        "State": ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
                  "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
                  "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
                  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
                  "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"],
        "Desert_Percentage": [60, 61, 48, 35, 60, 61, 51, 44, 38, 44,
                              68, 49, 58, 55, 23, 44, 50, 42, 22, 51,
                              53, 44, 26, 48, 54, 60, 28, 72, 46, 46,
                              53, 64, 44, 24, 39, 55, 60, 57, 47, 42,
                              43, 48, 48, 77, 35, 47, 63, 64, 54, 34,]
    })

    # Construct the hover text
    df['hover_text'] = df.apply(lambda row: f'State: {row["State"]}<br>ECC Desert: {row["Desert_Percentage"]}%', axis=1)

    # Create a choropleth map using Plotly with the states' ECC desert percentage
    fig = go.Figure(
        data=go.Choropleth(
            locations=df["State"],
            z=df["Desert_Percentage"].astype(float), 
            locationmode="USA-states",
            colorscale="Blues",
            text=df['hover_text'], 
            hoverinfo="text",  # Only show the hover text
            showscale=True,
            marker_line_color="white",
            marker_line_width=0.5,
        )
    )

    fig.update_layout(
        geo=dict(
            scope="usa",
            projection=go.layout.geo.Projection(type="albers usa"),
            showlakes=True,
            lakecolor="rgb(255, 255, 255)",
        ),
        margin=dict(l=0, r=0, t=0, b=0),
    )

    return fig



def create_il_map():
    fig_il = go.Figure(
        data=go.Choropleth(
            geojson=geojson,
            featureidkey="properties.GEOID",
            locations=gdf["GEOID"],  # Use the GEOID for mapping each tract
            z=gdf["distance_min_imp"],  # 'distance_min_imp' for color coding
            text=gdf["hover_text"],
            hoverinfo="text",
            colorscale="Blues",  
            colorbar_title="Distance to ECC<br>(min)", 
            marker_line_color="white",
            marker_line_width=0.1,
        )
    )

    # Sets the map bounds to the extent of the GeoJSON data
    fig_il.update_geos(
        visible=True,
        projection_scale=3,  # Adjust this value as needed
        center=dict(lat=39.8, lon=-89.6),  # Adjust the lat/lon as needed
        fitbounds="locations"
    )

    fig_il.update_layout(
        title_text="Exploring Distances to Closest Early Childcare Centers",
        geo=dict(
            showframe=False,
            showcoastlines=False,
            showcountries=False,
            showland=False,
            landcolor="rgba(255, 255, 255, 0)"
        ),
        margin=dict(l=0, r=0, t=40, b=0),
    )

    return fig_il


def early_education_dash():
    external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    app.layout = html.Div(
        children=[
            html.H1(
                children='''Bridging the Gap: Enhancing Early Childhood Education 
                Access in Illinois''',
                style={
                    "font-size": "2.5em",
                    "text-align": "center",
                    "margin-bottom": "20px",},
            ),
            html.Div(
                children="""
            Early childhood education (ECE) is a fundamental component of young 
            children's educational and developmental paths in the United States and, 
            of course, across the world. Nevertheless, despite its acknowledged 
            significance, there are still large differences in ECE enrollment and 
            accessibility, which have an impact on a wide range of communities 
            across the country. In this regard, Illinois stands out due to having 
            one of the highest rates of capacity utilization and accessibility for 
            early childhood centers (ECCs). Still, the low enrollment rate of 45 
            percent for children between the ages of one and five in early childhood 
            education (ECE) programmes indicates that the state has issues, 
            highlighting a significant disparity, even in environments with 
            relatively advanced infrastructures. In order to try to address this 
            issue, the "Bridging the Gap: Enhancing Early Childhood Education Access 
            in Illinois" project will carry out a thorough research of the ways in 
            which the proximity of ECE centers affects the attendance rates of 
            children between the ages of 0 and 5. This study offers a paradigm for 
            comprehending and possibly resolving such inequities across the country 
            in addition to mapping the accessibility of ECE facilities in Illinois 
            as of right now. Our goal is to provide stakeholders with the resources 
            they need to plan strategic increases in early childhood education (ECE) 
            access so that every kid, regardless of zip code, race, or of other 
            demographic characteristics, may take advantage of the vital learning 
            opportunities.
        """,
                style={"font-size": "1.2em", "margin-bottom": "20px"},
            ),
            html.H2(
                children="Early Childcare Center Deserts in The United States",
                style={"text-align": "center", "margin-bottom": "10px"},
            ),
            dcc.Graph(
                id="us-map", config={"displayModeBar": False}, figure=create_us_map()
            ),
            html.Div(
                children="""
            Childcare deserts are regions where the demand for licenced childcare 
            spaces cannot be met by the available capacity. The idea that certain 
            places are known as “deserts” is a serious problem that affects families 
            all around the country. The troubling aspect is that these areas are not 
            just desolate patches of sand; rather, they are regions characterised by 
            an extreme lack of easily accessible child care alternatives, 
            disproportionately impacting rural, low- to middle-class, and Hispanic 
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
                id="il-map", config={"displayModeBar": False}, figure=create_il_map()
            ),
            html.Div(
                children="""
            Census tracts are statistical subdivisions of a county that are small 
            and generally permanent, with the purpose of representing neighborhoods. 
            They are essential to resource allocation and urban planning as they 
            offer a standardized geographic unit for statistical data display. 
            This map of Illinois provides a detailed visual representation of 
            childcare facility distribution across the Illinois census tracts. 
            It serves for better understanding and identifying the different census 
            tracts considered in this study where, for example, childcare services 
            are most needed and assessing the state's capacity to meet the demand at 
            the county level. 
        """,
                style={"margin-top": "20px", "font-size": "1.2em"},
            ),
            html.H2(
                "Demographic Dynamics", style={"text-align": "center", "margin-top": 
                                               "40px"}),
            dcc.Dropdown(
                id="socioeconomic-factor-dropdown_1",
                options=["Race", "Housing", "Education", "Income"],
                value="Race Analysis",
            ),
            dcc.Graph(id="race-bar-graph"),
            html.P(
                children="""
            In order to understand child care demands and barriers, it is important 
            to examine different when we examine Illinois's demographics and 
            especially in the context of ECE accessibility. The graph clarifies the 
            makeup of the regions that child care facilities serve, highlighting 
            inequalities in access. When taken as a whole, the socio-economic 
            variables of race, education, housing, and poverty rates constitute 
            more than just data; they are the lived reality of families in Illinois 
            and their children, determining whether or not they have easy access to 
            early childhood education resources.
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
                    {"label": "Education", "value": "education_category"},],  # ADD INCOME
                value="race_category",
            ),
            html.Br(),
            dcc.Dropdown(
                id="socioeconomic-factor-y-dropdown",
                options=[
                    {"label": "Distance in Time", "value": "distance_mean_imp"},
                    {"label": "Haversine Distance", "value": "hdistance_mean"},
                ],
                value="distance_mean_imp",
            ),
            dcc.Graph(id="correlation-graph"),
            html.P(
                children="""
            The graphs present a visual narrative on the disparities in early 
               childhood education (ECE) accessibility among different socioeconomic 
               groups in Illinois. It is evident that communities with lower 
               educational attainment and homeownership rates face greater 
               challenges in accessing nearby childcare facilities, with 
               significantly higher average travel times to the closest ECE centers. 
               Racial demographics also reveal disparities; minority-majority areas, 
               particularly those that are majority Black or Hispanic, experience 
               greater distances to these essential services compared to majority 
               White or Asian areas. These insights are relevant and congruent with 
               our understanding that indeed ECE accessibility in Illinois is 
               influenced by a complex interplay of socioeconomic factors.
            """,
                style={"margin-top": "20px", "font-size": "1.2em"},
            ),
            html.H2("Model Simulation", style={"text-align": "center", "margin-top": "40px"}),
            html.P(children="""
            The proposed simulation model will enable us to forecast the effects of 
            introducing more ECCs, particularly in underserved areas. By 
            integrating this model, we can dynamically update our database, 
            refining the accuracy of our accessibility metrics across different 
            census tracts. Ultimately, the goal of this research is to provide light 
            on the ways in which more inclusive child care infrastructures may be 
            created, creating settings in which every family has a chance to 
            prosper and it is up to you to experiment and learn more about this 
            through our platform!  
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


    @app.callback(
        Output("correlation-graph", "figure"),
        [
            Input("socioeconomic-factor-dropdown", "value"),
            Input("socioeconomic-factor-y-dropdown", "value"),
        ],
    )
    def update_graph(selected_factor, y_col):
        fig = px.box(
            df_final,
            x=selected_factor,
            y=y_col,
            labels={"distance_mean_imp": "Average Distance to Closest 3 ECC (minutes)"},
            notched=True,
        )

        fig.update_traces(marker_color="#1f77b4")
        fig.update_layout(
            title='''Average Distance to Nearest Childcare Centers Among Different Socioeconomic Groups''',
            yaxis_title="Distance to Closest ECC (in minutes)",
            xaxis_title=selected_factor.replace("_", " ").title(),
            boxmode="group",
        )

        return fig


    @app.callback(
        Output("race-bar-graph", "figure"),
        [Input("socioeconomic-factor-dropdown_1", "value")],
    )
    def update_race_bar_graph(value):
        if value == "Race Analysis":
            current_analysis = [
                "majority_white",
                "majority_black",
                "majority_hispanic",
                "majority_asian",
            ]
            current_analysis_labels = [
                "Majority White",
                "Majority Black",
                "Majority Hispanic",
                "Majority Asian",
            ]
        elif value == "Housing":
            current_analysis = ["homeowner_rate", "mobility_rate"]
            current_analysis_labels = ["Homeowner Rate", "Mobility Rate"]
        elif value == "Education":
            current_analysis = ["less_than_hs_rate", "higher_education_rate"]
            current_analysis_labels = [
                "Less Than High School Rate",
                "Higher Education Rate",
            ]
        elif value == "Income":
            current_analysis = ["below_poverty_rate"]
            current_analysis_labels = ["Below Poverty Rate"]

        majority_counts = df_final[current_analysis].sum()
        total_tracts = len(df_final)
        race_percentages = (majority_counts / total_tracts) * 100

        custom_labels = current_analysis_labels
        race_bar_graph_figure = go.Figure(
            [
                go.Bar(
                    x=custom_labels,
                    y=race_percentages.values,
                    text=[f"{val:.2f}%" for val in race_percentages.values],
                    textposition="auto",
                    marker_color=["#1f77b4", "#aec7e8", "#3498db", "#5dade2"],
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


    @app.callback(
        Output("model_output", "children"),
        [Input("run-simulation-button", "n_clicks")],  # Listen for button click
        [State("centers_input", "value"), State("optimized_dropdown", "value")],  # Other inputs as states
    )

    def update_model_output(n_clicks, centers_input, optimized_dropdown):
        if n_clicks is None or centers_input is None:
            # No clicks means no simulation run
            return ""
        optimized = True if optimized_dropdown == 'Yes' else False

        ranking_lst, single_impact_km, single_impact_min, total_benefited_ct, total_impact_km, total_impact_min, = create_several_child_centers(
            "API_KEY", centers_input, optimized)
        output = html.Div(
            [
                html.Div([html.H5("Ranking List: "), ", ".join(str(v) for v in ranking_lst)]),
                html.Div(
                    [
                        html.H5("Singular Impact List in KM List: "),
                        ", ".join(str(v) for v in single_impact_km),
                    ]
                ),
                html.Div(
                    [html.H5("Singular Impact List in Min: "), ", ".join(str(v) for v in single_impact_min)]
                ),
                html.Div(
                    [
                        html.H5("List of All Benefited Census Tracks: "),
                        ", ".join(str(v) for v in total_benefited_ct),
                    ]
                ),
                html.Div(
                    [html.H5("Total Impact in Km: "), str(total_impact_km)]
                ),
                html.Div(
                    [html.H5("Total impact in Minutes List: "), str(total_impact_min)]
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



# REFERENCES: # https://plotly.com/python/bar-charts/
# https://plotly.com/python/county-choropleth/
