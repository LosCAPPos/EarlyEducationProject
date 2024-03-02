# Data Visualization
import dash
from dash import html, dcc, dash_table, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import geopandas as gpd
import json

# print: do you want to do an optimization?
# put an input: Yes No
# how many child centers de you want to put?
#input
#do you want to do in the less access or with optimization 
#input

#if 
#do the optimiztion function 
#open database optimized
#else
#open regular database


file_path = '../data/final_data_merged.csv'
gdf_path = '../data/tl_2023_17_tract/tl_2023_17_tract.shp'

df_final = pd.read_csv(file_path)
df_final['TRACTCE'] = df_final['TRACTCE'].astype(str)
df_final['ECC_Capacity'] = df_final['pop_under5'] / df_final['tot_pop']

gdf = gpd.read_file(gdf_path)
gdf['TRACTCE'] = gdf['TRACTCE'].astype(str)
gdf = gdf.merge(df_final[['TRACTCE', 'ECC_Capacity']], on='TRACTCE', how='left')
gdf['hover_text'] = gdf.apply(
    lambda row: f'Tract: {row["TRACTCE"]}<br>County: {row.get("COUNTYFP", "N/A")}<br>ECC Capacity: {row.get("ECC_Capacity", "N/A"):.2f}', axis=1)
geojson = json.loads(gdf.to_json())                                    


# STATIC Race Analysis GRAPH
majority_counts = df_final[['majority_white', 'majority_black', 'majority_hispanic', 'majority_asian']].sum()
total_tracts = len(df_final)
race_percentages = (majority_counts / total_tracts) * 100
race_bar_graph_figure = go.Figure([go.Bar(
        x=race_percentages.index, y=race_percentages.values,
        text=[f"{val:.2f}%" for val in race_percentages.values],
        textposition='auto',)])

custom_labels = ['Majority White', 'Majority Black', 'Majority Hispanic', 'Majority Asian']
race_bar_graph_figure = go.Figure([go.Bar(
        x=custom_labels, y=race_percentages.values,                                  
        text=[f"{val:.2f}%" for val in race_percentages.values],               
        textposition='auto',
        marker_color=['#1f77b4', '#aec7e8', '#3498db', '#5dade2'],)])

race_bar_graph_figure.update_layout(
    title_text='Demographic Analysis Across Census Tracts',
    xaxis_title="Race", yaxis_title="Percentage", yaxis=dict(ticksuffix="%"),)

# INTERACTIVE Early Education Accessibility GRAPH
race_mapping = {'majority_white': 'Majority White',
    'majority_black': 'Majority Black',
    'majority_asian': 'Majority Asian',
    'majority_hispanic': 'Majority Hispanic'}
for race_col, race_name in race_mapping.items():
    df_final.loc[df_final[race_col] == 1, 'race_category'] = race_name

df_final['housing_category'] = pd.cut(df_final['homeowner_rate'],
    bins=[-1, 0.5, 1], labels=['Lower Homeownership', 'Higher Homeownership'])

df_final['education_category'] = pd.cut(df_final['higher_education_rate'],
    bins=[-1, 0.5, 1], labels=['Lower Education', 'Higher Education'])


# ALL PLACEHOLDERS FOR NOW
least_populous_data = pd.DataFrame({
    'Census Tract': ['1001', '1002', '1003', '1004', '1005', '1006', '1007', '1008', '1009', '1010'],
    'Childcare Centers': [1, 2, 1, 0, 2, 1, 0, 1, 2, 1]})
most_populous_data = pd.DataFrame({
    'Census Tract': ['2001', '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010'],
    'Childcare Centers': [10, 9, 8, 10, 9, 8, 7, 6, 8, 7]})


app = dash.Dash(__name__)

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    html.H1(children='Impact of School Vicinity on Early Childhood Education Attendance Rates',
            style={'font-size': '2.5em', 'text-align': 'center', 'margin-bottom': '20px'}),
    html.Div(children='''
        TO DO: COMMENT on how this project analyzes the impact of school vicinity on the attendance rates of early childhood education (0-5 y/o) in Illinois.
        Our goal is to locate the zip codes/counties with the lowest rates of licensed capacity compared to their populations of children aged five-year-old and below.
    ''', style={'font-size': '1.2em', 'margin-bottom': '20px'}),
    
    html.H2(children='Childcare Center Capacity by State', style={'text-align': 'center', 'margin-bottom': '10px'}),
    dcc.Graph(id='us-map', config={'displayModeBar': False}),
    html.Div(children='''
        TO DO: COMMENT on the findings of this study indicate that capacity at childcare centers varies significantly by state, with Illinois being one of the states with the highest capacity.
        Given this context, our research focuses on understanding and improving early childhood education attendance rates in Illinois, where there is a substantial opportunity to make a positive impact.
    ''', style={'margin-top': '20px', 'font-size': '1.2em'}),
    
    html.H2(children='Illinois Census Tract Map', style={'text-align': 'center', 'margin-top': '40px', 'margin-bottom': '10px'}),
    dcc.Graph(id='il-map', config={'displayModeBar': False}),
    html.Div(children='''
        TO DO: COMMENT on Illinois facilities for child care will be added here after analyzing the county-level data.
             I WILL FIGURE THIS MAP OUT SOON...
    ''', style={'margin-top': '20px', 'font-size': '1.2em'}),
    
    # MAKE IT INTERACTIVE CENSUS MAP 
    
    html.H2('Race Analysis', style={'text-align': 'center', 'margin-top': '40px'}),
    dcc.Graph(
        id='race-bar-graph',
        figure=race_bar_graph_figure),
    
    html.H2('Early Education Accessibility', style={'text-align': 'center', 'margin-top': '40px'}),
    dcc.Dropdown(
        id='socioeconomic-factor-dropdown',
        options=[
            {'label': 'Race', 'value': 'race_category'},
            {'label': 'Housing', 'value': 'housing_category'},
            {'label': 'Education', 'value': 'education_category'}],
        value='race_category' ),
    dcc.Graph(id='correlation-graph'),

    ##### TABLES
    html.H2('Childcare Centers by Census Tract', style={'text-align': 'center', 'margin-top': '40px'}),
    html.Div([
        html.Div([
            html.H3('Top 10 Least Populous Census Tracts'),
            dash_table.DataTable(
                id='table-least',
                columns=[{"name": i, "id": i} for i in least_populous_data.columns],
                data=least_populous_data.to_dict('records'),
                style_cell={'textAlign': 'center'},
                style_header={
                    'backgroundColor': 'lightgrey',
                    'fontWeight': 'bold'},)], className='six columns'),
        html.Div([
            html.H3('Top 10 Most Populous Census Tracts'),
            dash_table.DataTable(
                id='table-most',
                columns=[{"name": i, "id": i} for i in most_populous_data.columns],
                data=most_populous_data.to_dict('records'),
                style_cell={'textAlign': 'center'},
                style_header={
                    'backgroundColor': 'lightgrey',
                    'fontWeight': 'bold'},)], className='six columns'),], 
                    className='row')])

