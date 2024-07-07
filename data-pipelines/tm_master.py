# -*- coding: utf-8 -*-
"""
Program to make a master spreadsheet for the concentration of the studied trace metals 

@author: alima
"""

'''
There are three sources of errors:
    1) cv (which is the coef of variations between 2 or 3 MCE filters of same visits)
    2) device errors: uncertainties arising from the device (from metals_UC spreadsheet)
    3) mdl: method detection limit (constant across all visits) (from tm_mdl_error.py and 'Metals Resutls - ALireza' spreadsheet)
    
'''

import sys
sys.modules[__name__].__dict__.clear()
import pandas as pd
import re
import numpy as np
exec(open(r'C:\PhD Research\Generic Codes\notion_corrections.py').read())

elem_list = stata_varlist_split('Pb As Cd Cu Zn Ni K Ti V Fe Sr Sb')

############################################################################
### Step 1: Calculating cv error arising from same visit tm measurements ###
############################################################################
 
df1 = pd.read_excel(backslash_correct('C:\PhD Research\Airborne\Des\Chemicals\Metals Results_Alireza.xlsx'), sheet_name = 'conversions')
df1.dropna(subset = ['SN'], inplace = True)
df1 = df1[~(df1['SN'].str[0:1] == 'P')]
df1 = df1[~(df1['Location deployed'] == 'PEM')]
df1 = df1[~(df1['Location deployed'] == 'Blank')]
df1.sort_values(['Location deployed', 'SN'], inplace = True)
del df1['Unnamed: 4']

df1[['Dust/tsp mass_mg'] + elem_list] = df1[['Dust/tsp mass_mg'] + elem_list].astype(float)
df1 = df1[['SN', 'Location deployed', 'Dust/tsp mass_mg'] + elem_list]
df1.rename(columns = {'SN': 'Filter S/N'}, inplace = True)

df2 = pd.read_excel(backslash_correct(r'C:\PhD Research\Airborne\Des\Filter_Master_v21_200206_am.xlsx'))
df = df1.merge(df2, on = 'Filter S/N', how = 'outer')
df.dropna(subset = ['Location deployed'], inplace = True)

df = df[['Filter S/N', 'Visit_#', 'Location deployed', 'Average Flow'] + elem_list]
df['Visit_#'] = df['Visit_#'].str[-1:].astype(int)

for col in elem_list:
    df[col] = (df[col]/df['Average Flow'])

a = df.groupby('Visit_#', as_index = False)[elem_list].agg('std')
for col in elem_list:
    a.rename(columns = {col: col + '_std'}, inplace = True)   
    
    
b = df.groupby('Visit_#', as_index = False)[elem_list].agg('mean') 
for col in elem_list:
    b.rename(columns = {col: col + '_mean'}, inplace = True)   

df_tm_cv = a.merge(b, on = 'Visit_#')

for col in elem_list:
    df_tm_cv[col + '_cv'] = df_tm_cv[col + '_std'] / df_tm_cv[col + '_mean']
    
df_tm_cv = df_tm_cv[['Visit_#'] + [col for col in df_tm_cv.columns if ('_cv' in col)]]
df_tm_cv.rename(columns = {'Visit_#': 'visit'}, inplace = True)

df_cv_error = pd.read_excel(backslash_correct('C:\PhD Research\Airborne\Des\Chemicals\Metals Results_Alireza.xlsx'), sheet_name = 'conversions')
df_cv_error.dropna(subset = ['SN'], inplace = True)
df_cv_error = df_cv_error[~(df_cv_error['SN'].str[0:1] == 'P')]
df_cv_error = df_cv_error[~(df_cv_error['Location deployed'] == 'PEM')]
df_cv_error = df_cv_error[~(df_cv_error['Location deployed'] == 'Blank')]
df_cv_error = df_cv_error[['SN'] + elem_list]
df_cv_error.rename(columns = {'SN': 'Filter S/N'}, inplace = True)
df_cv_error = pd.concat([df_cv_error['Filter S/N'],df_cv_error.iloc[:,1:].astype(float)], axis = 1)

fgm = pd.read_excel(backslash_correct(r'C:\PhD Research\Airborne\Processed\filter_gravimetric_master.xlsx')) # fgm stands for filter_gravimetric_master

df_cv_error = df_cv_error.merge(fgm, on = 'Filter S/N', how = 'inner')
df_cv_error = df_cv_error[['visit'] + elem_list]

