# -*- coding: utf-8 -*-
"""
Program to read and process method detection limit (MDL) error for trace metal measurements

@author: alima
"""

import sys
sys.modules[__name__].__dict__.clear()
import pandas as pd

dustmass = 0.11215

exec(open(r'C:\PhD Research\Generic Codes\notion_corrections.py').read())
elem_list = stata_varlist_split('Pb As Cd Cu Zn Ni K Ti V Fe Sr Sb')
df = pd.read_excel(backslash_correct(r'C:\Career\Learning\Python Practice\Stata_Python_Booster\PhD - QFF\Des\Chemicals\Metals Results_Alireza.xlsx'), sheet_name = 'raw')
df = df[['Dust/tsp mass_mg'] + elem_list].iloc[13:18].astype(float)

for col in elem_list:
    df[col] = df[col] * df['Dust/tsp mass_mg']/1000
    
df = pd.concat([df[elem_list].std(),df[elem_list].std()], axis = 1).T
df.loc[0, 'type'] = 'mf'
df.loc[1, 'type'] = 'f'

df.iloc[0,0:12] = df.iloc[0,0:12] * 3
df.iloc[1,0:12] = df.iloc[1,0:12] / dustmass

df.to_excel(backslash_correct(r'C:\PhD Research\Airborne\Processed\tm_mdl_errors.xlsx'), index = False)
