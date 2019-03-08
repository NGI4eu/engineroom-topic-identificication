import pandas as pd
import numpy as np
import pickle
from datetime import datetime
from collections import Counter, defaultdict
from ast import literal_eval
import string
import gc
import os
from nltk import FreqDist  # frequency distribution
from nltk.tokenize import sent_tokenize  # fast tokenize
from nltk.tokenize. treebank import TreebankWordTokenizer, TreebankWordDetokenizer
from nltk.stem import SnowballStemmer  # stemming
from sklearn import linear_model  # OLS
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # sentiment analysis


def make_directory(dir_name):
    os.system('mkdir -p ' + dir_name)


def flatten(l):
    return [item for sublist in l for item in sublist]


def initial_transform(df, date_start, date_end, text_column='text', date_columns=('date', 'date_outside'),
                      title_columns=('title', 'title_outside'), links_column='link',
                      weight_title=1, weight_first_paragraph=1):
    """ Transform scraped data by dropping duplicates and cleaning dates.
    Initial transformation required because scraped data is quite messy.

    :param df: scraped data
    :type df: DataFrame
    :param date_start: date understandable to pd.to_datetime, preferably YYYY-MM-DD
    :type date_start: string
    :param date_end: see above
    :type date_end: string
    :param text_column: column with texts, drop duplicates based on it
    :type text_column: string
    :param date_columns: list, columns with dates. If length > 1, fillna first column with next.
    :type date_columns: list
    :param title_columns: list, columns with titles, see above
    :type title_columns: list
    :return: transformed scraped data
    :rtype: DataFrame
    """
    df.drop_duplicates(subset=[text_column], inplace=True)
    if len(date_columns) > 1:
        for column in date_columns[1:]:
            df[date_columns[0]].fillna(df[column], inplace=True)
    if len(title_columns) > 1:
        for column in title_columns[1:]:
            df[title_columns[0]].fillna(df[column], inplace=True)
    df[date_columns[0]] = df[date_columns[0]].apply(
        lambda x: str(x).replace(' p.m.', '').replace('BUSINESS NEWS', '').split(' | ')[0])
    for i, row in df.iterrows():
        print(row[date_columns[0]], row['link'])
        pd.to_datetime(row[date_columns[0]])
    df[date_columns[0]] = df[date_columns[0]].apply(lambda x: pd.to_datetime(x))
    df[text_column] = df.apply(lambda row: '\n\n'.join(weight_title*[str(
        row[title_columns[0]])]) + '\n\n' + '\n\n'.join(weight_first_paragraph*[str(
        row[text_column]).split('\n\n')[0]]) + '\n\n' + '\n\n'.join(str(
        row[text_column]).split('\n\n')[1:]),
                               axis=1)
    print('pre-drop', df.shape)
    df = df.loc[
        (df[date_columns[0]] >= pd.to_datetime(date_start)) &
        (df[date_columns[0]] < pd.to_datetime(date_end))]
    print('post-drop', df.shape)
    return df


def link_to_site_name(df, links_column='link', site_column='site'):
    """DataFrame contains a column with links, transform it to site name"""
    df[site_column] = df[links_column]
    df[site_column] = df[site_column].str.replace('://(www\.)?', '').str.replace('https|http', '').str.split(
        '\.com|\.net|\.eu').apply(lambda x: x[0])
    df[site_column] = df[site_column].apply(lambda x: x.split('.')[1] if '.gizmodo' in x else x)
    df[site_column] = df[site_column].apply(lambda x: 'ieee' if 'spectrum.ieee.org' in x else x)
    df[site_column] = df[site_column].apply(lambda x: 'register' if (
            x == 'theregister' or 'theregister.co.uk/' in x) else x)
    df[site_column] = df[site_column].apply(
        lambda x: 'techforge' if x[-4:] == 'news' or x[-4:] == '-cio' or x[-5:] == '-tech' else x)
    print(df[site_column].value_counts())
    return df


