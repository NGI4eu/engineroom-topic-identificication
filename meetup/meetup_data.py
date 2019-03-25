# download data from meetup API
# largest towns in the world

import pandas as pd
import numpy as np
import meetup.api
import pickle

client_id = ''  # insert client id

cities = pd.read_csv('cities15000.txt', header=None, sep='\t')

columns_txt = '''geonameid         : integer id of record in geonames database
name              : name of geographical point (utf8) varchar(200)
asciiname         : name of geographical point in plain ascii characters, varchar(200)
alternatenames    : alternatenames, comma separated, ascii names automatically transliterated, convenience attribute from alternatename table, varchar(10000)
latitude          : latitude in decimal degrees (wgs84)
longitude         : longitude in decimal degrees (wgs84)
feature class     : see http://www.geonames.org/export/codes.html, char(1)
feature code      : see http://www.geonames.org/export/codes.html, varchar(10)
country code      : ISO-3166 2-letter country code, 2 characters
cc2               : alternate country codes, comma separated, ISO-3166 2-letter country code, 200 characters
admin1 code       : fipscode (subject to change to iso code), see exceptions below, see file admin1Codes.txt for display names of this code; varchar(20)
admin2 code       : code for the second administrative division, a county in the US, see file admin2Codes.txt; varchar(80) 
admin3 code       : code for third level administrative division, varchar(20)
admin4 code       : code for fourth level administrative division, varchar(20)
population        : bigint (8 byte int) 
elevation         : in meters, integer
dem               : digital elevation model, srtm3 or gtopo30, average elevation of 3''x3'' (ca 90mx90m) or 30''x30'' (ca 900mx900m) area in meters, integer. srtm processed by cgiar/ciat.
timezone          : the iana timezone id (see file timeZone.txt) varchar(40)
modification date : date of last modification in yyyy-MM-dd format'''
cities.columns = [x.split(':')[0].strip() for x in columns_txt.split('\n')]

cities['continent'] = cities['timezone'].apply(lambda x: x.split('/')[0])
cities_europe = cities.loc[cities['continent'] == 'Europe'].sort_values('population', ascending=False)
cities_america = cities.loc[cities['country code'].isin(
    ['US', 'MX', 'CA'])].sort_values('population', ascending=False)

client = meetup.api.Client(client_id)

cities_all = pd.concat([cities_europe, cities_america])
dir_name = './meetup_geo/'
for i, row in cities_all.iterrows():
    city = row['country code'] + '_' + row['asciiname'].replace('/', '')
    lat, lon = row['latitude'], row['longitude']
    groups = client.GetFindGroups(lat = lat, lon = lon, category = [2])
    pickle.dump(groups, open(dir_name + city + '_business.pickle', 'wb'))
    groups = client.GetFindGroups(lat = lat, lon = lon, category = [34])
    pickle.dump(groups, open(dir_name + city + '_tech.pickle', 'wb'))
    groups = client.GetFindGroups(lat = lat, lon = lon)
    pickle.dump(groups, open(dir_name + city + '.pickle', 'wb'))