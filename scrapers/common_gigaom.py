from common_scraping import sleep_r, full_driver, csv_dir_common
import pandas as pd
from selenium import webdriver
import pickle

link = 'https://gigaom.com/topics/'
driver = full_driver()
driver.get(link)


def topics_links():
    # find links to categories (BIZ & IT, TECH etc.)
    tags = driver.find_element_by_id('topics-nav').find_elements_by_tag_name('li')

    topics_href = []
    for i in tags:
        topics_href.append(i.find_element_by_tag_name('a').get_attribute('href'))

        # append already clean links

    return topics_href


def categories_links(time_border, arts, category):
    any_in = False
    print('---')
    article_category = category.split('/')[-2]
    articles_all = driver.find_elements_by_xpath('//article[not(contains(@class, "sub-post"))]')
    for article in articles_all:
        article_link = article.find_element_by_tag_name('a').get_attribute('href')
        article_title = article.find_element_by_class_name('entry-title').text
        try:
            article_author = article.find_element_by_class_name('article-header').find_element_by_css_selector(
                '.author').text
        except:
            article_author = "NaN"
        try:
            article_date = article.find_element_by_class_name('article-header').find_element_by_tag_name('time').text
            article_date = pd.to_datetime(article_date)
        except:
            article_date = "NaN"
        print(article_date)
        try:
            # sponsor=article.find_element_by_class_name('article-header').find_element_by_class_name('sponsored-by ').find_element_by_tag_name('a').get_attribute('href')
            sponsored_div = article.find_elements_by_xpath('./header/div[contains(@class, "sponsored-by")]//a')
            article_sponsor = ''
            if len(sponsored_div) > 0:
                article_sponsor = sponsored_div[0].get_attribute('href')

        except:
            sponsor = "NaN"

        if article_date == 'NaN' or article_date > time_border:
            any_in = True

            arts.append({'link': article_link,
                         'title_outside': article_title,
                         'author_outside': article_author,
                         'date_outside': article_date,
                         'sponsor_outside': article_sponsor,
                         'category': article_category}
                        )
        else:
            return arts

    if not any_in:
        return arts
    else:
        sleep_r('m')
        next_page = driver.find_element_by_class_name('page-numbers').find_element_by_class_name('next').get_attribute(
            'href')
        driver.get(next_page)
        return categories_links(time_border=time_border, arts=arts, category=category)


def download_articles(all_articles, time_border, csv_dir):
    for cat, df_grp in all_articles.groupby('category'):
        topic_list = []
        for i, row in df_grp.iterrows():
            link_dict = {}
            link = row['link']
            print(i, link)
            sleep_r('m')
            driver.get(link)
            sleep_r('s')

            link_dict['link'] = link
            link_dict['title'] = link_dict['title'] = driver.find_element_by_id(
                'inner-content').find_element_by_tag_name('h1').text
            try:
                link_dict['author'] = driver.find_element_by_class_name('article-header').find_element_by_css_selector(
                    '.author').text
            except:
                link_dict['author'] = "NaN"
            try:
                link_dict['date'] = driver.find_element_by_class_name('entry-time').text
            except:
                link_dict['date'] = "NaN"

            # if pd.to_datetime(link_dict['date']) < time_border:
            # continue

            ## It may contain sponsor information at the beginning
            article_p_list = []
            for p in driver.find_element_by_id('main').find_element_by_class_name(
                    'entry-content').find_elements_by_tag_name('p'):
                article_p_list.append(p.text)
                link_dict['text'] = '\n\n'.join(article_p_list)

            topic_list.append(link_dict)

        articles_df_inside = pd.DataFrame(topic_list)
        print(articles_df_inside.shape[0])

        df_all = pd.merge(df, articles_df_inside, on='link', how='right')
        pd.merge(df, articles_df_inside, on='link', how='right').to_csv(csv_dir + 'gigaom_' + cat + '.csv')


topics = topics_links()
arts = []
time_border = pd.to_datetime('now') - pd.Timedelta('190 days')

for topic in topics:
    print(topic)
    driver.get(topic)
    categories_links(time_border=time_border, arts=arts, category=topic)

df = pd.DataFrame(arts)
df = df.drop_duplicates('link', keep='first')

download_articles(df, time_border, csv_dir_common())
