#!/usr/bin/env python3

import requests
import pandas as pd

def clean_census_data(test=""):
    """
    Clean data from Census API
    
    Returns:
        Save data to data/Census_data.csv
    """
    # retreive raw data
    census_raw_file = test + "data/Census_data_raw.csv"
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

    CensusData["majority_white"] = raw_census.apply(lambda row: is_majority(int(row["WHITE"]), int(row["TOTPOP"])), axis=1)
    CensusData["majority_black"] = raw_census.apply(lambda row: is_majority(int(row["BLACK"]), int(row["TOTPOP"])), axis=1)
    CensusData["majority_asian"] = raw_census.apply(lambda row: is_majority(int(row["ASIAN"]), int(row["TOTPOP"])), axis=1)
    CensusData["majority_hispanic"] = raw_census.apply(lambda row: is_majority(int(row["HISPANIC"]), int(row["TOTPOP"])), axis=1)
    
    # Remove census tracts with fewer than 10 children (unneccessary for our analysis)
    CensusData = CensusData[CensusData['pop_under5'] >= 10]


    # save to clean .csv
    file_path = test + "data/Census_data.csv"
    CensusData.to_csv(file_path, index=False)

def is_majority(population, total_population):
    """
    Helper Function: check if it is majority
        define majority as > 50% population in tract identifying as that race
    
    Input: 
        population (int): population of that race in the tract
        total_population (int): total population in that tract
        
    Returns:
        ind (int): 1 if it is majority, 0 if not
    """
    proportion = population / total_population
    return 1 if proportion > 0.5 else 0