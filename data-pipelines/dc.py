# -*- coding: utf-8 -*-
"""
Program to read in and process time-series DC1700 PM number concentration data

@author: alima
"""

import sys
sys.modules[__name__].__dict__.clear()
import pandas as pd
import glob
import os

exec(open(r'C:\PhD Research\Generic Codes\notion_corrections.py').read())
exec(open(r'C:\PhD Research\Generic Codes\sensor_master_generic_simple.py').read())

path = backslash_correct(r'C:\PhD Research\Airborne\Raw\dc1700\\')
exp_path = backslash_correct(r'C:\PhD Research\Airborne\Processed\dc\\')
os.chdir(path)
full_list = glob.glob('*.txt')

df = pd.DataFrame([])
for file in [f for f in full_list]:
    new_df = dc_1700_read_in(path, exp_path, file, file[:-4])
    df = df.append(new_df)

df['Date/Time'] = pd.to_datetime(df['Date/Time'])
df_sch = pd.read_excel(backslash_correct(r'C:\PhD Research\Airborne\Des\visit_time_cutoff.xlsx'))

for i in df_sch['visit_#'].unique():
    locals()['time_%s'  %i] = df_sch.loc[i-1, 'overall']

for i in list(range(1,8)):
    j = i + 1
    # df.loc[df['Time'].between(locals()['time_%s'  %i], locals()['time_%s'  %j], inclusive = 'left'), 'visit'] = i
    df.loc[df['Date/Time'] >= locals()['time_%s'  %i], 'visit'] = i

df = df[df['visit'] < 7]

df.to_excel(backslash_correct(r'C:\PhD Research\Airborne\Processed\\') + 'dc_1700.xlsx', index = False)
