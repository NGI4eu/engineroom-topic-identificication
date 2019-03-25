# transform data to form possible to display on map

import pandas as pd
import numpy as np
import folium
import os
import string
from pyproj import Proj, transform

all_events = pd.read_pickle('all_meetups_unique.pickle')
events = []
for i, event in all_events.items():
    events.append(
        {'name': event.name, 'lat': event.lat, 'lon': event.lon, 'members': event.members,
         'created': event.created, 'description': event.description, 'city': event.city}
    )

events = pd.DataFrame(events)
events.drop_duplicates(inplace=True)
events['date'] = events['created'].apply(lambda x: pd.to_datetime(int(str(x) + '000000')))
events['year_month'] = events['date'].apply(lambda x: str(x.year) + '-' + str(x.month).zfill(2))
events['from_year'] = events['date'].apply(lambda x: (x - pd.to_datetime('2008-01-01')).days)
events['from_year'] = events['from_year'].apply(lambda x: x if x > 0 else 0)

# convert to true area representation projection
in_proj = Proj(init = 'epsg:4326')
out_proj = Proj(init = 'epsg:3035')
events['coord'] = events[['lon', 'lat']].apply(
    lambda row: transform(in_proj, out_proj, row['lon'], row['lat']), axis = 1)
events['x'] = events['coord'].apply(lambda x: x[0])
events['y'] = events['coord'].apply(lambda x: x[1])

mult = (events['x'].max() - events['x'].min()) / (events['y'].max() - events['y'].min())

# display on Processing canvas
events['y'] = 1000 - 1000*((events['y'] - events['y'].min()) / (events['y'].max() - events['y'].min()))
events['x'] = 125 + mult*1000*((events['x'] - events['x'].min()) / (events['x'].max() - events['x'].min()))
events['code'] = -1

events_ai = events.loc[(events['name'].str.contains('AI')) | (
    events['name'].str.lower().str.contains('artificial intellig')) | (
    events['name'].str.lower().str.contains('machine learning')) | (
    events['description'].str.lower().str.contains('machine learning')) |
    (events['description'].str.lower().str.contains('artificial intellig'))
                      ]

events_web = events.loc[(events['name'].str.contains('JS')) | (
    events['name'].str.lower().str.contains('javascript')) | (
    events['name'].str.contains('HTML')) | (
    (events['name'].str.lower().str.contains('web')) & ~(events['name'].str.lower().str.contains('webinar'))) |
    (events['description'].str.lower().str.contains('javascript')) |
    (events['description'].str.contains('JS'))]

events_agile = events.loc[(events['description'].str.contains('Agil')) |
    events['name'].str.contains('Agil')]

print(events_ai.shape, events_web.shape, events_agile.shape)
events_ai['code'] = 0
events_web['code'] = 1
events_agile['code'] = 2

events_all = pd.concat([events_ai, events_web, events_agile])

with open('./meetups.csv', 'a') as f:
    for i, row in events_all.iterrows():
        f.write(','.join([str(row['x']),
                str(row['y']),
                str((row['from_year'] // 3) + 1),
                str(row['members']),
                str(row['code'])]) + '\n')