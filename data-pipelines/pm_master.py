# -*- coding: utf-8 -*-
"""
Program to make a master spreadsheet of all airborne PM parameters (e.g., TSP, PM10, PM2.5 etc.,) from gravimetric filter spreadsheet

@author: alima
"""

import sys
sys.modules[__name__].__dict__.clear()
import pandas as pd
import numpy as np
from scipy import stats
import math
exec(open(r'C:\PhD Research\Generic Codes\notion_corrections.py').read())

df = pd.read_excel(backslash_correct(r'C:\PhD Research\Airborne\Des\Filter_Master_v21_200206_am.xlsx'))

########################################################
### Step 1: Initial scalars and gravimetric read-out ###
########################################################

## Initial Scalars for later calculations:
ptfe_mass_error = df[df['Visit_#'] == 'Visit 0']['PM Mass'].describe().loc['50%']

## Making a gravimetric master
df = df[df['Visit_#'] != 'Pilot']
df = df[df['Visit_#'] != 'Visit 0']
# df = df[stata_varlist_split('FilterSN FilterPosition FilterMaterial PilotFieldTravel Visit_ PredeployMass Postdeploymass PMMass AverageFlow InitialFlow FinalFlow')]

df = df[['Filter S/N', 'Filter Position', 'Filter Material', 'Pilot/Field/Travel', 'Visit_#',
         'Predeploy Mass', 'Postdeploy mass', 'PM Mass',  'Initial Flow', 'Final Flow',
         'Average Flow']]

df['Visit_#'] = df['Visit_#'].str[-1:].astype(int)
df.rename(columns = {'Visit_#' : 
                     'visit'}, inplace = True)

## Correction fo F75 filter
df_ref = df[(df['Filter Position'].str[0:3] == 'PEM')|(df['Filter Position'].str[0:3] == 'SCI')]
df_ref = df_ref[~(df_ref['Filter Position'].str[-1:] == 'A')]
df_ref['Filter Position'] = df_ref['Filter Position'].str[0:3]

df_ref = df_ref.groupby(['visit', 'Filter Position'], as_index = False)['PM Mass'].agg('sum')
df_ref.loc[(df_ref['visit'] == 6) & (df_ref['Filter Position'] == 'PEM'), 'PM Mass'] = np.nan
del df_ref['visit']

a = df_ref[df_ref['Filter Position'] == 'SCI']['PM Mass'].reset_index(drop = True)
b = df_ref[df_ref['Filter Position'] == 'PEM']['PM Mass'].reset_index(drop = True)

# df_reg = pd.concat([df_ref[df_ref['Filter Position'] == 'SCI']['PM Mass'],df_ref[df_ref['Filter Position'] == 'PEM']['PM Mass']], axis = 1)
df_reg = pd.concat([b,a], axis = 1).dropna()
df_reg.columns = ['PEM', 'SCI']

slope, intercept, r_value, p_value, std_err = stats.linregress(df_reg['SCI'], df_reg['PEM'])
new_val = slope * df_ref.iloc[5,1] + intercept

df.loc[df['Filter S/N'] == 'F75', 'PM Mass'] = new_val
df.to_excel(backslash_correct(r'C:\PhD Research\Airborne\Processed\filter_gravimetric_master.xlsx'), index = False)

###################################################
### Step 2: Calculating CV of PMs in each visit ###
###################################################

df_cv = df[(df['Filter Material'] == 'MCE') & (df['Pilot/Field/Travel'] == 'Field') & (df['Filter Position'] != 'Blank')]
df_cv['PM Mass per Flow'] = df_cv['PM Mass'] / df_cv['Average Flow']

a = df_cv.groupby('visit', as_index = False)['PM Mass per Flow'].agg('std').rename(columns = {'PM Mass per Flow' : 'PM Mass per Flow: Std'})
b = df_cv.groupby('visit', as_index = False)['PM Mass per Flow'].agg('mean').rename(columns = {'PM Mass per Flow' : 'PM Mass per Flow: Mean'}) 

df_cv = a.merge(b, on = 'visit', how = 'outer')
df_cv['PM Mass CV'] = df_cv['PM Mass per Flow: Std']/df_cv['PM Mass per Flow: Mean']
df_cv.drop(['PM Mass per Flow: Std', 'PM Mass per Flow: Mean'], axis = 1, inplace = True)
pm_mass_cv = df_cv['PM Mass CV'] # making a separate series for PM error calculations later

# df_cv = df_cv.groupby('visit', as_index = False)['PM Mass per Flow'].apply(lambda x: np.std(x) / np.mean(x)) # did not understand why it didn';t work

##################################################
### Step 3: Correction of PEM and SCI samplers ###
##################################################

## SCI vs. PEM Correction factor
df_cor_sci = df[(df['Filter Position'].str[0:3] == 'SCI') & (df['Filter Position'].str[-1:] != "A")]
df_cor_sci = df_cor_sci.groupby('visit').agg({'PM Mass' : 'sum',
                                              'Average Flow': 'mean'})
