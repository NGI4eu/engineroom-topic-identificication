from gaudy_functions import *
import os
from time import sleep

# Parameters to use later.
#
# Assign weights so that no site skews the results too much
# In our case, we also use it to give higher priority to European sources
# Save weights to pickle, because we use it later
# Timeframe beginning (inclusive) and end (exclusive)
# Directories to save results in (create if do not exist)

weights = {
    'ssrn': 1.0,
}

analysis_begin = '2016-01-01'  # inclusive
analysis_end = '2019-03-01'  # exclusive

res = './res_ssrn_0309/'
assets = './assets_ssrn_0309/'
grams = {1: './mod_ssrn_0309/', 2: './mod-bi_ssrn_0309/'}
make_directory(res)
make_directory(assets)
for gram_dir_name in grams.values():
    make_directory(gram_dir_name)
if abs(sum(weights.values()) - 1) > 0.000001:
    raise Exception('Sum of weights is not 1', sum(weights.values()))

important_1 = ['leaveeu','aidriven', 'gdpr','farright', 'metoo', 'misinform', 'decentr', 'monopoli',   ]
important_1 = list(set(important_1))

important_2 = ['ai startup', 'chines tech', 'digit health', 'autonom weapon', 'internet freedom', 'network neutral',
               'fake news', 'conspiraci theori', 'hate speech', 'person data', 'privaci polici', 'russian interfer',
               'youtub kid', 'black box', 'cambridg analytica', 'black box', 'money launder', 'distribut ledger' ]
important_2 = list(set(important_2))

sentiment_words = important_1

sentiment_bigrams = important_2


def prepare():
    dfs = [
    ]
    print([x.shape for x in dfs])
    df = pd.concat(dfs, axis=0)
    df['text'] = df['abstract']
    df['date'] = df['date'].apply(lambda x: x.replace('Posted: ', ''))
    df = df.loc[df['date'] != 'Posted:']
    print(df.shape)
    df = initial_transform(df, analysis_begin, analysis_end, date_columns=['date', ], title_columns=['title', ])
    df = months_columns(df)
    df['link'] = 'ssrn'
    df['site'] = 'ssrn'
    df['author'] = ''
    save_months(df, assets_dir=assets)
    save_frequencies(df, gram_dirs=grams, weights=weights, assets_dir=assets, res_dir=res)


def concat():
    save_concat(gram_dirs=grams, assets_dir=assets, res_dir=res, weights=weights)


def regression():
    reg(gram_dirs=grams, assets_dir=assets, res_dir=res)


def co_occurrence():
    for ngram, words in ((2, important_2), (1, important_1)):
        for ngram_compare, _ in ((1, important_1), (2, important_2)):
            cooc(ngram, ngram_compare, words, assets, grams, res, weights)


def sentiments():
    sentiment(important_1, weights=weights, gram_dirs=grams, assets_dir=assets, res_dir=res, ngram=1,
              ngram_compare=2)
    sentiment(important_2, weights=weights, gram_dirs=grams, assets_dir=assets, res_dir=res, ngram=2,
              ngram_compare=2)
    sentiment(important_1, weights=weights, gram_dirs=grams, assets_dir=assets, res_dir=res)
    sentiment(important_2, weights=weights, gram_dirs=grams, assets_dir=assets, res_dir=res, ngram=2,
              ngram_compare=1)
    
prepare()
concat()
regression()
co_occurrence()
sentiments()
