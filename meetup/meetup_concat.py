import os
import pickle
import gc
import pandas as pd

all_meetups = {}
dir_name = './meetup_geo/'
part_count = 0
for i, filename in enumerate(sorted(os.listdir(dir_name))):
    if i % 100 == 0:
        print(i, len(all_meetups))
    x = pd.read_pickle(dir_name + filename)
    
    for meetup in x:
        if meetup.id not in all_meetups.keys():
            all_meetups[meetup.id] = meetup
    
    del x
    gc.collect()
    
pickle.dump(all_meetups, open('all_meetups_unique.pickle', 'wb'))