################################################################################
# US MAP
@app.callback(dash.dependencies.Output('us-map', 'figure'), 
    [dash.dependencies.Input('us-map', 'hoverData')])

def update_map(hoverData):
    df = pd.DataFrame({
        'State': ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'],
        'Capacity_Percentage': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
                                11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                                21, 22, 23, 24, 25, 26, 27, 28, 29, 30,
                                31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
                                41, 42, 43, 44, 45, 46, 47, 48, 49, 50]})         # Placeholder values

    # Create a choropleth map using Plotly with the states' capacity percentage
    fig = go.Figure(data=go.Choropleth(
        locations=df['State'],                                                  # Sets the spatial coordinates
        z=df['Capacity_Percentage'].astype(str),                                # Sets the data to be color-coded
        locationmode='USA-states',                                              # Matches locations to the USA states
        colorscale='Blues',                                                     # Sets the color scale
        text=df['State'],                                                       # Sets the hover text
        hoverinfo='text+z',                                                     # Sets the content of the hoverinfo
        showscale=False,                                                        # Hides the color scale bar
        marker_line_color='white',                                              # Sets the color of the state boundaries
        marker_line_width=1,))                                                  # Sets the width of the state boundaries

    fig.update_layout(geo=dict(scope='usa',
            projection=go.layout.geo.Projection(type='albers usa'),             # Sets the map projection type
            showlakes=True,                                                     # Shows lakes on the map
            lakecolor='rgb(255, 255, 255)'),
        margin=dict(l=0, r=0, t=0, b=0))                                        # Adjusts margins to fit the map properly

    return fig 
################################################################################
# ILLINOIS MAP Callback
@app.callback(
    Output('il-map', 'figure'),
    [Input('il-map', 'hoverData')])

def update_il_map(hoverData):
    # Create a choropleth map using Plotly for Illinois census tracts
    fig_il = go.Figure(data=go.Choropleth(
        geojson=geojson,                                                        # Uses the GeoJSON data
        featureidkey="properties.TRACTCE",                                      # Sets the feature identifier key
        locations=gdf['TRACTCE'],  # Sets the locations in the GeoDataFrame
        z=gdf.index,  # Uses the index as a placeholder for actual data
        text=gdf['hover_text'],  # Sets the hover text to the census tract code
        hoverinfo='text',  # Sets the content of the hoverinfo
        colorscale='Blues',  # Sets the color scale
        showscale=False,   
        marker_line_color='white',  # Sets the color of the tract boundaries
        marker_line_width=0.5,))

    fig_il.update_geos(
        visible=False, 
        projection_scale=5,  # zoom factor, adjust as needed
        center=dict(lat=40.0, lon=-89.0))

    fig_il.update_layout(
        title_text='Illinois Census Tract Map',
        geo_scope='usa',
        margin=dict(l=0, r=0, t=40, b=0))

    return fig_il 
################################################################################
# Early Education Accessibility
@app.callback(
    Output('correlation-graph', 'figure'),
    [Input('socioeconomic-factor-dropdown', 'value')])
def update_graph(selected_factor):
    fig = px.box(
        df_final, 
        x=selected_factor, 
        y='distance_mean_imp', 
        labels={'distance_mean_imp': 'Distance to Closest ECC (minutes)'},
        notched=True)
    
    fig.update_traces(marker_color='#1f77b4')
    fig.update_layout(
        title='Average Distance to Nearest Childcare Center Among Different Socioeconomic Groups',
        yaxis_title='Distance to Closest ECC (in minutes)',
        xaxis_title=selected_factor.replace('_', ' ').title(),
        boxmode='group')
    
    return fig
################################################################################

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)

# REFERENCES: # https://plotly.com/python/bar-charts/ 
# https://plotly.com/python/county-choropleth/