df_count = df_cv_error ## This is for later calculation of normalizer

df_cv_error = df_cv_error.groupby('visit', as_index = False)[elem_list].agg('mean')
df_cv_error = df_cv_error.merge(df_tm_cv, on = 'visit', how = 'outer')

for var in elem_list:
    df_cv_error[var] = df_cv_error[var + '_cv'] * df_cv_error[var]

df_cv_error = df_cv_error[['visit'] + elem_list]
ren = [col + '_cv_error' for col in elem_list]
df_cv_error.rename(columns = dict(zip(elem_list, ren)), inplace= True)


######################################################################
### Step 2: Calculating device error arising from ICP measurements ###
######################################################################

df_dev_error = pd.read_excel(backslash_correct(r'C:\PhD Research\Airborne\Des\Chemicals\Metals_UC.xlsx'))
df_dev_error = df_dev_error[1:]

df_dev_error.rename(columns = {'Unnamed: 0': 'Filter S/N'}, inplace = True)

pattern = '\D+'
a = dict(zip([col for col in df_dev_error.columns][1:], [re.findall(pattern,col)[0] for col in df_dev_error.columns][1:]))

df_dev_error.rename(columns = a, inplace = True)

for col in elem_list:
    df_dev_error.rename(columns = {col : col + '_dev_error'}, 
                 inplace = True)

df_dev_error = df_dev_error[['Filter S/N'] + [col for col in df_dev_error.columns if '_dev_error' in col]]

df_dev_error = df_dev_error.merge(fgm, on = 'Filter S/N', how = 'inner')
df_dev_error = df_dev_error[df_dev_error['Filter Position'] != 'Blank']
df_dev_error = df_dev_error[['visit', 'Filter S/N', 'PM Mass'] + [col + '_dev_error' for col in elem_list]]

for col in [item + '_dev_error' for item in elem_list]:
    df_dev_error[col] = (df_dev_error['PM Mass'] *  df_dev_error[col]) / 1000 # making mass in ug

del df_dev_error['PM Mass']

for col in elem_list:
    df_dev_error[col + '_dev_error'] = df_dev_error[col + '_dev_error'].pow(2)

t = [col for col in df_dev_error.columns if col.split("_")[0] in elem_list]
df_dev_error = df_dev_error.groupby('visit', as_index = False)[t].sum() 
df_dev_error.iloc[:,1:] = df_dev_error.iloc[:,1:].pow(0.5)


######################################################################
### Step 3: Calculating count normalizer for mdl and device errors ###
######################################################################

df_count = df_count.groupby('visit', as_index = False)[elem_list].agg('count')

for col in elem_list:
    df_count.rename(columns = {col : col + '_count'}, inplace = True)


###################################################################
### Step 4: Calculating mdl error arising from ICP measurements ###
###################################################################

df_mdl_error = pd.read_excel(backslash_correct(r'C:\PhD Research\Airborne\Processed\tm_mdl_errors.xlsx'))

df_mdl_error = pd.concat([df_mdl_error.iloc[0,:-1]] * 6, axis = 1).T
df_mdl_error = df_mdl_error.astype(float)
df_mdl_error['visit'] = df_mdl_error.reset_index().index + 1
df_mdl_error = df_mdl_error[['visit'] + elem_list]


df_mdl_error = df_mdl_error.merge(df_count, on ='visit', how = 'outer')

for col in elem_list:
    df_mdl_error[col] = df_mdl_error[col] * df_mdl_error[col + '_count'].pow(0.5)
    df_mdl_error.rename(columns = {col : col + '_mdl_error'}, inplace = True)

# test = df_mdl_error.pow(2)
df_mdl_error = df_mdl_error[['visit'] + [col for col in df_mdl_error.columns if '_mdl_error' in col]]


#############################################################################
### Step 5: Bringing all errors together and calculate the ultimate error ###
#############################################################################

tm_error_all = pd.concat([df_cv_error, df_dev_error, df_mdl_error, df_count], axis = 1)
tm_error_all = tm_error_all.T.drop_duplicates().T # getting rid of duplicate columns

tm_error_all.rename(columns = {'Pb_count': 'count'}, inplace = True)

for var in elem_list:
    tm_error_all[var + '_error'] = np.sqrt((1/(tm_error_all['count'].pow(2)))*(tm_error_all[var + '_dev_error'].pow(2) + tm_error_all[var + '_mdl_error'].pow(2)) + tm_error_all[var + '_cv_error'].pow(2))