def months_columns(df, date_time_column='date', create_period_column='year_month'):
    """Sort dataframe by date_time_column and create a column with periods (months, assuming YYYY-MM-DD)"""
    df[create_period_column] = df[date_time_column].astype(str).str[0:7]
    df.sort_values(date_time_column, inplace=True)
    return df


def save_months(df, assets_dir, periods_filename='months.pickle', period_column='year_month'):
    """Create file with list of months."""
    all_months = df[period_column].unique()
    all_months = all_months[~pd.isnull(all_months)]
    pickle.dump(all_months, open(assets_dir + periods_filename, 'wb'))


def to_bigram(x):
    return [[' '.join(y) for y in
            list(zip(z, z[1:]))]
            for z in x]


def transform_texts(art, period, site, ngrams=1, mod=None,
                    text_column='text', text_token_column='text_token', remain_columns=('author', 'site', 'link')):
    """Transform dataframe with texts, create tokenized lists in columns.
    Save dataframe to mod directory, if mod is not None."""
    text_column_paragraphs = text_column + '_paragraphs'
    text_token_column_lower = text_token_column + '_lower'
    text_token_column_stemmed = text_token_column + '_stemmed'
    text_token_column_count = text_token_column + '_count'

    st = SnowballStemmer('english')
    art.dropna(subset=[text_column], inplace=True)  # maketrans fails if there are nans
    art_sh = art[list((text_column,) + remain_columns)].copy()  # we don't need more columns
    del art
    gc.collect()

    additional_punctuation = string.punctuation + '«»…—’‘“”–•'  # a few additional, non-ascii chars
    # gigaom
    tt = TreebankWordTokenizer()
    art_sh[text_column] = art_sh[text_column].apply(lambda x: x.replace(
        'Tweet\nShare\nPost\n', '').replace('“', '').replace('”', '').replace('’', '\''))
    # sent_tokenize tokenizes by paragraphs
    art_sh[text_column_paragraphs] = art_sh[text_column].apply(lambda x: x.split('\n\n'))
    art_sh[text_token_column] = art_sh[text_column_paragraphs].apply(
        lambda x: [flatten([tt.tokenize(z) for z in sent_tokenize(y)]) for y in x])
    # to lower, stem
    art_sh[text_token_column_lower] = art_sh[text_token_column].apply(
        lambda x: [[word.lower() for word in paragraph] for paragraph in x])
    art_sh[text_token_column_stemmed] = art_sh[text_token_column_lower].apply(
        lambda x: [[st.stem(word) for word in paragraph] for paragraph in x])
    if ngrams == 2:  # convert to bigrams
        art_sh[text_token_column] = art_sh[text_token_column_lower].apply(to_bigram)
        art_sh[text_token_column_lower] = art_sh[text_token_column_lower].apply(to_bigram)
        art_sh[text_token_column_stemmed] = art_sh[text_token_column_stemmed].apply(to_bigram)

    art_sh[text_token_column_count] = art_sh[text_token_column_stemmed].apply(lambda x: dict(
        Counter(FreqDist(flatten(x)))))

    if mod is not None:
        art_sh.to_csv(mod + 'dfs_articles' + period + site + '.csv')

    return art_sh


def most_used(art, period, site, text_token_column_count='text_token_count',
              ngrams=1, mod=None,
              text_column='text', text_token_column='text_token', remain_columns=('author', 'site', 'link')):
    """Return dict with counts, and the number of articles in a given dataframe.
    Save ngram counts to mod directory, if mod is not None.
    """
    time_start = datetime.now()
    art = transform_texts(art, period=period, site=site, ngrams=ngrams, mod=mod,
                          text_column=text_column, text_token_column=text_token_column, remain_columns=remain_columns)
    div = art.shape[0]  # number of articles

    # sum all the tokens
    all_frequencies = Counter()
    for token in art[text_token_column_count]:
        all_frequencies.update(token)

    print(datetime.now() - time_start, art.shape[0], period, site)
    del art
    gc.collect()
    return all_frequencies, div