df_cor_sci = df_cor_sci.sum()
sci_25 = (df_cor_sci.iloc[0] * 1000) / (df_cor_sci.iloc[1] * ((7 * 24 * 60)/1000))

df_cor_pem = df[(df['Filter Position'].str[0:3] == 'PEM') & (df['Filter Position'].str[-1:] != "A")]
df_cor_pem = df_cor_pem[['PM Mass', 'Average Flow']].sum()
pem_25 = (df_cor_pem.iloc[0] * 1000) / (df_cor_pem.iloc[1] * ((7 * 24 * 60)/1000))

pm25_cor_factor = (pem_25 + sci_25)/(2*sci_25)


###############################################
### Step 4: Calculating error uncertainties ###
###############################################

## Reading time error by travel blanks
df_travel = df[(df['Filter Material'] == 'MCE') & ((df['Pilot/Field/Travel'] == "Travel"))]
df_travel['PM Mass'] = np.abs(df_travel['PM Mass'])
tsp_mass_error = df_travel['PM Mass'].describe().loc['50%']

## Calculating TSP Concnetrtion and errors
df_tsp = df[(df['Pilot/Field/Travel'] == 'Field') & (df['Filter Material'] == 'MCE') & (df['Filter Position'] != 'Blank')]
df_tsp['TSP Time Error'] = tsp_mass_error ** 2

df_tsp = df_tsp.groupby('visit', as_index =  False).agg({'PM Mass' : 'mean',
                                                         'Average Flow' : 'mean',
                                                         'TSP Time Error' : 'sum',})

df_tsp['TSP Time Error'] = np.sqrt(df_tsp['TSP Time Error'])/3
df_tsp = df_tsp.merge(df_cv, on = 'visit', how = 'outer')
df_tsp['CV Error'] = df_tsp['PM Mass CV'] * df_tsp['PM Mass'] 

df_tsp['TSP Mass Error'] = np.sqrt(df_tsp['CV Error'].pow(2) + df_tsp['TSP Time Error'].pow(2))
 
df_tsp['TSP Concentration'] = (df_tsp['PM Mass']/(df_tsp['Average Flow'] * (7*24*60))) * 1000000
df_tsp['TSP Concentration Error'] = df_tsp['TSP Concentration'] * np.sqrt((df_tsp['TSP Mass Error']/df_tsp['PM Mass']).pow(2) + (0.1/(np.sqrt(3)*df_tsp['Average Flow'])).pow(2) + 0.025 ** 2)
df_tsp = df_tsp[['visit', 'TSP Concentration', 'TSP Concentration Error', 'PM Mass', 'TSP Mass Error', 'Average Flow']]
df_tsp.rename(columns = {'PM Mass': 'TSP Mass',
                         'Average Flow': 'Average Flow FC'}, inplace = True)

### Calculating other pms and errors
## PM10 by SCI (and its error)

df_pm10 = df[df['Filter Position'].str[0:3] == 'SCI']
df_pm10 = df_pm10.groupby('visit', as_index = False).agg({'PM Mass': 'sum',
                                                      'Average Flow': 'mean'})

df_pm10['PM10 SCI'] = ((df_pm10['PM Mass'] / (df_pm10['Average Flow'] * (7*24*60))) * 1000000) * pm25_cor_factor
df_pm10['PM10 SCI Mass Error'] = np.sqrt((ptfe_mass_error * math.sqrt(5))**2 +  (pm_mass_cv * df_pm10['PM Mass']).pow(2))  
df_pm10['PM10 SCI Error'] = df_pm10['PM10 SCI'] * np.sqrt((df_pm10['PM10 SCI Mass Error']/df_pm10['PM Mass']).pow(2) + (0.5/(df_pm10['Average Flow'])).pow(2) + 0.025 ** 2)
df_pm10['PM10 SCI Error'] = np.sqrt(df_pm10['PM10 SCI Error'].pow(2) + (0.06 * df_pm10['PM10 SCI Error']).pow(2))
df_pm10.rename(columns = {'PM Mass': 'PM10 SCI Mass',
                          'Average Flow': 'Average Flow SCI'}, inplace = True)

## PM2.5 by SCI (and its error)
df_pm25 = df[(df['Filter Position'].str[0:3] == 'SCI') & (df['Filter Position'].str[-1:] != 'A')]
df_pm25 = df_pm25.groupby('visit', as_index = False).agg({'PM Mass': 'sum',
                                                          'Average Flow': 'mean'})

df_pm25['PM2.5 SCI'] = ((df_pm25['PM Mass'] / (df_pm25['Average Flow'] * (7*24*60))) * 1000000) * pm25_cor_factor
df_pm25['PM2.5 SCI Mass Error'] = np.sqrt((ptfe_mass_error * math.sqrt(4))**2 +  (pm_mass_cv * df_pm25['PM Mass']).pow(2))
df_pm25['PM2.5 SCI Error'] = df_pm25['PM2.5 SCI'] * np.sqrt((df_pm25['PM2.5 SCI Mass Error']/df_pm25['PM Mass']).pow(2) + (0.5/(df_pm25['Average Flow'])).pow(2) + 0.025 ** 2)
df_pm25['PM2.5 SCI Error'] = np.sqrt(df_pm25['PM2.5 SCI Error'].pow(2) + (0.06 * df_pm25['PM2.5 SCI Error']).pow(2))
df_pm25.rename(columns = {'PM Mass': 'PM2.5 SCI Mass'}, inplace = True)
df_pm25.drop(['Average Flow'], axis = 1, inplace = True)

