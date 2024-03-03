import pandas as pd

# Open data as pandas (just in case)
ct_three_ccc = pd.read_csv('data/census_ccc_joined_backup.csv')


# Correct weird cases from distance_minutes
# Generate distance ratio
ct_three_ccc['distance_km'] = pd.to_numeric(ct_three_ccc['distance_km'], errors = 'coerce')
ct_three_ccc['distance_ratio'] = ct_three_ccc['distance_km'] / ct_three_ccc['hdistance']

# Check results with histogram and quantile --> Graph in ipynb
#plt.hist(ct_three_ccc['distance_ratio'], range = (0, 20), bins = 'auto', edgecolor = 'white')
#plt.show()

# We will use the 90 percentile, only for those cases where hdistance > 0.5 km 
filter_hdistance500 = ct_three_ccc[ct_three_ccc['hdistance'] > 0.5]
quantile90 = filter_hdistance500['distance_ratio'].quantile(0.90)

# Imputate values to distance_minutes (identify them with an indicator variable)
ct_three_ccc = ct_three_ccc.reset_index(drop = True)
# First imputation
conditions1 = (ct_three_ccc['distance_ratio'] > quantile90) & (ct_three_ccc['hdistance'] > 0.5)
ct_three_ccc['imputation'] = 0
ct_three_ccc.loc[conditions1, 'imputation'] = 1
ct_three_ccc['distance_minutes_imp'] = ct_three_ccc['distance_minutes'].copy()
ct_three_ccc.loc[conditions1, 'distance_minutes_imp'] = (
    ct_three_ccc['hdistance'] / ct_three_ccc['distance_km']) * ct_three_ccc['distance_minutes']
# Second imputation
conditions2 = (ct_three_ccc['distance_ratio'] > quantile90) & (ct_three_ccc['distance_km'] > 0.5)
ct_three_ccc.loc[conditions2, 'imputation'] = 1
ct_three_ccc.loc[conditions2, 'distance_minutes_imp'] = (
    ct_three_ccc['hdistance'] / ct_three_ccc['distance_km']) * ct_three_ccc['distance_minutes']

# Save data as csv
ct_three_ccc.to_csv('data/census_ccc_joined.csv', index = True)


################################################################################
## Aggregate data at the census tract level for visualizations
# Prepare data for aggregation
ct_three_ccc['distance_minutes_imp'] = pd.to_numeric(ct_three_ccc['distance_minutes_imp'], errors = 'coerce')
ct_three_ccc = ct_three_ccc.sort_values(by = ['GEOID', 'hdistance'])
ct_three_ccc = ct_three_ccc.rename(columns = {'distance_minutes': 'distance_min',
                                              'hdistance' : 'hdistance_min',
                                              'distance_minutes_imp' : 'distance_min_imp'})

ct_three_ccc['distance_mean_imp'] = ct_three_ccc['distance_min_imp'].copy()
ct_three_ccc['hdistance_mean'] = ct_three_ccc['hdistance_min'].copy()

# Census tract repeated variables for each CCC
agg_stats = {'distance_min_imp': 'min',
             'distance_mean_imp': 'mean',
             'hdistance_min': 'min',
             'hdistance_mean': 'mean',
             'centroid_lat' : 'first',
             'centroid_lon' : 'first',
             'STATEFP' : 'first',
             'COUNTYFP' : 'first',
             'TRACTCE' : 'first',
             'population' : 'sum'}
pre_merge = ct_three_ccc.groupby('GEOID').agg(agg_stats).reset_index()

# Save data as csv
pre_merge.to_csv('data/data_pre_merge.csv', index = True)

################################################################################
## Merge data with socioeconomic census data
census_clean_data = pd.read_csv('data/Census_data.csv')

pre_merge['COUNTYFP'] = pd.to_numeric(pre_merge['COUNTYFP'])
pre_merge['TRACTCE'] = pd.to_numeric(pre_merge['TRACTCE'])
final_data_merged = pd.merge(pre_merge,
                             census_clean_data,
                             left_on = ['COUNTYFP', 'TRACTCE'],
                             right_on = ['county_code', 'tract_code'],
                             how = 'inner')

final_data_merged.to_csv('data/final_data_merged.csv', index = True)