def save_frequencies(df, gram_dirs, weights, assets_dir, res_dir, periods_filename='months.pickle'):
    """Save unweighted frequencies and counts by month for all sites"""
    months = pd.read_pickle(assets_dir + periods_filename)
    for n, gram_dir in gram_dirs.items():
        for i_month, month in enumerate(months):
            for i_site, site in enumerate(weights.keys()):  # weights contain sites as keys
                word_counter, div = most_used(df.loc[(df['year_month'] == month) & (df['site'] == site)],
                                              month, site, ngrams=n, mod=gram_dir)
                word_df = pd.DataFrame.from_dict(dict(word_counter), orient='index')

                # we need counts and frequencies
                word_df.columns = ['count_' + month + site]
                word_df['freq_' + month + site] = word_df['count_' + month + site] / div
                if i_site == 0:
                    word_dfs_all = word_df.copy()
                else:
                    word_dfs_all = word_dfs_all.join(word_df, how='outer')  # join with previous sites
                print(word_dfs_all.shape)
                del word_df
                gc.collect()
            word_dfs_all.to_csv(res_dir + 'freq_' + str(n) + '_' + month + '-all_site.csv')
            del word_dfs_all
            gc.collect()


def save_concat(gram_dirs, assets_dir, res_dir, weights, any_month_used=2, periods_filename='months.pickle'):
    """Concat weighted frequencies and unweighted counts for all sites and all months"""
    months = pd.read_pickle(assets_dir + periods_filename)
    for ngram in gram_dirs.keys():
        for i_month, month in enumerate(sorted(months, reverse=True)):
            final_columns = []
            frequency_month = pd.read_csv(res_dir + 'freq_' + str(ngram) + '_' + month + '-all_site.csv', index_col=0)
            frequency_month['freq_' + month] = 0
            frequency_month['count_' + month] = 0
            final_columns.extend(['freq_' + month, 'count_' + month])

            # sum counts and weighted frequencies
            for site in weights.keys():
                frequency_month['freq_' + month + site].fillna(0, inplace=True)
                frequency_month['count_' + month + site].fillna(0, inplace=True)
                frequency_month['freq_' + month] += frequency_month['freq_' + month + site] * weights[site]
                frequency_month['count_' + month] += frequency_month['count_' + month + site]

            if i_month == 0:
                # initial df
                final_df = frequency_month[final_columns].copy()
            elif i_month < any_month_used:
                # take only these words which occured at least once in the last any_month_used months
                final_df = final_df.join(frequency_month[final_columns], how='outer')
            else:
                # do not add further words
                final_df = final_df.join(frequency_month[final_columns], how='left')
            # there may be some empty rows, which cause problems later
            final_df = final_df.loc[final_df.index.notnull()]
            print(final_df.shape)

            del frequency_month
            gc.collect()

        final_df.to_csv(res_dir + 'freq_' + str(ngram) + '-all_site.csv')
        del final_df
        gc.collect()
        print('finished', ngram)


def stopwords_regex():
    """Return regex with stopwords."""
    stopwords = ['the', 'and', 'to', 'of', 'on', 'this', 'their', 'in', 'i', 'about', 'that', 'do', 'not', 'a', 'an',
                 'was', 'far', 'with', 'for', 'as', 'like', 'at', 'who', 'by', 'now', 'will', 'ever', 'month', 'our',
                 'such', 'so', 'can', 'if', 'have', 'run', 'you', 'we', 'they', 'or', 'where', 'had', 'than', 'are',
                 'your', 'then', 'how', 'say', 'said', 'he', 'she', 'must', 'from', 'get', 'up', 'were', 'been',
                 'tell', 'told', 'out', 'need', 'his', 'her', 'which', 'dont', 'no', 'but', 's', 'make', 'is', 'has',
                 'more', 'use', 'know', 'thing', 'those', 'becaus', 'there', 'may', 'through', 'be', 'when', 'happen',
                 'take', 'could', 'one', 'two', 'three',
                 '\'s', '\.', '\,', 'whi', 'it', '\[', '\]', '\&', 'mani', '\$', 'what', '\?', '\(', '\)', '\:', '–',
                 'n\'t', 'doe', '‘', '•', '\!', '\@', '\'', '\;'
                 ]
    return '^' + ' |^'.join(stopwords) + ' | ' + '$| '.join(stopwords) + '$'


