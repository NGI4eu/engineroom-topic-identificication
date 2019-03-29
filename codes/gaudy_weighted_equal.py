from gaudy_functions import *

# Parameters to use later.
#
# Assign weights so that no site skews the results too much
# In our case, we also use it to give higher priority to European sources
# Save weights to pickle, because we use it later
# Timeframe beginning (inclusive) and end (exclusive)
# Directories to save results in (create if do not exist)

weights = {
    'ieee': 0.06,
    'gigaom': 0.01,
    'arstechnica': 0.06,
    'zdnet': 0.1,
    'theguardian': 0.165,
    'gizmodo': 0.1,
    'fastcompany': 0.06,
    'register': 0.165,
    'theconversation': 0.06,
    'reuters': 0.06,
    'techforge': 0.06,
    'politico': 0.06,
    'euractiv': 0.04,
}


analysis_begin = '2016-01-01'  # inclusive
analysis_end = '2019-03-01'  # exclusive

res = './res_0307_weighted_111/'
assets = './assets_0307_weighted_111/'
grams = {1: './mod_0307_weighted_111/', 2: './mod-bi_0307_weighted_111/'}
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

<<<<<<< HEAD
def prepare():
    dfs = [
=======

def fix_date(x):
    x['date'] = x['date'].apply(lambda x: pd.to_datetime(x, format='%d-%m-%Y'))
    return x


def fix_text(x):
    x['text'] = x['text'].str.replace('\n', '\n\n')
    return x


def fix_months(x):
	for pol, eng in (('sty', 'January'),
		('lut', 'February'),
		('mar', 'March'),
		('kwi', 'April'),
		('maj', 'May'),
		('cze', 'June'),
		('lip', 'July'),
		('sie', 'August'),
		('wrz', 'September'),
		('paź', 'October'),
		('lis', 'November'),
		('gru', 'December')):
		x['date'] = x['date'].str.replace(pol, eng)
	return x


def fix_link(x, value):
	x['link'] = value
	return x


def prepare():
    dfs = [
        pd.read_csv('../engineroom_scraping/arstechnica.csv'),
        pd.read_csv('../engineroom_scraping/arstechnica_01.csv'),
        pd.read_csv('../engineroom_scraping/arstechnica_04.csv'),
        pd.read_csv('../engineroom_scraping/arstechnica_09.csv'),
        pd.read_csv('../engineroom_scraping/arstechnica_1903.csv'),
        pd.read_csv('../engineroom_scraping/zdnet.csv'),
        pd.read_csv('../engineroom_scraping/zdnet_01.csv'),
        pd.read_csv('../engineroom_scraping/zdnet_04.csv'),
        pd.read_csv('../engineroom_scraping/zdnet_09.csv'),
        pd.read_csv('../engineroom_scraping/zdnet_1903.csv'),
        pd.read_csv('../engineroom_scraping/gigaom.csv'),
        pd.read_csv('../engineroom_scraping/gigaom_01.csv'),
        pd.read_csv('../engineroom_scraping/gigaom_04.csv'),
        pd.read_csv('../engineroom_scraping/gigaom_09.csv'),
        pd.read_csv('../engineroom_scraping/gigaom_1903.csv'),
        pd.read_csv('../engineroom_scraping/gizmodo.csv'),
        pd.read_csv('../engineroom_scraping/gizmodo_01.csv'),
        pd.read_csv('../engineroom_scraping/gizmodo_04.csv'),
        pd.read_csv('../engineroom_scraping/gizmodo_09.csv'),
        pd.read_csv('../engineroom_scraping/gizmodo_1903.csv'),
        pd.read_csv('../engineroom_scraping/theguardian.csv'),
        pd.read_csv('../engineroom_scraping/theguardian_01.csv'),
        pd.read_csv('../engineroom_scraping/theguardian_04.csv'),
        pd.read_csv('../engineroom_scraping/theguardian_09.csv'),
        pd.read_csv('../engineroom_scraping/theguardian_1903.csv'),
        pd.read_csv('../engineroom_scraping/fastcompany.csv'),
        pd.read_csv('../engineroom_scraping/fastcompany_01.csv'),
        pd.read_csv('../engineroom_scraping/fastcompany_04.csv'),
        pd.read_csv('../engineroom_scraping/fastcompany_09.csv'),
        pd.read_csv('../engineroom_scraping/fastcompany_1903.csv'),
        fix_text(pd.read_csv('../engineroom_scraping/ieee_01_full.csv')),
        fix_date(fix_text(pd.read_pickle('../engineroom_scraping/ieee_april.p'))),
        pd.read_csv('../engineroom_scraping/ieee_09.csv'),
        pd.read_csv('../engineroom_scraping/ieee_1903.csv'),
        fix_text(pd.read_csv('../engineroom_scraping/register_01_full.csv')),
        fix_date(fix_text(pd.read_pickle('../engineroom_scraping/register_april.p'))),
        pd.read_csv('../engineroom_scraping/register_09.csv'),
        pd.read_csv('../engineroom_scraping/register_1903.csv'),
        pd.read_csv('../engineroom_scraping/theconversation_04.csv'),
        pd.read_csv('../engineroom_scraping/theconversation_09.csv'),
        pd.read_csv('../engineroom_scraping/theconversation_1903.csv'),
        pd.read_csv('../engineroom_scraping/techforge_04.csv'),
        pd.read_csv('../engineroom_scraping/techforge_09.csv'),
        pd.read_csv('../engineroom_scraping/techforge_1903.csv'),
        pd.read_csv('../engineroom_scraping/reuters_04.csv'),
        pd.read_csv('../engineroom_scraping/reuters_09.csv'),
        pd.read_csv('../engineroom_scraping/reuters_1903.csv'),
        fix_link(fix_months(pd.read_csv('../engineroom_scraping/euractiv_1903.csv')), 'euractiv'),
        pd.read_csv('../engineroom_scraping/politico_1903.csv'),
>>>>>>> 0cd159f401e3f5c0fe800013dd578d725f38fc98
    ]
    print([x.shape for x in dfs])
    df = pd.concat(dfs, axis=0)
    print(df.shape)
    df = initial_transform(df, analysis_begin, analysis_end, weight_title=1, weight_first_paragraph=1)
    df = months_columns(df)
    df = link_to_site_name(df)
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
    sentiment(important_1, weights=weights, gram_dirs=grams, assets_dir=assets, res_dir=res, ngram=1, ngram_compare=2)
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