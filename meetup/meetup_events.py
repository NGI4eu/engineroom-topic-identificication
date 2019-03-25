import pandas as pd
import numpy as np
import meetup.api
from time import sleep
import pickle

client_id = ''
client = meetup.api.Client(client_id)

groups = pd.read_pickle('all_meetups_unique.pickle')

dir_name = './events/'
if not os.path.exists(dir_name):
    os.makedirs(dir_name)

counter = 0
all_events = {}
for i, group in groups.items():
    while True:
        try:
            print(i, group.id)
            events = client.GetEvents(group_id = group.id, status = 'past,upcoming')
            break
        except Exception as ex:
            print(i, group.id, ex)
            sleep(1)
    
    all_events[i] = events
    if counter % 100 == 0 and counter > 0:
        pickle.dump(all_events, open(dir_name + str(counter) + '.pickle', 'wb'))
        all_events = {}
    counter += 1
pickle.dump(all_events, open(dir_name + str(counter) + '.pickle', 'wb'))