def reg(gram_dirs, assets_dir, res_dir, regression_periods_length=('', 12, 6, 3), periods_filename='months.pickle'):
    """Save regression coefficients to file"""
    periods = pd.read_pickle(assets_dir + periods_filename)
    regression = linear_model.LinearRegression()
    stopwords_re = stopwords_regex()
    for ngram in gram_dirs.keys():
        for regression_length in regression_periods_length:
            print(regression_length)
            df = pd.read_csv(res_dir + 'freq_' + str(ngram) + '-all_site.csv', index_col=0)
            df = df[[x for x in df.columns if 'count' not in x]]
            df = df.transpose()  # nice table, easier to manipulate, but requires a lot of memory
            word_list = df.columns  # list of words in columns due to transpose
            df['_period_'] = [str(x) for x in range(len(periods), 0, -1)]  # how many months
            if type(regression_length) == int:
                df = df.loc[df['_period_'].astype(int) > len(periods) - regression_length]
            df.fillna(0, inplace=True)  # regression doesn't work with nans, replace with 0
            coef_normalized, coef_normalized_max, coef = dict(), dict(), dict()

            # regression for every relevant word
            time_old = datetime.now()
            for i_word, word in enumerate(word_list):
                if i_word % 1000 == 0:
                    print(i_word, len(word_list), datetime.now() - time_old)  # progress
                    time_old = datetime.now()
                regression.fit(df.loc[:, '_period_'].values.reshape(-1, 1), df.loc[:, word].values.reshape(-1, 1))
                coef_normalized[word] = regression.coef_[0][0] / df[word].mean()
                coef_normalized_max[word] = regression.coef_[0][0] / df[word].max()
                coef[word] = regression.coef_[0][0]

            df = df.transpose()  # transpose back, words from columns to indices

            df['coef_norm'], df['coef_norm_max'], df['coef'] = \
                pd.Series(coef_normalized), pd.Series(coef_normalized_max), pd.Series(coef)
            if ngram == 2:  # clean a bit, drop most stopwords
                df = df.loc[~(df.index.str.contains(stopwords_re))]

            df.sort_values('coef', ascending=False).to_csv(
                res_dir + 'coefs_' + str(ngram) + 'weighted_site' + str(regression_length) + '.csv')


def words_with_means(df, most_significant):
    """Create dictionary, where keys are words and values are average frequencies"""
    row_words_means = {}
    # n most significant ngrams
    for i, row in df[:most_significant].iterrows():
        row_words_means[i] = np.mean(row[[x for x in df.columns if 'freq' in x]])
    return row_words_means


def read_articles(month, site, ngram, gram_dirs, ac, text_token_count_column='text_token_count', cooc_use=True):
    """Read given articles and rename column to format required by cooc() if cooc_use"""
    df_art = pd.read_csv(gram_dirs[ngram] + 'dfs_articles' + month + site + '.csv')
    if cooc_use:
        df_art[text_token_count_column] = df_art[
            text_token_count_column].apply(lambda x: defaultdict(lambda: 0, literal_eval(x)))
    df_art.rename(columns={text_token_count_column: text_token_count_column + ac}, inplace=True)

    return df_art


def read_both_ngram_articles(month, site, ngram_art, ngram_compare, gram_dirs,
                             text_token_count_column='text_token_count'):
    """Run read_articles function for both base and compare ngrams"""
    df = read_articles(month, site, ngram_art, gram_dirs, ac='_art', text_token_count_column=text_token_count_column)
    df_compare = read_articles(
        month, site, ngram_compare, gram_dirs, ac='_compare', text_token_count_column=text_token_count_column)

    return df, df_compare


