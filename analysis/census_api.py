#!/usr/bin/env python3

import requests
import pandas as pd
import os

# get parent_folder to grab information from separate folder
#parent_folder = os.path.abspath(os.path.join(os.getcwd(), ".."))
# testing if it runs in Terminal, keep empty when done
test_folder = ""

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

# retreive raw data
census_raw_file = test_folder + "data/Census_data_raw.csv"
raw_census = pd.read_csv(census_raw_file, dtype=str)
raw_census[['Tract_name', 'County_name', 'State_name']] = raw_census["DETAILS"].str.split(';', expand=True)
raw_census.head()

# remove rows with tracts that do not have any population
raw_census = raw_census[raw_census["TOTPOP"].astype(int) > 0]

# raw data has -666666666 as the median income if there is no figure available, set this to mean of state"
mean_median_income = int(raw_census["MEDIAN_INCOME"][raw_census["MEDIAN_INCOME"].astype(int) > 0].astype(int).mean())
raw_census.loc[raw_census["MEDIAN_INCOME"].astype(int) <= 0, "MEDIAN_INCOME"] = str(mean_median_income)

# median income bins
med_income_quantiles = raw_census['MEDIAN_INCOME'].astype(int).quantile([0, 1/3, 2/3, 1])
labels = ['low', 'medium', 'high']

# drop the tracts that do not have any population
raw_census = raw_census.loc[raw_census["TOTPOP"].astype(int) > 0]

# empty datafram for new columns
CensusData = pd.DataFrame()

# fill columns
CensusData["state_name"] = raw_census["State_name"]
CensusData["state_code"] = raw_census["STATE"].astype(str)
CensusData["county_name"] = raw_census["County_name"]
CensusData["county_code"] = raw_census["COUNTY"].astype(str)
CensusData["tract_name"] = raw_census["Tract_name"]
CensusData["tract_code"] = raw_census["TRACT"].astype(str)
CensusData["tot_pop"] = raw_census["TOTPOP"].astype(int)
CensusData["pop_under5"] = raw_census["MALES_UNDER5"].astype(int) + raw_census["FEMALES_UNDER5"].astype(int)
CensusData["homeowner_rate"] = round(raw_census["HOMEOWNER_OCCUPIED_HOUSES"].astype(int)/raw_census["TOTAL_OCCUPIED_HOUSES"].astype(int), 4)
CensusData["less_than_hs_rate"] = round(raw_census["LESS_THAN_HS"].astype(int)/raw_census["POP_OVER25"].astype(int), 4)
CensusData["higher_education_rate"] = round(raw_census["BACHELOR_OR_GREATER"].astype(int)/raw_census["POP_OVER25"].astype(int), 4)
CensusData["below_poverty_rate"] = round(raw_census["BELOW_POVERTY_LINE"].astype(int)/raw_census["TOTPOP"].astype(int), 4)
CensusData["mobility_rate"] = round(raw_census["SAME_HOUSE_AS_LAST_YEAR"].astype(int)/raw_census["TOTPOP"].astype(int), 4)
CensusData["income_cat"] = pd.cut(raw_census['MEDIAN_INCOME'].astype(int), bins=med_income_quantiles, labels=labels)

# define majority as > 50% population in tract identifying as that race
def is_majority(population, total_population):
    proportion = population / total_population
    return 1 if proportion > 0.5 else 0

CensusData["majority_white"] = raw_census.apply(lambda row: is_majority(int(row["WHITE"]), int(row["TOTPOP"])), axis=1)
CensusData["majority_black"] = raw_census.apply(lambda row: is_majority(int(row["BLACK"]), int(row["TOTPOP"])), axis=1)
CensusData["majority_asian"] = raw_census.apply(lambda row: is_majority(int(row["ASIAN"]), int(row["TOTPOP"])), axis=1)
CensusData["majority_hispanic"] = raw_census.apply(lambda row: is_majority(int(row["HISPANIC"]), int(row["TOTPOP"])), axis=1)

# save to clean .csv
file_path = test_folder + "data/Census_data.csv"
CensusData.to_csv(file_path, index=False)