# -*- coding: utf-8 -*-
"""
Created on Tue Jun 15 10:15:31 2021

@author: ncruickshank

"""

import datetime
print("Script last ran on", datetime.datetime.today().strftime("%m/%d/%Y"))

# libraries
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import re
import requests

# data
pioneer = pd.read_csv('scryfall_pioneer_20210614.csv')

# tidy dataframe
## evasion bool
evasion_keywords = ['Flying', 'Trample', 'Menace',
                    'Plainswalk', 'Islandwalk', 'Forestwalk', 'Mountainwalk', 'Swampwalk',
                    'Skulk', 'Shadow', 'Fear', 'Intimidate']
pioneer['evasion'] = pioneer['keywords'].apply(lambda x: bool(any(item in x for item in evasion_keywords)))

## removal bool
removal_regexes = [
    # white removal
    re.compile(r'enchanted (creature|permanent) can\'t attack (?!until end of turn)'),
    re.compile(r'exile target (?!card)'),
    
    # blue removal
    re.compile(r'enchanted creature doesn\'t untap'),
    re.compile(r'return target (creature|nonland permanent) to its owner\'s hand'),
    re.compile(r'put target (creature|permanent)'),
    
    # black removal
    re.compile(r'destroy target (creature|permanent)'),
    re.compile(r'target (player|opponent) sacrifice'),
    re.compile(r'(\+|-)[0-9]*/-[1-9]* until end of turn'),
    
    # red removal
    re.compile(r'deals [0-9]* damage'),
    
    # green removal
    re.compile(r'deals damage equal'),
    re.compile(r'target creature .* control(s)? fight')
]

pioneer['removal'] = pioneer['oracle_text'].astype(str).apply(lambda x: bool(any(regex.search(x.lower()) for regex in removal_regexes)))

## combat trick bool
combat_regexes = [
    re.compile(r'target creature .* gets (\+|-)[0-9]*/(\+|-)[0-9]*'),
    re.compile(r'tap target creature'),
    re.compile(r'tap up to (two|three|four) target creature'),
    re.compile(r'target creature can\'t block this turn'),
    re.compile(r'creatures can\'t block'),
    re.compile(r'target creature blocks this turn if able'),
    re.compile(r'target creature gains .* until end of turn'),
    re.compile(r'\+1/\+1 (counter|counters) on target creature'),
    re.compile(r'untap target creature'),
    re.compile(r'creatures you control .* until end of turn')
]

pioneer['combat_trick'] = pioneer['oracle_text'].astype(str).apply(lambda x: bool(any(regex.search(x.lower()) for regex in combat_regexes)))

# summary statistics by set
card_type_breakdown = pioneer.groupby('set_name').size().reset_index(name = 'commons') # number of commons

card_types = ['Creature', 'Enchantment', 'Instant', 'Sorcery', 'Artifact']
for card_type in card_types:
    new_df = pioneer[pioneer['type_line'].str.contains(card_type)].groupby('set_name').size().reset_index(name = card_type + "s")
    card_type_breakdown = card_type_breakdown.merge(new_df, how = 'left', on = 'set_name')

card_type_breakdown = card_type_breakdown.replace(np.nan, 0)

fig, axs = plt.subplots(2,3)
fig.set_figheight(15)
fig.set_figwidth(30)
fig.suptitle('MTG Pioneer Sets: Common Creature Curve', fontsize = 20)

## subplot 1: white

## white dfs
white = pioneer[pioneer['color_identity'].astype(str).str.contains("W")]
card_type_breakdown_w = white.groupby('set_name').size().reset_index(name = 'commons') # number of commons

card_types = ['Creature', 'Enchantment', 'Instant', 'Sorcery', 'Artifact']
for card_type in card_types:
    new_df = white[white['type_line'].str.contains(card_type)].groupby('set_name').size().reset_index(name = card_type + "s")
    card_type_breakdown_w = card_type_breakdown_w.merge(new_df, how = 'left', on = 'set_name')

card_type_breakdown_w = card_type_breakdown_w.replace(np.nan, 0).set_index('set_name')
ctypes_ratio_w = card_type_breakdown_w.iloc[:, 1:].div(card_type_breakdown_w.commons, axis = 0)
#ratio_sums = [row.Creatures + row.Enchantments + row.Instants + row.Sorcerys + row.Artifacts for index, row in ctypes_ratio_w.iterrows()]
#ctypes_ratio_w['ratio_sums'] = ratio_sums

white_creatures = white[white['type_line'].str.contains('Creature')]
creature_curve_df_w = white_creatures.groupby(['set_name', 'cmc']).size().reset_index(name = 'cards')
creature_curve_df_w = creature_curve_df_w.groupby('cmc').cards.agg(['mean', 'min', 'max', 'std']).reset_index()
creature_curve_df_w['count_ratio'] = creature_curve_df_w['mean'] / creature_curve_df_w['mean'].sum()

creature_ratio_w = ctypes_ratio_w['Creatures'].mean()
creatures_w_evasion = len(white_creatures[white_creatures['evasion'] == True]) / len(white_creatures)

axs[0,0].set_title('WHITE: {} of commons are creatures. {} of creatures have evasion.'.
              format(str(round(100 * creature_ratio_w)) + '%', str(round(100*creatures_w_evasion)) + '%'))
axs[0,0].bar(x = creature_curve_df_w['cmc'], height = creature_curve_df_w['mean'], yerr = creature_curve_df_w['std'],
            color = 'ivory', edgecolor = 'black')
for index, row in creature_curve_df_w.iterrows():
    axs[0,0].text(row['cmc'], 0.5, 'Ratio:', horizontalalignment = 'center')
    axs[0,0].text(row['cmc'], 0.25, round(row['count_ratio'], 2), horizontalalignment = 'center')


## subplot 2: blue
axs[0,1].set_title('Blue')

## subplot 3: black
axs[0,2].set_title('Black')

## subplot 4: red
axs[1,0].set_title('Red')

## subplot 5: green
axs[1,1].set_title('Green')

## subplot 6: colorless
axs[1,2].set_title('Colorless')