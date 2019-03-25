from common_scraping import sleep_r, full_driver, csv_dir_common
import selenium
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
import numpy as np

link = 'https://www.theregister.co.uk/'
driver = full_driver()
driver.get(link)

def topics_links():
    # find links to categories (BIZ & IT, TECH etc.)
    topics_a = driver.find_element_by_id('top_nav').find_elements_by_tag_name('a')
    topics_href = []

    for i in topics_a:
        if i.get_attribute('href') not in [link, link+'lectures/', 'https://search.theregister.co.uk/']:
            # specification says these categories are unnecessary
            # FORUMS would also break the code
            topics_href.append(i.get_attribute('href'))
            # append already clean links

    return topics_href


def categories_links(time_border, arts, category):
    stop_categories = False
    article_category = category.split('/')[-2]
    print('category', article_category)
#     articles_all = driver.find_element_by_class_name('headlines').find_elements_by_class_name('story_link')
    articles_all = driver.find_elements_by_xpath('//div[contains(@class, "rt-1")]/article')
    if len(articles_all) == 0:
        articles_all = driver.find_elements_by_xpath('//div[contains(@class, "rt-")]/article')
#         articles_all = driver.find_elements_by_xpath('//div[contains(@class, "one_story")]')

    for article in articles_all:
        article_link = article.get_attribute('href')
        if article_link is None:
            article_link = article.find_element_by_xpath('./a').get_attribute('href')

        try:
            article_title = article.find_element_by_tag_name('h4').text  # 2a
        except:
            article_title = article.find_element_by_tag_name('h3').text

        article_abstract = article.find_element_by_class_name('standfirst').text  # 2b

        try:
            date = article.find_element_by_class_name('time_stamp').get_attribute('data-epoch')
        except:
            date = np.nan

        article_date = pd.to_datetime(date, unit='s')
        print(date, article_date, article_link)
        arts.append({'link': article_link,
                     'category': article_category,
                     'title_outside': article_title,  # 2a
                     'abstract_outside': article_abstract,
                     'date_outside': article_date  # 2d
                     })

        if article_date < time_border:
            stop_categories = True

    if not stop_categories:
        sleep_r('m')
        try:
            next_page = driver.find_element_by_xpath('//div[contains(@class, "more_content")]//a')
            driver.get(next_page.get_attribute('href'))
        except NoSuchElementException:
            next_page = driver.find_element_by_class_name('earlier_pages').find_elements_by_tag_name('a')
            driver.get(next_page[-1].get_attribute('href'))
        except Exception as e:
            print(e)
            return arts

        return categories_links(time_border=time_border, arts=arts, category=category)

    return arts


def download_articles(all_articles, time_border, csv_dir):
    for cat, df_grp in all_articles.groupby('category'):  # only one category at a time
        print(cat, df_grp.shape)
        topic_list = []
        for i, row in df_grp.iterrows():
            link_dict = {}
            link = row['link']
            if row['link'] != None:
                link = row['link']
            else:
                print('no', link)
                continue
            print(i, link)
            sleep_r('m')
            driver.get(link)
            sleep_r('s')

            link_dict['link'] = link
            link_dict['title'] = driver.find_element_by_class_name('article_head').find_element_by_tag_name(
                'h1').text  # 4a
            link_dict['description'] = driver.find_element_by_class_name('article_head').find_element_by_tag_name(
                'h2').text  # 2b/4a
            link_dict['author'] = driver.find_element_by_class_name('byline').find_element_by_tag_name('a').text
            link_dict['date'] = driver.find_element_by_class_name('dateline').text

            # all_articles may contain too many articles
            # time_border is checked only with regards to page
            print(pd.to_datetime(link_dict['date']), pd.to_datetime(row['date_outside']), time_border)
            if pd.to_datetime(link_dict['date']) < time_border or pd.to_datetime(row['date_outside']) < time_border:
                continue

            article_p_list = []
            for p in driver.find_element_by_id('body').find_elements_by_tag_name('p'):
                article_p_list.append(p.text)
            link_dict['text'] = '\n\n'.join(article_p_list)  # 4a

            topic_list.append(link_dict)

        articles_df_inside = pd.DataFrame(topic_list)  # converting list of dicts to DataFrame
        print(articles_df_inside.shape[0])

        # merging outside with inside
        pd.merge(df_grp, articles_df_inside, on='link', how='right').to_csv(csv_dir + 'register_' + cat + '.csv')


csvs = csv_dir_common()
topics = topics_links()
arts = []

# remember to pass a list in for i (even if downloading a single topic), otherwise it will not work
# you may freely change the parameters in two lines below
time_limit = pd.to_datetime('now') - pd.Timedelta('190 days')  # 3
articles = []  # keep all articles in this list
print(topics, topics[6:])
for topic in topics[6:]:
    print(topic)
    driver.get(topic)

    sleep_r('m')
    articles = categories_links(time_border=time_limit, arts=articles, category=topic)

    articles_df = pd.DataFrame(articles)
    download_articles(articles_df, time_border=time_limit, csv_dir=csvs)
