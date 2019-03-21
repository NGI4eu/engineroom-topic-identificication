# Guide to reproducing results

## Requirements

This guide assumes you have Python 3 installed with all the required packages. We suggest using [Anaconda](https://www.anaconda.com) to keep things organized and simple. Basic knowledge of Python and pandas will also be helpful, but transforming data into default format does not require it.

Required packages:
* pandas
* numpy
* NLTK
* scikit-learn
* vaderSentiment

## Data

We suggest to maintain the same data structure and column names. It is not required and may be changed later (by passing different parameters to functions), but it will make things easier. From now on we assume default column names.

You may split the dataset into as many or as few files as you like. All articles are required to have a text column, title column, date column and link column. Links are not required to be exact links, they may be just names of sources, they just would not be transformed this way. Unless specified otherwise in initial_transform() parameters, there should exist another column with \_outside suffix (apart from text) which is used to fill NA values in the main column, in case anything goes wrong. Dates do not have to be in a consistent format – even single files may contain multiple date formats, as long as they are unambiguous for pandas to_datetime().

For every source, in each month there has to be at least one article. If there is zero, you should either aggregate sources or introduce modifications to month_columns function – to aggregate by e.g. year-quarter. Most likely aggregating sources is the right solution – a very small source with a disproportionately high weight could affect results significantly.

## Definitions

### Weights
Including multiple sources in your analysis may require different weights to be set. For example, if a source is influential, but has a low number of articles, in an equal-weight analysis it would be irrelevant for the results, which may be undesirable. Setting weights helps to equalize the importance of sources. Weights are defined in the weights variable at the beginning of the file. Their sum must be 1, otherwise the program throws an exception.

### Dates
Date limits are defined in analysis_begin and analysis_end. analysis_begin is inclusive and analysis_end is exclusive (just like Python range). You can use any date format you want which pandas to_datetime understands, YYYY-MM-DD or DD Month YYYY are suggested.

### Directories
res, assets and grams are directories to save results, data and modified articles respectively in. res and assets are strings, grams requires a dictionary with two keys: 1 (words) and 2 (bigrams). If you decide to analyse only words, you do not have to define key-value pair for key=2, but remember to modify further functions accordingly.

### Words
important_1 and important_2 are lists of words and bigrams (respectively) for which co-occurrences will be computed. The longer the lists are, the more time the computation will take, so be careful in large datasets. sentiment_words and sentiment_bigrams are chosen to compute sentiment values, by default they are the same as terms for co-occurrences, but they are not required to be.

## Execute code

The pipeline must be run in this order, but not necessarily in full. If you decide to modify co-occurring words, you must run sentiments afterwards, because sentiments function uses results from co_occurrence. However, you do not need to run prepare, concat and regression.

### prepare()
The prepare() function's dfs variable takes all the files in a required format. dfs is a list of DataFrames, obviously you can use whatever form of passing dataframes you prefer, reading .csv files is a possibleoption. You can choose weights of title and first paragraph in initial_transform() functions. You need to define 'site' column, either by using link_to_site_name function or defining same site for everything, e.g. df['site'] = 'news'. Keep in mind that the names must be the same as keys in weights. Other functions inside prepare should not be changed.

### concat() and regression()
These functions concatenate files and compute ordinary least squares regression. They are required to run before further steps and crucial, as regression creates files with trending words. After regression is computed, you may likely start analysing results – and choose the list of interesting terms for co_occurrence and sentiments.

### co_occurrence()
The cooc() function run within co_occurrence() takes lists of words, as well as numbers defining n for ngrams (in rows and columns of resulting files). In the example file, ngram and words are variables to be used in columns, as we are interested in sorting them to see the top co-occurring words in any spreadsheet software.

### sentiments()
The sentiments() functions compute sentiments for a pre-defined list of words. Pairs of n-grams (ngram and ngram_compare) are independent of each other and you may run them in any order. Sentiments computation is rather slow, because paragraphs need to be modified in order to remove terms from them – a seemingly negative word in positive context will have assigned high sentiment score.

To run the full or partial analysis, you just need to execute the file with appropriate functions called.

---

## Appendix: functions

Modifications of underlying functions are also possible, here we show two typical changes which would require code modifications and are not parametrized to keep things simple for default use cases.

### Different link to site name conversions
Usually, the first replace line works as intended. However, sometimes one source may have various domains. In this case, you should use apply method with a function (conditionals in lambda are used) on the site_column that modifies all links to the desired site name. For the set of chosen sources the modifications join all the sites from the Techforge and Gizmodo family to one (as they are rather specialized and a single site skips multiple topics).

### Text transformations
Default stemming method is SnowballStemmer, but it can be replaced with any function with .stem method. Rembember to choose the proper language for SnowballStemmer.
