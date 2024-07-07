# -*- coding: utf-8 -*-
"""
Program to calculate the runtime fraction of HVAC system using pressure sensor data based on different statuses of Cooling, Fan Only, and Off

@author: alima
"""

import sys
sys.modules[__name__].__dict__.clear()

import pandas as pd
import numpy as np

#############################################################
### Step 1: Reading raw pressure sensor data and refining ###
#############################################################

exec(open(r'C:\PhD Research\Generic Codes\notion_corrections.py').read())
df_sch = pd.read_excel(backslash_correct(r'C:\PhD Research\Airborne\Des\visit_time_cutoff.xlsx'))

for i in df_sch['visit_#'].unique():
    locals()['time_%s'  %i] = df_sch.loc[i-1, 'overall']

df = pd.read_csv(backslash_correct(r'C:\PhD Research\Airborne\Raw\runtime\qff_eval_verisx_145_180829_am.csv'), skiprows = 1)
df = df[['Date Time, GMT-04:00', 'Pressure, Pa (LGR S/N: 10570145)']]
df.rename(columns = {'Date Time, GMT-04:00': 'Time',
                     'Pressure, Pa (LGR S/N: 10570145)': 'Pressure'}, inplace = True)
df.iloc[:,1] = (df.iloc[:,1] - df.iloc[0,1]).abs()



df['Time'] = '20' + df['Time'].str[6:8] + '-' + df['Time'].str[3:5] + '-' + df['Time'].str[0:2] + ' ' + df['Time'].str[-8:]
df['Time'] = pd.to_datetime(df['Time'])

for i in list(range(1,8)):
    j = i + 1
    # df.loc[df['Time'].between(locals()['time_%s'  %i], locals()['time_%s'  %j], inclusive = 'left'), 'visit'] = i
    df.loc[df['Time'] >= locals()['time_%s'  %i], 'visit'] = i

df = df[~(df['visit'] == 7)]


##########################################
### Step 2: System stats determination ###
##########################################

df['Mode'] = 'Transient'
df.loc[df['Pressure'] <= 1, 'Mode'] = 'Off'
df.loc[df['Pressure'] >= 25 , 'Mode'] = 'Compressor'
df.loc[df['Pressure'].between(15,20, inclusive='left'), 'Mode'] = 'Fan Only'

df['Mode'].unique()
df['Mode'].value_counts()
len(df['Mode'])


##############################################
### Step 3: Other processing and exporting ###
##############################################

df.to_excel(backslash_correct(r'C:\PhD Research\Airborne\Processed\runtime_master.xlsx'), index = False)

# length, Fan, and Compressors are ok which is good.

## Aggreate per visit and mode
# df = df[df['Mode'] != 'Transient'] # removing Transient
df_size = df.groupby(['visit', 'Mode'], as_index = False).size()
df_count = df.groupby(['visit'], as_index = False).size()

df_rt_mode = df_size.merge(df_count, on = 'visit', how = 'outer')
df_rt_mode['runtime'] = (df_rt_mode['size_x'] / df_rt_mode['size_y']) * 100
df_rt_mode.drop(['size_x' , 'size_y'], axis = 1, inplace = True)
df_rt_mode.to_excel(backslash_correct(r'C:\PhD Research\Airborne\Processed\runtime_sum_mode.xlsx'), index = False)   

df_rt_unst = df_rt_mode

## Aggreate per visit only
df_rt_all = df_rt_mode
df_rt_all.loc[df_rt_all['Mode'] == 'Transient', 'Mode'] = 'Off'
df_rt_all.loc[df_rt_all['Mode'] != 'Off', 'Mode'] = 'On'
df_rt_all = df_rt_all.groupby(['visit', 'Mode'], as_index = False)['runtime'].sum()
df_rt_all.to_excel(backslash_correct(r'C:\PhD Research\Airborne\Processed\runtime_sum.xlsx'), index = False)   
