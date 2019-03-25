from common_scraping import sleep_r, full_driver, csv_dir_common
import selenium
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
import numpy as np

link = 'https://spectrum.ieee.org/blog/'
driver = full_driver()
driver.get(link)

def topics_links():
    # find links to categories (BIZ & IT, TECH etc.)
    topics_a = driver.find_element_by_xpath('//ul[@class="cols active blogs"]').find_element_by_class_name('sort-links').find_elements_by_tag_name('a')
    topics_href = []

    for i in topics_a:
        if i.get_attribute('href') not in [link+'Newsletter', link+'Top-Stories']:
            # specification says these categories are unnecessary
            # FORUMS would also break the code
            topics_href.append(i.get_attribute('href'))
            # append already clean links

    return topics_href


def categories_links(time_border, arts, category):
    stop_categories = False
    article_category = category.split('/')[-1]
    try:
        driver.execute_script('splashpage.closeit()')
    except:
        pass
    try:
        driver.find_element_by_class_name('cc-compliance').click()
        sleep_r('l')
    except:
        print('no cc compliance')
        pass

    articles_all = driver.find_element_by_class_name('topic-wrap').find_elements_by_tag_name('article')

    for article in articles_all:
        
        try:
            article_link = article.find_element_by_tag_name('a').get_attribute('href')
        except NoSuchElementException:
            print(article.text, 'no link')
            continue
        article_title = article.find_element_by_tag_name('h3').text  # 2a
        try:
            article_author = article.find_element_by_class_name('author-name').text  # 2c
        except:
            article_author = np.nan
        try:
            date = article.find_element_by_tag_name('label').text
        except:
            try:
                date = article.find_element_by_tag_name('time').text
            except:
                date = np.nan

        if len(str(date)) > 10:
            article_date = pd.to_datetime(date[:11])
        elif len(str(date)) < 10 and len(str(date)) > 4:
            date = yr + str(date)
            article_date = pd.to_datetime(date, format="%Y %d %b")
        else:
            article_date = pd.to_datetime('2100-01-01')

        arts.append({'link': article_link,
                     'category': article_category,
                     'title_outside': article_title,  # 2a
                     'author_outside': article_author,  # 2c
                     'date_outside': article_date  # 2d
                     })

        if article_date < time_border:
            stop_categories = True

    if not stop_categories:
        sleep_r('m')
        WebDriverWait(driver, 100).until(lambda driver: driver.find_element_by_id('blog-load-more'))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep_r('s')
        loadMoreButton = driver.find_element_by_id('blog-load-more')
        try:
            loadMoreButton.click()
        except Exception as e:
            print(e)
            return arts

        return categories_links(time_border=time_border, arts=arts, category=category)

    return arts


def download_articles(all_articles, time_border, csv_dir):
    for cat, df_grp in all_articles.groupby('category'):  # only one category at a time
        topic_list = []
        for i, row in df_grp.iterrows():
            link_dict = {}
            if 'newsletters-signup' not in row['link']:
                link = row['link']
                print(i, link)
            else:
                continue
            sleep_r('m')
            driver.get(link)
            sleep_r('s')

            link_dict['link'] = link

            link_dict['title'] = driver.find_element_by_class_name('article-main-title').text  # 4a
            link_dict['description'] = driver.find_element_by_class_name('article-dek').text  # 2b/4a
            link_dict['author'] = driver.find_element_by_class_name('author-name').text  # 2c
            link_dict['date'] = driver.find_element_by_tag_name('label').text

            # all_articles may contain too many articles
            # time_border is checked only with regards to page
            if pd.to_datetime(link_dict['date'][:11]) < time_border or pd.to_datetime(
                    row['date_outside']) < time_border:
                continue

            article_p_list = []
            for p in driver.find_elements_by_xpath('//div[contains(@class, "articleBody")]//p'):
                article_p_list.append(p.text)
            link_dict['text'] = '\n\n'.join(article_p_list)  # 4a

            topic_list.append(link_dict)

        articles_df_inside = pd.DataFrame(topic_list)  # converting list of dicts to DataFrame
        print(articles_df_inside.shape[0])

        # merging outside with inside
        pd.merge(df_grp, articles_df_inside, on='link', how='right').to_csv(csv_dir + 'ieee_' + cat + '.csv')


csvs = csv_dir_common()
topics = topics_links()
arts = []
yr = str(pd.to_datetime('now').year) + ' '

# remember to pass a list in for i (even if downloading a single topic), otherwise it will not work
# you may freely change the parameters in two lines below
time_limit = pd.to_datetime('now') - pd.Timedelta('190 days')  # 3
articles = []  # keep all articles in this list
for topic in topics:
    print(topic)
    driver.get(topic)

    sleep_r('m')
    articles = categories_links(time_border=time_limit, arts=articles, category=topic)

articles_df = pd.DataFrame(articles)
download_articles(articles_df, time_border=time_limit, csv_dir=csvs)