tm_error_all = tm_error_all[['visit'] + [(col + '_error') for col in elem_list]]
# tm_error_all.to_excel(backslash_correct(r'C:\Career\Learning\Python Practice\Stata_Python_Booster\PhD - QFF\Processed\tm_mass_errors.xlsx'), index = False)
                                                                                     
'''
    ['visit', 'Pb_dev_error', 'As_dev_error', 'Cd_dev_error', 'Cu_dev_error',
       'Zn_dev_error', 'Ni_dev_error', 'K_dev_error', 'Ti_dev_error',
       'V_dev_error', 'Fe_dev_error', 'Sr_dev_error', 'Sb_dev_error',
       'Pb_mdl_error', 'As_mdl_error', 'Cd_mdl_error', 'Cu_mdl_error',
       'Zn_mdl_error', 'Ni_mdl_error', 'K_mdl_error', 'Ti_mdl_error',
       'V_mdl_error', 'Fe_mdl_error', 'Sr_mdl_error', 'Sb_mdl_error',
       'Pb_dev_error_count', 'As_dev_error_count', 'Cd_dev_error_count',
       'Cu_dev_error_count', 'Zn_dev_error_count', 'Ni_dev_error_count',
       'K_dev_error_count', 'Ti_dev_error_count', 'V_dev_error_count',
       'Fe_dev_error_count', 'Sr_dev_error_count', 'Sb_dev_error_count',
       'Pb_cv_error', 'As_cv_error', 'Cd_cv_error', 'Cu_cv_error',
       'Zn_cv_error', 'Ni_cv_error', 'K_cv_error', 'Ti_cv_error', 'V_cv_error',
       'Fe_cv_error', 'Sr_cv_error', 'Sb_cv_error']
       
'''     

#################################################
### Step 6: Calculating weekly concentrations ###
#################################################

df_a = pd.read_excel(backslash_correct(r'C:\PhD Research\Airborne\Des\Filter_Master_v21_200206_am.xlsx'))
df_b = pd.read_excel(backslash_correct(r'C:\PhD Research\Airborne\Des\Chemicals\Metals Results_Alireza.xlsx'), sheet_name = 'conversions')

df_b.dropna(subset = ['SN'], inplace = True)
df_b = df_b[~(df_b['SN'].str[0:1] == 'P')]
df_b = df_b[~(df_b['Location deployed'] == 'PEM')]
df_b = df_b[~(df_b['Location deployed'] == 'Blank')]
df_b.sort_values(['Location deployed', 'SN'], inplace = True)
df_b.rename(columns = {'SN': 'Filter S/N'}, inplace = True)

df = df_a.merge(df_b, on = 'Filter S/N', how = 'inner')
df = df[['Filter S/N', 'Visit_#', 'Location deployed', 'Average Flow'] + elem_list]
df.dropna(subset = ['Average Flow'], inplace =True)
df[elem_list] = df[elem_list].astype(float)
df['Visit_#'] = df['Visit_#'].str[-1:].astype(int)
df.rename(columns = {'Visit_#' : 'visit'}, inplace = True)

df = df.groupby('visit', as_index = False)[['Average Flow'] + elem_list].mean()
df = df.merge(tm_error_all, on = 'visit')

#### Saving a copy of all mass terms and theri errors prior to the final concentration (and error) calculations
df.to_excel(backslash_correct(r'C:\PhD Research\Airborne\Processed\tm_mass.xlsx'), index = False)

for col in elem_list:
    var = col + '_error'
    df.loc[(df['visit'] == 1) | (df['visit'] == 6), var] = np.sqrt((df[var]/df[col]).pow(2) + (0.1/(2**(1/2) * df['Average Flow'])).pow(2) + (0.025) ** 2)
    df.loc[(df['visit'] != 1) & (df['visit'] != 6), var] = np.sqrt((df[var]/df[col]).pow(2) + (0.1/(3**(1/2) * df['Average Flow'])).pow(2) + (0.025) ** 2)
    
    df[col + '_mass'] = df[col]
    df[col] = (df[col] * 1000)/(df['Average Flow'] * ((7*24*60)/1000))
    df[var] = df[col] * df[var]

df.to_excel(backslash_correct(r'C:\PhD Research\Airborne\Processed\tm_concentration_master.xlsx'), index = False)
