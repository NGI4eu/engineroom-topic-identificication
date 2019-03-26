from nltk.stem import SnowballStemmer
import pandas as pd
import os
from IPython.display import display

dir_name = './res_reddit/'
news_dir = ''
news2 = pd.read_csv(news_dir + 'cooc21weighted.csv', index_col=0)
news1 = pd.read_csv(news_dir + 'cooc11weighted.csv', index_col=0)
st = SnowballStemmer('english')

for filename in os.listdir(dir_name):
    if 'count_term_500' in filename:
        print(filename)
    else:
        continue
        
    term = filename.split('_child_')[1][:-4]
    term_clean = ' '.join(term.split('_'))
    term_stemmed = ' '.join([st.stem(x) for x in term.split('_')])
    red = pd.read_csv(dir_name + 'count_term_500_child_' + term + '.csv', index_col=0)
    
    if len(term.split('_')) == 2:
        news_words = news2
    else:
        news_words = news1
    
    if term_stemmed + '_count_freq_weighted' not in news_words.columns:
        continue
    news_words = news_words[[term_stemmed + '_count_freq_weighted']]
    news_words.columns = ['news']
    news_words['news_rank'] = news_words['news'].rank(method='min', ascending=False)
    
    red_words = red.loc[red['ratio'] > 100].sort_values(by='count', ascending=False)
    
    red_words = red_words[['count']]
    red_words.columns = ['reddit']
    red_words['reddit_rank'] = red_words['reddit'].rank(method='min', ascending=False)[:1000]
    
    words = news_words.join(red_words, how='outer').dropna()
    words['ratio'] = words['reddit'] / words['news']
    words['rank_diff'] = words['news_rank'] - words['reddit_rank']

    print(term)
    print('inf', words.loc[words['ratio'] > 10000].index)
    print(words.loc[words['ratio'] <= 10000].sort_values('ratio', ascending=False)[:25])
    print(words.loc[words['ratio'] <= 10000].sort_values('rank_diff', ascending=False)[:25])