# -*- coding: utf-8 -*-
"""
Program to calculate runtime hours of HVAC system based on system status (Off, fan only, cooling)

@author: alima
"""

import sys
sys.modules[__name__].__dict__.clear()
import pandas as pd
exec(open(r'C:\PhD Research\Generic Codes\notion_corrections.py').read())


df = pd.read_excel(backslash_correct(r'C:\PhD Research\Airborne\Processed\runtime_master.xlsx'))

df = df[['visit', 'Mode']]
df = df[(df['Mode'] == 'Fan Only')|(df['Mode'] == 'Compressor')]
df = df.groupby(['visit', 'Mode']).size()/60

df = df.unstack(level = -1)
df.fillna(0, inplace = True)
df['Overall'] = df.sum(axis = 1)
df['visit'] = df.index
df = df[['visit', 'Fan Only', 'Compressor', 'Overall']]

df.to_excel(r'C:\PhD Research\Airborne\Processed\runtime_hr.xlsx', index = False)
