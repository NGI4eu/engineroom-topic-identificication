from common_scraping import sleep_r, full_driver, csv_dir_common
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import numpy as np
import threading
import os

driver = full_driver()

driver.get('https://www.zdnet.com/topic/')


def topics_links(categories):
    pages = driver.find_elements_by_xpath('//ul[@class = "nav nav-tabs topic-nav"]/li//a')
    pages_href = []
    for page in pages:
        pages_href.append(page.get_attribute('href'))

    topics_href = []
    for page in pages_href:

        x = True

        driver.get(page)

        while x == True:

            topics_a = driver.find_elements_by_xpath('//div[@class="col-2"]/h3/a')
            for topic in topics_a:
                if topic.text in categories:
                    topics_href.append(topic.get_attribute('href'))

            try:
                x = True
                next_page = driver.find_element_by_xpath('//a[@class = "next"]')
                driver.get(next_page.get_attribute('href'))
            except:
                x = False
                continue

    topics_href = np.unique(topics_href)
    return topics_href


def articles_links(time_border, topics, arts, driver):
    for topic in topics:

        first_date = pd.to_datetime('now')
        i = 1
        while first_date > time_border:

            driver.get(topic + '/' + str(i))
            sleep_r('m')

            first_date = pd.to_datetime(
                driver.find_element_by_xpath('//article[@class = "item"]/div/div/p/span').get_attribute('data-date'))
            if first_date is None:
                first_date = pd.to_datetime('now')
            i = i + 1

            # category = driver.find_element_by_xpath('//header/h1[@itemprop = "headline"]').text
            category = topics[0].split('/')[-2]
            sleep_r('m')

            articles_all = driver.find_elements_by_xpath('//section[@id="topic-river-latest"]/div/div/div/article')
            if not len(articles_all):
                break
            elif pd.to_datetime(driver.find_element_by_xpath('//article[@class = "item"]/div/div/p/span').get_attribute(
                    'data-date')) is not None and pd.to_datetime(driver.find_element_by_xpath('//article[@class = "item"]/div/div/p/span').get_attribute(
                    'data-date')) < time_border:
                break

            else:
                for article in articles_all:

                    article_link = article.find_element_by_xpath('.//h3/a').get_attribute('href')
                    article_title = article.find_element_by_xpath('.//h3/a').text  # 2a
                    article_abstract = article.find_element_by_xpath('.//p[@class = "summary"]').text  # 2b

                    try:
                        article_author = article.find_element_by_xpath('.//p[@class="meta"]/a').text  # 2c
                    except NoSuchElementException:
                        article_author = ''

                    try:
                        date = article.find_element_by_xpath('.//p[@class="meta"]/span')
                        article_date = pd.to_datetime(date.get_attribute('data-date'))  # 2d
                    except NoSuchElementException:
                        article_date = ''

                    arts.append({'link': article_link,
                                 'category': category,
                                 'title_outside': article_title,  # 2a
                                 'abstract_outside': article_abstract  # 2b
                                    , 'author_outside': article_author,  # 2c
                                 'date_outside': article_date  # 2d
                                 }
                                )
                sleep_r('l')

    return arts


def download_articles(all_articles, csv_dir, category_name, driver):
    for i_art, art in enumerate(all_articles):
        link_dict = {}
        print(i_art, len(all_articles), category_name, art['link'])

        try:
            driver.get(art['link'])

            sleep_r('m')
            link_dict['link'] = art['link']

            try:
                link_dict['title'] = driver.find_element_by_xpath('//header/h1[@itemprop = "headline"]').text

            except NoSuchElementException:
                link_dict['title'] = ''

            try:
                link_dict['author'] = driver.find_element_by_xpath('//p/a[@itemprop="author"]').text
            except NoSuchElementException:
                link_dict['author'] = ''

            try:
                link_dict['description'] = driver.find_element_by_xpath(
                    '//header[@class="storyHeader article"]/p[@itemprop="description alternativeHeadline"]').text
            except NoSuchElementException:
                link_dict['description'] = ''

            try:
                link_dict['date'] = driver.find_element_by_xpath(
                    '//header[@class="storyHeader article"]/div/p/time').get_attribute('datetime')  # 5a
            except NoSuchElementException:
                continue

            article_p_list = []
            for p in [x.text for x in driver.find_elements_by_xpath('//article/div/p')]:
                article_p_list.append(p)

            link_dict['text'] = '\n\n'.join(article_p_list)

            art.update(link_dict)
            all_articles[i_art] = art


        except TimeoutException:
            print('timeout', art['link'])
            all_articles.append(art)
            continue

    pd.DataFrame(all_articles).to_csv(csv_dir + 'zdnet_' + category_name + '.csv')

topics_list = ['3D Printing',
 'Artificial Intelligence',
 'Banking',
 'Data Centers',
 'Data Management',
 'Developer',
 'Digital Transformation',
 'E-Commerce',
 'Enterprise Software',
 'EU',
 'Future of Work',
 'Google',
 'Government',
 'Great Debate',
 'Innovation',
 'Internet of Things',
 'IT Priorities',
 'Legal',
 'Mastering Business Analytics',
 'Networking',
 'Open Source',
 'Reimagining the Enterprise',
 'Robotics',
 'Security',
 'Smart Cities',
 'Social Enterprise',
 'Start-Ups',
 'Tech Industry',
 'Virtual Reality']
time_limit = pd.to_datetime('now') - pd.Timedelta('190 days')
csvs = csv_dir_common()
topics = topics_links(categories = topics_list)
topics = [x for x in topics if not os.path.exists(csvs + 'zdnet_' + x.split('/')[-2] + '.csv')]


def tf_site(topics_sh, driver):
    for topic in topics_sh:
        driver.get(topic)
        articles = []
        articles = articles_links(time_border=time_limit, topics=[topic], arts=articles, driver=driver)
        download_articles(all_articles=articles, csv_dir=csvs, category_name=topic.split('/')[-2], driver=driver)


class myThread (threading.Thread):
    def __init__(self, topics_sh):
        threading.Thread.__init__(self)
        self.topics_sh = topics_sh
    def run(self):
        print ("Starting ", self.topics_sh)
        driver_run = full_driver()
        tf_site(topics_sh=self.topics_sh, driver=driver_run)
        print ("Exiting ", self.topics_sh)


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


for chunk in chunks(topics, (len(topics) // 3) + 1):
    mt = myThread(topics_sh=chunk)
    mt.start()