## PM1 by SCI (and its error)
df_pm1 = df[(df['Filter Position'].str[0:3] == 'SCI') & (df['Filter Position'].str[-1:] != 'A') & (df['Filter Position'].str[-1:] != 'B')]
df_pm1 = df_pm1.groupby('visit', as_index = False).agg({'PM Mass': 'sum',
                                                          'Average Flow': 'mean'})

df_pm1['PM1 SCI'] = ((df_pm1['PM Mass'] / (df_pm1['Average Flow'] * (7*24*60))) * 1000000) * pm25_cor_factor
df_pm1['PM1 SCI Mass Error'] = np.sqrt((ptfe_mass_error * math.sqrt(3))**2 +  (pm_mass_cv * df_pm1['PM Mass']).pow(2))
df_pm1['PM1 SCI Error'] = df_pm1['PM1 SCI'] * np.sqrt((df_pm1['PM1 SCI Mass Error']/df_pm1['PM Mass']).pow(2) + (0.5/(df_pm1['Average Flow'])).pow(2) + 0.025 ** 2)
df_pm1['PM1 SCI Error'] = np.sqrt(df_pm1['PM1 SCI Error'].pow(2) + (0.06 * df_pm1['PM1 SCI Error']).pow(2))
df_pm1.rename(columns = {'PM Mass': 'PM1 SCI Mass'}, inplace = True)
df_pm1.drop(['Average Flow'], axis = 1, inplace = True)

## PM2.5 by PEM
df_pem = df[(df['Filter Position'].str[0:3] == 'PEM')]
df_pem = df_pem[['visit', 'PM Mass', 'Average Flow']].reset_index()

df_pem['PM2.5 PEM'] = (df_pem['PM Mass'] / (df_pem['Average Flow'] * (7*24*60))) * 1000000
df_pem['PM2.5 PEM Mass Error'] = np.sqrt(ptfe_mass_error**2 +  (pm_mass_cv * df_pem['PM Mass']).pow(2))
df_pem['PM2.5 PEM Error'] = df_pem['PM2.5 PEM'] * np.sqrt((df_pem['PM2.5 PEM Mass Error']/df_pem['PM Mass']).pow(2) + (0.5/(df_pem['Average Flow'])).pow(2) + 0.025 ** 2)
df_pem['PM2.5 PEM Error'] = np.sqrt(df_pem['PM2.5 PEM Error'].pow(2) + (0.06 * df_pem['PM2.5 PEM Error']).pow(2))
df_pem.rename(columns = {'PM Mass': 'PM2.5 PEM Mass'}, inplace = True)
df_pem.drop(['Average Flow'], axis = 1, inplace = True)

##########################################
### Step 5: Merging all dfs and export ###
##########################################

df_pam_all = df_tsp.merge(df_pm10, 
                          on = 'visit', 
                          how = 'outer').merge(df_pm25, 
                                               on = 'visit', 
                                               how = 'outer').merge(df_pm1,
                                                                    on = 'visit', 
                                                                    how = 'outer').merge(df_pem,
                                                                                         on = 'visit',
                                                                                         how = 'outer')                                                                                 
df_pam_all = df_pam_all[['visit', 
                           'TSP Mass', 'TSP Mass Error', 'TSP Concentration', 'TSP Concentration Error', 'Average Flow FC',
                           'PM10 SCI Mass', 'PM10 SCI Mass Error', 'PM10 SCI', 'PM10 SCI Error',
                           'PM2.5 SCI Mass', 'PM2.5 SCI Mass Error', 'PM2.5 SCI', 'PM2.5 SCI Error', 
                           'PM1 SCI Mass', 'PM1 SCI Mass Error', 'PM1 SCI', 'PM1 SCI Error','Average Flow SCI',
                           'PM2.5 PEM Mass', 'PM2.5 PEM Mass Error', 'PM2.5 PEM', 'PM2.5 PEM Error']]

df_pam_all.rename(columns = {'Average Flow_x': 'Average Flow SCI'}, inplace = True)

### saving with mass errors
df_pam_all.to_excel(backslash_correct(r'C:\PhD Research\Airborne\Processed\pm_master_all_error.xlsx'), index = False)

df_pam_all = df_pam_all[['visit', 'TSP Concentration', 'TSP Concentration Error', 
                         'PM10 SCI', 'PM10 SCI Error', 'PM2.5 SCI', 'PM2.5 SCI Error', 'PM1 SCI',
                         'PM1 SCI Error', 'PM2.5 PEM', 'PM2.5 PEM Error']]

### Saving with concentration errors only
df_pam_all.to_excel(backslash_correct(r'C:\PhD Research\Airborne\Processed\pm_master_all.xlsx'), index = False)