def count_words(words, site, df, row_words_means, article_word_count):
    """Count how many words (and how often) exist in articles on a site"""
    cooc_words = {}

    for word in words:
        cooc_words[word + '_count_' + site] = defaultdict(lambda: 0)
        cooc_words[word + '_bool_' + site] = defaultdict(lambda: 0)
        column_word_count = df['text_token_count_art'].apply(lambda x: x[word])
        article_word_count[word][site]['_count_'] += sum(column_word_count)
        column_word_bool = column_word_count.apply(bool)
        article_word_count[word][site]['_bool_'] += sum(column_word_bool)

        df_word_exists = df.loc[column_word_count > 0]
        if not df_word_exists.empty:
            counts = Counter()
            bools = Counter()
            for d in df_word_exists['text_token_count_compare'].values:
                counts.update(d)
                bools.update({k: 1 for k, _ in d.items()})
            for row_word in row_words_means.keys():
                # row_word_count = df_word_exists['text_token_count_compare'].apply(lambda x: x[row_word])
                cooc_words[word + '_count_' + site][row_word] = counts[row_word]
                cooc_words[word + '_bool_' + site][row_word] = bools[row_word]

        # print(word, {k: v for k, v in cooc_words[word + '_count_' + site].items() if v > 0},
        #       {k: v for k, v in article_word_count[word][site].items() if v > 0})
    return cooc_words, article_word_count


def create_word_count(words, sites):
    """Create dictionary with booleans: sum([1 if exists] else 0) and counts of words"""
    article_word_count = {}
    for word in words:
        article_word_count[word] = {site: {'_bool_': 0, '_count_': 0} for site in sites}
    return article_word_count


def normalize_by_article_count(words, cooc_words, sites, article_word_count):
    """Normalizes cooc DataFrame so that maximum bool (i.e. co-occurrence of words A and A) is 100.
    Analogous procedure is done for counts; however resulting values may be greater than 100,
    if a row-word is used more often than the column-word."""
    old_datetime = datetime.now()
    for i, word in enumerate(words):
        print('coef', word, 100*i/len(words), datetime.now() - old_datetime)
        old_datetime = datetime.now()
        for site in sites:
            for bc in ['_count_', '_bool_']:
                if word + bc + site not in cooc_words.columns:
                    continue
                print('not continued')
                if article_word_count[word][site][bc] > 0:
                    cooc_words[word + bc + site + '_freq'] = 100 * cooc_words[
                        word + bc + site] / article_word_count[word][site][bc]
                else:
                    cooc_words[word + bc + site + '_freq'] = 0
                print(word, cooc_words[word + bc + site + '_freq'] )
    return cooc_words


def normalize_by_weights(words, cooc_all, weights, row_words_means):
    """Return DataFrame with six additional coefficients:
    frequency, frequency normalized by mean, frequency normalized by root of mean
    both for booleans and counts"""
    old_datetime = datetime.now()
    for i, word in enumerate(words):
        print('count/bool', word, 100 * i / len(words), datetime.now() - old_datetime)
        old_datetime = datetime.now()
        for bc in ['_count_', '_bool_']:
            cooc_all[word + bc + 'freq_weighted'] = 0
            cooc_all[word + bc + 'freq_weighted_normalized'] = 0
            cooc_all[word + bc + 'freq_weighted_normalized_root'] = 0
            for site in weights.keys():
                if word + bc + site + '_freq' in cooc_all.columns:  # avoid KeyErrors
                    cooc_all[word + bc + 'freq_weighted'] += weights[site] * cooc_all[
                        word + bc + site + '_freq']
                    cooc_all[word + bc + 'freq_weighted_normalized'] += weights[site] * cooc_all[
                        word + bc + site + '_freq']
                    cooc_all[word + bc + 'freq_weighted_normalized_root'] += weights[site] * cooc_all[
                        word + bc + site + '_freq']
            for row_word, mean in row_words_means.items():
                cooc_all.loc[
                    row_word, word + bc + 'freq_weighted_normalized'] = cooc_all.loc[
                    row_word, word + bc + 'freq_weighted_normalized'] / mean
                cooc_all.loc[row_word, word + bc + 'freq_weighted_normalized_root'] = cooc_all.loc[
                    row_word, word + bc + 'freq_weighted_normalized_root'] / (mean ** (1/2))

    return cooc_all


