# -*- coding: utf-8 -*-
"""
Program to read in and process time-series DustTrack PM data

@author: alima
"""

import sys
sys.modules[__name__].__dict__.clear()

import pandas as pd
import glob
import os
exec(open(r'C:\PhD Research\Generic Codes\notion_corrections.py').read())
exec(open(r'C:\PhD Research\Generic Codes\sensor_master_generic_simple.py').read())

#####################################
### Step 1: Reading all drx files ###
#####################################

pm25_cor_factor = 1.061952

path = backslash_correct(r'C:\PhD Research\Airborne\Raw\dt\\')
exp_path = backslash_correct(r'C:\PhD Research\Airborne\Processed\dt\\')
os.chdir(path)
full_list = glob.glob('*.txt')

df = pd.DataFrame([])
for file in [f for f in full_list if 'drx' in f]:
    new_df = dt_drx_read_in(path, exp_path, file, file[:-4])
    df = df.append(new_df)

df['Date'] = '20' + df['Date'].str[8:10] + '-' + df['Date'].str[3:5] + '-' + df['Date'].str[0:2] + ' ' + df['Date'].str[-8:-2] + '00'
df['Date'] = pd.to_datetime(df['Date'])

df_sch = pd.read_excel(backslash_correct(r'C:\Career\Learning\Python Practice\Stata_Python_Booster\PhD - QFF\Des\visit_time_cutoff.xlsx'))

for i in df_sch['visit_#'].unique():
    locals()['time_%s'  %i] = df_sch.loc[i-1, 'overall']


for i in list(range(1,8)):
    j = i + 1
    # df.loc[df['Time'].between(locals()['time_%s'  %i], locals()['time_%s'  %j], inclusive = 'left'), 'visit'] = i
    df.loc[df['Date'] >= locals()['time_%s'  %i], 'visit'] = i


####################################################################
### Step 2: DustTrack data calibration using gravimetric results ###
####################################################################

## PM1
gr = pd.read_excel(backslash_correct(r'C:\PhD Research\Airborne\Processed\filter_gravimetric_master.xlsx'))
gr = gr[(gr['Filter Position'].str[0:6] == 'SCI, E') | (gr['Filter Position'].str[0:6] == 'SCI, D') | (gr['Filter Position'].str[0:6] == 'SCI, C')]
gr = gr.groupby('visit', as_index = False).agg({'PM Mass': 'sum',
                                                'Average Flow': 'mean'}, inplace = True)
c_pm1 = (gr['PM Mass'].sum()*1000) / (gr['Average Flow'].sum() * ((7*24*60)/1000)) * pm25_cor_factor

## PM2.5
gr = pd.read_excel(backslash_correct(r'C:\PhD Research\Airborne\Processed\filter_gravimetric_master.xlsx'))
gr = gr[(gr['Filter Position'].str[0:3] == 'SCI')]
gr = gr[(gr['Filter Position'].str[0:6] != 'SCI, A') ]
gr = gr.groupby('visit', as_index = False).agg({'PM Mass': 'sum',
                                                'Average Flow': 'mean'}, inplace = True)
c_pm25 = (gr['PM Mass'].sum()*1000) / (gr['Average Flow'].sum() * ((7*24*60)/1000)) * pm25_cor_factor

## PM10
gr = pd.read_excel(backslash_correct(r'C:\PhD Research\Airborne\Processed\filter_gravimetric_master.xlsx'))
gr = gr[(gr['Filter Position'].str[0:3] == 'SCI')]
gr = gr.groupby('visit', as_index = False).agg({'PM Mass': 'sum',
                                                'Average Flow': 'mean'}, inplace = True)
c_pm10 = (gr['PM Mass'].sum()*1000) / (gr['Average Flow'].sum() * ((7*24*60)/1000)) * pm25_cor_factor

## TSP
gr = pd.read_excel(backslash_correct(r'C:\PhD Research\Airborne\Processed\filter_gravimetric_master.xlsx'))
gr = gr[(gr['Filter Position'].str[0:2] == 'FC') & (gr['Filter Material'].str[0:3] == 'MCE')]
c_tsp = (gr['PM Mass'].sum()*1000) / (gr['Average Flow'].sum() * ((7*24*60)/1000)) * pm25_cor_factor

df['PM1'] = df['PM1'] * (c_pm1/df['PM1'].mean())
df['PM2.5'] = df['PM2.5'] * (c_pm25//df['PM2.5'].mean())
df['PM10'] = df['PM10'] * (c_pm10/df['PM10'].mean())
df['TSP'] = df['TSP'] * (c_tsp/df['TSP'].mean())

df.to_excel(backslash_correct(r'C:\PhD Research\Airborne\Processed\\') + 'dt_drx.xlsx', index = False)
