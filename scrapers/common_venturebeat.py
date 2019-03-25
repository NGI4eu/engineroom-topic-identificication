from common_scraping import sleep_r, full_driver, csv_dir_common
import pandas as pd
import numpy as np
from selenium.common.exceptions import TimeoutException
import os

link = 'https://venturebeat.com/'
driver = full_driver()
driver.get(link)


def topics_links():
    # find links to categories (BIZ & IT, TECH etc.)
    topics_a = driver.find_elements_by_class_name('list-item-link')
    topics_href = []

    for i in topics_a:
        if i.find_element_by_tag_name('a').get_attribute('href') not in ['mailto:partners@venturebeat.com', link+'category/games/', link+'category/pc-gaming/', link+'events/#upcoming_events', 'https://vbevents.venturebeat.com/EventSponsor/', 'https://vbevents.venturebeat.com/EventSpeaker', 'https://docs.google.com/a/venturebeat.com/forms/d/1wtWn2vpDjjVFxX5_4c4Ztv5LFiyRXlokDl-_ZOsIav8/viewform']:
            # specification says these categories are unnecessary
            # FORUMS would also break the code
            topics_href.append(i.find_element_by_tag_name('a').get_attribute('href'))
            # append already clean links

    return topics_href


def categories_links(time_border, arts, category):
    stop_categories = False
    article_category = category.split('/')[-2]
    articles_all = driver.find_element_by_class_name('skin-wrapper').find_elements_by_xpath(
        '//a[@class="article"] | //div/article')
    try:
        date = articles_all[-1].find_element_by_class_name('the-time').get_attribute('title')
    except:
        date = np.nan
    if date == np.nan:
        article_date = np.nan
    else:
        article_date = pd.to_datetime(str(date)[:11])
    if article_date < time_border:
        stop_categories = True

    if stop_categories:
        for article in articles_all:
            article_link = article.find_element_by_tag_name('a').get_attribute('href')
            article_title = article.text  # 2a
            article_date = article.find_element_by_class_name('the-time').get_attribute('title')
            print(date, article_date)
            arts.append({'link': article_link,
                         'category': article_category,
                         'title_outside': article_title,  # 2a
                         'date_outside': article_date  # 2d
                         })
        print(len(arts), article_category, category)
        return arts
    else:
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep_r('l')
            # sleep_r('m')
            driver.find_element_by_xpath('//div[@class="load-more"]/button').click()
            # driver.execute_script('arguments[0].click();', driver.find_element_by_xpath('//div[@class="load-more"]/button'))
        except Exception as e:
            print(e)

        return categories_links(time_border=time_border, arts=arts, category=category)


def download_articles(all_articles, time_border, csv_dir):
    all_articles.drop_duplicates(subset=['link'], inplace=True)
    all_links = []
    for i in os.listdir(csv_dir):
        if 'venturebeat' in i:
            all_links.extend(pd.read_csv(csv_dir + i)['link'].unique().tolist())
    for cat, df_grp in all_articles.groupby('category'):  # only one category at a time
        print(cat, df_grp.shape)
        topic_list = []
        for i, row in df_grp.iterrows():
            link_dict = {}
            if row['link'] is not None and row['link'] not in all_links:
                link = row['link']
                print(row['link'], all_links[0])
            else:
                continue
            if pd.to_datetime(row['date_outside']) < time_border:
                continue
            print(i, link)
            sleep_r('m')
            while True:
                try:
                    driver.get(link)
                    break
                except TimeoutException:
                    sleep_r('l')
            sleep_r('s')

            link_dict['link'] = link
            link_dict['title'] = driver.find_element_by_class_name('article-header').find_element_by_class_name(
                'article-title').text  # 4a
            link_dict['author'] = driver.find_element_by_xpath('//a[contains(@class, "author")]').text
            link_dict['date'] = driver.find_element_by_class_name('the-time').get_attribute('title')[:11]
            print(link_dict['date'], pd.to_datetime(link_dict['date']), row['date_outside'], time_border)
            # all_articles may contain too many articles
            # time_border is checked only with regards to page
            if pd.to_datetime(link_dict['date']) < time_border or pd.to_datetime(row['date_outside']) < time_border:
                continue

            article_p_list = []
            for p in driver.find_element_by_class_name('article-content').find_elements_by_tag_name('p'):
                article_p_list.append(p.text)
            link_dict['text'] = '\n\n'.join(article_p_list)  # 4a

            topic_list.append(link_dict)
            print(len(topic_list))
        articles_df_inside = pd.DataFrame(topic_list)  # converting list of dicts to DataFrame
        print(articles_df_inside.shape)

        # merging outside with inside
        print('save', cat)
        pd.merge(df_grp, articles_df_inside, on='link', how='right').to_csv(csv_dir + 'venturebeat_' + cat + '.csv')


csvs = csv_dir_common()
topics = topics_links()
arts = []

# remember to pass a list in for i (even if downloading a single topic), otherwise it will not work
# you may freely change the parameters in two lines below
time_limit = pd.to_datetime('now') - pd.Timedelta('190 days')  # 3
articles = []  # keep all articles in this list
print(topics)
for topic in topics:
    articles = []  # keep all articles in this list
    print(topic)
    driver.get(topic)
    print('topic', topic, 'opened')
    sleep_r('l')
    articles = categories_links(time_border=time_limit, arts=articles, category=topic)

    articles_df = pd.DataFrame(articles)
    download_articles(articles_df, time_border=time_limit, csv_dir=csvs)