def cooc(ngram, ngram_compare, words, assets_dir, gram_dirs, res_dir, weights,
         min_coef_norm=0.025, most_significant=15000, periods_filename='months.pickle',
         text_token_column='text_token_count', text_token_count_column='text_token_count'):
    """Save files with co-occurrence values"""
    months = pd.read_pickle(assets_dir + periods_filename)
    # coefficients for rows
    coefs_compare = pd.read_csv(res_dir + 'coefs_' + str(ngram_compare) + 'weighted_site.csv', index_col=0)
    coefs_compare = coefs_compare.loc[coefs_compare['coef_norm'] > min_coef_norm].sort_values('coef', ascending=False)

    row_words_means = words_with_means(coefs_compare, most_significant=most_significant)
    cooc_all = []
    article_word_count = create_word_count(words, weights.keys())
    old_datetime = datetime.now()
    for site in weights.keys():
        print(site, datetime.now() - old_datetime)
        old_datetime = datetime.now()
        cooc_months = []
        for i_month, month in enumerate(months):
            print(i_month, month)
            # take articles for columns and rows
            df_art, df_compare = read_both_ngram_articles(
                month=month, site=site, ngram_art=ngram, ngram_compare=ngram_compare, gram_dirs=gram_dirs,
                text_token_count_column=text_token_count_column)

            df_tmp = pd.concat([df_art[['site', text_token_column + '_art']],
                                df_compare[[text_token_column + '_compare']]], axis=1)
            # if i_month == 0:
            #     df = df_tmp.copy()
            # else:
            #     df = pd.concat([df, df_tmp], axis=0)
            cooc_site, article_word_count = count_words(words, site, df_tmp, row_words_means, article_word_count)

            cooc_months.append(cooc_site)

            del df_art, df_compare, df_tmp
            gc.collect()

        cooc_site = defaultdict(lambda: defaultdict(lambda: 0))
        for cooc_month in cooc_months:
            for k, v in cooc_month.items():
                for k1, v1 in v.items():
                    cooc_site[k][k1] += v1

        cooc_all.append(pd.DataFrame.from_dict(cooc_site))

    cooc_all = pd.concat(cooc_all, axis=1)
    cooc_all = normalize_by_article_count(words, cooc_all, weights.keys(), article_word_count)
    cooc_all = normalize_by_weights(words, cooc_all, weights, row_words_means)

    cooc_all[[x for x in cooc_all.columns if 'weighted' in x]].to_csv(
        res_dir + 'cooc' + str(ngram) + str(ngram_compare) + 'weighted.csv')


def comparison_cooc(res_dir, ngram, ngram_compare, n=100):
    """Get dictionary with n most commonly co-occurring stemmed words for a given word."""
    cooc_words = defaultdict(lambda: [])
    cooc_data = pd.read_csv(res_dir + 'cooc' + str(ngram) + str(ngram_compare) + 'weighted.csv', index_col=0)
    for i in cooc_data.columns:
        if 'count_freq_weighted' in i and '_normalized' not in i:
            column_term = i.split('_')[0]
            row_terms = cooc_data[i].sort_values(ascending=False).index[:n].tolist()
            cooc_words[column_term] = row_terms
    return cooc_words


