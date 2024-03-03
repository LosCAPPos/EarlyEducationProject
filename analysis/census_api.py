#!/usr/bin/env python3

import requests
import pandas as pd

# testing if it runs in Terminal, keep empty when done
test_folder = "test/"

# retrieve Census API Key
CensusAPI_fn = "CensusAPI_key.txt"

with open(CensusAPI_fn, "r") as file:
    api_key = file.readline().strip()
    
# save variables and hostname
host = "https://api.census.gov/data"
dataset = "acs/acs5"

year = "2022"

geography = 'TRACT:*'
state = '17'  # Illinois state code

"""
Variables

Children under 5
B01001_003E - Males under 5

B01001_027E - Female under 5 years

Demographics
B02001_001E - Total Population

B02001_002E - White Alone

B02001_003E - Black Alone

B02001_005E - Asian Alone

B03001_003E - Hispanic Alone

Income/Poverty Status
B17001_002E - Poverty status

B19013_001E - Median Income

Home Ownership rates
B25002_002E - Total occupied houses

B25003_002E - Home owner occupied houses

Mobility
B07003_004E - Lived in same house 1 Year ago
Educational Attainment
B15003_001E: Total population age 25 and over

B16010_002E: Population 25 Years and over with less than HS

B16010_041E: Population 25 Years and over with at least Bachelor
"""
variables = "NAME,B01001_003E,B01001_027E,B02001_001E,B02001_002E,B02001_003E,B02001_005E,B03001_003E,B17001_002E,B19013_001E,B25002_002E,B25003_002E,B07003_004E,B15003_001E,B16010_002E,B16010_041E"

# Construct the API URL
url = f'{host}/{year}/{dataset}?get={variables}&for={geography}&in=state:{state}&key={api_key}'

response = requests.get(url)
data = response.json()

col_names = ["DETAILS",
             "MALES_UNDER5",
             "FEMALES_UNDER5",
             "TOTPOP",
             "WHITE",
             "BLACK",
             "ASIAN",
             "HISPANIC",
             "BELOW_POVERTY_LINE",
             "MEDIAN_INCOME",
             "TOTAL_OCCUPIED_HOUSES",
             "HOMEOWNER_OCCUPIED_HOUSES",
             "SAME_HOUSE_AS_LAST_YEAR",
             "POP_OVER25",
             "LESS_THAN_HS",
             "BACHELOR_OR_GREATER",
             "STATE",
             "COUNTY",
             "TRACT"]

# save to raw .csv
df = pd.DataFrame(data[1:], columns=col_names)
file_path = test_folder + "data/Census_data_raw.csv"
df.to_csv(file_path, index=False)
