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
pioneer['color_identity'] = pioneer['color_identity'].apply(lambda x: x.replace('[]', '[C]'))

## removal bool
removal_regexes = [
    # white removal
    re.compile(r'enchanted (creature|permanent) can\'t attack (?!until end of turn)'),
    re.compile(r'exile target (?!card)'),
    
    # blue removal
    re.compile(r'enchanted creature doesn\'t untap'),
    re.compile(r'return target (creature|nonland permanent) to its owner\'s hand'),
    re.compile(r'put target (creature|permanent)'),
    re.compile(r'counter target .* spell'),
    
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

# plot the data

## reshape df
card_type_breakdown = pioneer.groupby('set_name').size().reset_index(name = 'commons') # number of commons

## define function to be used for each axs
card_types = ['Creature', 'Enchantment', 'Instant', 'Sorcery', 'Artifact']
def creature_curve_variables(color_identity):
    # take a slice of the pioneer df for the color identity
    df = pioneer[pioneer['color_identity'].astype(str).str.contains(color_identity)]
    
    # establish card type breakdown and card type ratios
    card_type_breakdown = df.groupby('set_name').size().reset_index(name = 'commons')
    for card_type in card_types:
        new_df = df[df['type_line'].str.contains(card_type)].groupby('set_name').size().reset_index(name = card_type + "s")
        card_type_breakdown = card_type_breakdown.merge(new_df, how = 'left', on = 'set_name')
    card_type_breakdown = card_type_breakdown.replace(np.nan, 0).set_index('set_name')
    ctype_ratio = card_type_breakdown.iloc[:, 1:].div(card_type_breakdown.commons, axis = 0)
    
    # creatures
    creatures = df[df['type_line'].str.contains('Creature')]
    noncreatures = df[~df['type_line'].str.contains('Creature')]
    creature_curve_df = creatures.groupby(['set_name', 'cmc']).size().reset_index(name = 'cards')
    creature_curve_df = creature_curve_df.groupby('cmc').cards.agg(['mean', 'min', 'max', 'std']).reset_index()
    creature_curve_df['count_ratio'] = creature_curve_df['mean'] / creature_curve_df['mean'].sum()
    
    # additional values
    creature_ratio = ctype_ratio['Creatures'].mean()
    creatures_w_evasion = len(creatures[creatures['evasion'] == True]) / len(creatures)
    noncreature_removal_spell_ratio = len(noncreatures[noncreatures['removal'] == True]) / len(noncreatures)
    noncreature_combat_trick_ratio = len(noncreatures[noncreatures['combat_trick'] == True]) / len(noncreatures)
    
    return creature_ratio, creatures_w_evasion, creature_curve_df, noncreature_removal_spell_ratio, noncreature_combat_trick_ratio

## set up the plot
fig, axs = plt.subplots(2,3)
fig.set_figheight(18)
fig.set_figwidth(30)
fig.suptitle('Magic the Gathering:\nDistribution of Pioneer-Legal Common Cards (as of Strixhaven)', fontsize = 20)

## subplot 1: white
creature_ratio_w, creatures_w_evasion_w, creature_curve_df_w, noncreature_removal_spell_ratio_w, noncreature_combat_trick_ratio_w = creature_curve_variables('[W]')

### set axis title
axs[0,0].set_title('WHITE COMMONS:\n{} of commons are creatures. {} of creatures have evasion.\n{} of noncreatures are removal. {} of noncreatures are combat tricks.'.
              format(
                  str(round(100 * creature_ratio_w)) + '%',
                  str(round(100 * creatures_w_evasion_w)) + '%',
                  str(round(100 * noncreature_removal_spell_ratio_w)) + '%', 
                  str(round(100 * noncreature_combat_trick_ratio_w)) + '%')
              )
axs[0,0].set_xlabel('Creature Curve (Mana Value)')

### plot curve
axs[0,0].bar(x = creature_curve_df_w['cmc'], height = creature_curve_df_w['mean'], yerr = creature_curve_df_w['std'],
            color = 'ivory', edgecolor = 'black')

### add text to bars
for index, row in creature_curve_df_w.iterrows():
    axs[0,0].text(row['cmc'], 0.5, 'Ratio:', horizontalalignment = 'center')
    axs[0,0].text(row['cmc'], 0.25, round(row['count_ratio'], 2), horizontalalignment = 'center')


## subplot 2: blue
creature_ratio_u, creatures_w_evasion_u, creature_curve_df_u, noncreature_removal_spell_ratio_u, noncreature_combat_trick_ratio_u = creature_curve_variables('[U]')

### set axis title
axs[0,1].set_title('BLUE COMMONS:\n{} of commons are creatures. {} of creatures have evasion.\n{} of noncreatures are removal. {} of noncreatures are combat tricks.'.
              format(
                  str(round(100 * creature_ratio_u)) + '%',
                  str(round(100 * creatures_w_evasion_u)) + '%',
                  str(round(100 * noncreature_removal_spell_ratio_u)) + '%', 
                  str(round(100 * noncreature_combat_trick_ratio_u)) + '%')
              )
axs[0,1].set_xlabel('Creature Curve (Mana Value)')

### plot curve
axs[0,1].bar(x = creature_curve_df_u['cmc'], height = creature_curve_df_u['mean'], yerr = creature_curve_df_u['std'],
            color = 'skyblue', edgecolor = 'black')

### add text to bars
for index, row in creature_curve_df_u.iterrows():
    axs[0,1].text(row['cmc'], 0.5, 'Ratio:', horizontalalignment = 'center')
    axs[0,1].text(row['cmc'], 0.25, round(row['count_ratio'], 2), horizontalalignment = 'center')

## subplot 3: black
creature_ratio_b, creatures_w_evasion_b, creature_curve_df_b, noncreature_removal_spell_ratio_b, noncreature_combat_trick_ratio_b = creature_curve_variables('[B]')

### set axis title
axs[0,2].set_title('BLACK COMMONS:\n{} of commons are creatures. {} of creatures have evasion.\n{} of noncreatures are removal. {} of noncreatures are combat tricks.'.
              format(
                  str(round(100 * creature_ratio_b)) + '%',
                  str(round(100 * creatures_w_evasion_b)) + '%',
                  str(round(100 * noncreature_removal_spell_ratio_b)) + '%', 
                  str(round(100 * noncreature_combat_trick_ratio_b)) + '%')
              )
axs[0,2].set_xlabel('Creature Curve (Mana Value)')

### plot curve
axs[0,2].bar(x = creature_curve_df_b['cmc'], height = creature_curve_df_b['mean'], yerr = creature_curve_df_b['std'],
            color = 'darkorchid', edgecolor = 'black')

### add text to bars
for index, row in creature_curve_df_b.iterrows():
    axs[0,2].text(row['cmc'], 0.5, 'Ratio:', horizontalalignment = 'center')
    axs[0,2].text(row['cmc'], 0.25, round(row['count_ratio'], 2), horizontalalignment = 'center')

## subplot 4: red
creature_ratio_r, creatures_w_evasion_r, creature_curve_df_r, noncreature_removal_spell_ratio_r, noncreature_combat_trick_ratio_r = creature_curve_variables('[R]')

### set axis title
axs[1,0].set_title('RED COMMONS:\n{} of commons are creatures. {} of creatures have evasion.\n{} of noncreatures are removal. {} of noncreatures are combat tricks.'.
              format(
                  str(round(100 * creature_ratio_r)) + '%',
                  str(round(100 * creatures_w_evasion_r)) + '%',
                  str(round(100 * noncreature_removal_spell_ratio_r)) + '%', 
                  str(round(100 * noncreature_combat_trick_ratio_r)) + '%')
              )
axs[1,0].set_xlabel('Creature Curve (Mana Value)')

### plot curve
axs[1,0].bar(x = creature_curve_df_r['cmc'], height = creature_curve_df_r['mean'], yerr = creature_curve_df_r['std'],
            color = 'crimson', edgecolor = 'black')

### add text to bars
for index, row in creature_curve_df_r.iterrows():
    axs[1,0].text(row['cmc'], 0.5, 'Ratio:', horizontalalignment = 'center')
    axs[1,0].text(row['cmc'], 0.25, round(row['count_ratio'], 2), horizontalalignment = 'center')

## subplot 5: green
creature_ratio_g, creatures_w_evasion_g, creature_curve_df_g, noncreature_removal_spell_ratio_g, noncreature_combat_trick_ratio_g = creature_curve_variables('[G]')

### set axis title
axs[1,1].set_title('GREEN COMMONS:\n{} of commons are creatures. {} of creatures have evasion.\n{} of noncreatures are removal. {} of noncreatures are combat tricks.'.
              format(
                  str(round(100 * creature_ratio_g)) + '%',
                  str(round(100 * creatures_w_evasion_g)) + '%',
                  str(round(100 * noncreature_removal_spell_ratio_g)) + '%', 
                  str(round(100 * noncreature_combat_trick_ratio_g)) + '%')
              )
axs[1,1].set_xlabel('Creature Curve (Mana Value)')

### plot curve
axs[1,1].bar(x = creature_curve_df_g['cmc'], height = creature_curve_df_g['mean'], yerr = creature_curve_df_g['std'],
            color = 'springgreen', edgecolor = 'black')

### add text to bars
for index, row in creature_curve_df_g.iterrows():
    axs[1,1].text(row['cmc'], 0.5, 'Ratio:', horizontalalignment = 'center')
    axs[1,1].text(row['cmc'], 0.25, round(row['count_ratio'], 2), horizontalalignment = 'center')

## subplot 6: colorless
creature_ratio_c, creatures_w_evasion_c, creature_curve_df_c, noncreature_removal_spell_ratio_c, noncreature_combat_trick_ratio_c = creature_curve_variables('[C]')

### set axis title
axs[1,2].set_title('COLORLESS COMMONS:\n{} of commons are creatures. {} of creatures have evasion.\n{} of noncreatures are removal. {} of noncreatures are combat tricks.'.
              format(
                  str(round(100 * creature_ratio_c)) + '%',
                  str(round(100 * creatures_w_evasion_c)) + '%',
                  str(round(100 * noncreature_removal_spell_ratio_c)) + '%', 
                  str(round(100 * noncreature_combat_trick_ratio_c)) + '%')
              )
axs[1,2].set_xlabel('Creature Curve (Mana Value)')

### plot curve
axs[1,2].bar(x = creature_curve_df_c['cmc'], height = creature_curve_df_c['mean'], yerr = creature_curve_df_c['std'],
            color = 'gray', edgecolor = 'black')

### add text to bars
for index, row in creature_curve_df_c.iterrows():
    axs[1,2].text(row['cmc'], 0.5, 'Ratio:', horizontalalignment = 'center')
    axs[1,2].text(row['cmc'], 0.25, round(row['count_ratio'], 2), horizontalalignment = 'center')