def sentiment(terms, weights, gram_dirs, assets_dir, res_dir, periods_filename='months.pickle', k=50,
              text_token_column='text_token', text_column='text', ngram=1, ngram_compare=1):
    months = pd.read_pickle(assets_dir + periods_filename)
    d = TreebankWordDetokenizer()
    print(terms)
    articles_months = {}
    comparison = comparison_cooc(res_dir, ngram, ngram_compare)
    print(comparison)
    # for month in months:
    #     print(month)
    #     for site in weights.keys():
    #         df_original = read_articles(month, site, 1, gram_dirs, ac='', cooc_use=False)
    #         df = read_articles(month, site, ngram, gram_dirs, ac='', cooc_use=False)
    #         df_compare = read_articles(month, site, ngram_compare, gram_dirs, ac='', cooc_use=False)
    #         texts = list(zip(df[text_token_column + '_stemmed'].tolist(),
    #                          df_compare[text_token_column + '_stemmed'].tolist(),
    #                          df[text_token_column + '_stemmed'].apply(lambda x: set(
    #                              terms) & set(flatten(literal_eval(x)))),
    #                          df_original[text_token_column].tolist()))
    #         texts = [x for x in texts if x[-1]]  # get rid of articles not containing any term
    #         if month in articles_months.keys():
    #             articles_months[month].extend(texts)
    #         else:
    #             articles_months[month] = texts
    #     print(articles_months[month][0])

    analyzer = SentimentIntensityAnalyzer()
    additional_punctuation = string.punctuation + '«»…—’‘“”–•'  # a few additional, non-ascii chars
    all_scores = {}
    all_words = defaultdict(lambda: defaultdict(lambda: []))
    for month in months:
        print(month)

        articles_months = []
        for site in weights.keys():
            df_original = read_articles(month, site, 1, gram_dirs, ac='', cooc_use=False)
            df = read_articles(month, site, ngram, gram_dirs, ac='', cooc_use=False)
            df_compare = read_articles(month, site, ngram_compare, gram_dirs, ac='', cooc_use=False)
            texts = list(zip(df[text_token_column + '_stemmed'].tolist(),
                             df_compare[text_token_column + '_stemmed'].tolist(),
                             df[text_token_column + '_stemmed'].apply(lambda x: set(
                                 terms) & set(flatten(literal_eval(x)))),
                             df_original[text_token_column].tolist()))
            texts = [x for x in texts if x[-1]]  # get rid of articles not containing any term
            if articles_months:
                articles_months.extend(texts)
            else:
                articles_months = texts

        polarities = defaultdict(lambda: [])
        for tokens_original, tokens_compare_original, words, original_unigrams in articles_months:
            tokens_original = literal_eval(tokens_original)
            tokens_compare_original = literal_eval(tokens_compare_original)
            original_unigrams = literal_eval(original_unigrams)
            for i in range(len(tokens_original)):
                for word in words:
                    to_remove = [list(i + n for n in range(ngram)) for i, x in enumerate(
                        tokens_original[i]) if x == word]
                    tokens = list(np.delete(original_unigrams[i], to_remove))
                    sentence = d.detokenize(tokens).replace(' .', '.')
                    # print(word, sentence)
                    vs = analyzer.polarity_scores(sentence)
                    polarities[word].append(vs['compound'])
                    polarities[word + '_count'].append(1)
                    # print(polarities)
                    for token in set(flatten(tokens_compare_original)) & set(comparison[word]):
                        to_remove_compare = [list(i + n for n in range(ngram_compare)) for i, x in enumerate(
                            tokens_compare_original[i]) if x == token]
                        print(to_remove, to_remove_compare)
                        print(flatten(to_remove) + flatten(to_remove_compare))
                        tokens = list(np.delete(original_unigrams[i], flatten(to_remove) + flatten(to_remove_compare)))
                        sentence = d.detokenize(tokens).replace(' .', '.')
                        print(word, token, sentence)
                        vs = analyzer.polarity_scores(sentence)
                        all_words[word][token].append(vs['compound'])
                        all_words[word + '_count'][token].append(1)

        all_scores[month] = {k: sum(v) if k[-6:] == '_count' else v for k, v in polarities.items()}
        del articles_months[:]
        gc.collect()

    word_scores = {}
    for month, v in all_scores.items():
        for word, scores in v.items():
            if word not in word_scores.keys():
                word_scores[word] = {}
            word_scores[word][month] = np.mean(scores)
    cooc_scores = {}
    print(all_words)
    for word1, v in all_words.items():
        cooc_scores[word1] = {}
        for word2, scores in v.items():
            if word1[-6:] != '_count':
                cooc_scores[word1][word2] = np.mean(scores)
            else:
                cooc_scores[word1][word2] = np.sum(scores)

    print(cooc_scores)
    pd.DataFrame(word_scores).to_csv(res_dir + 'sentiments_mod' + str(ngram) + str(ngram_compare) + '.csv')
    pd.DataFrame(cooc_scores).to_csv(res_dir + 'sentiments_cooc_mod' + str(ngram) + str(ngram_compare) + '.csv')
