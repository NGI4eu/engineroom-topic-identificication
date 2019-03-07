from common_scraping import sleep_r, full_driver, csv_dir_common
import pandas as pd

site = 'https://www.blockchaintechnology-news.com'

driver = full_driver()
driver.get(site)

def topics_links():
    # find links to categories (BIZ & IT, TECH etc.)
    topics_a = driver.find_elements_by_xpath('''//ul[@class="sub-menu"]/li[contains(@class,
                                             "menu-item-object-category")]/a''')
    topics_href = []

    for i in list(set(topics_a)):
        if '/category/' in i.get_attribute('href'):
            topics_href.append(i.get_attribute('href'))

    # topic numbers, if you want to choose only some
    for i, topic in enumerate(list(set(topics_href))):
        print(i, topic)

    return topics_href


def article_links(art_df, category='//'):
    article_category = category.split('/')[-2]

    articles_top = driver.find_elements_by_xpath('//div[contains(@class,"feat-wide5-main")]')
    for article in articles_top:
        article_link = article.find_element_by_xpath('./a').get_attribute('href')

        # 2a
        article_title = article.find_element_by_xpath('./a').text

        art_df.append({'link': article_link,
                       'category': article_category,
                       'title_outside': article_title,  # 2a
                       'abstract_outside': '',  # 2b
                       }
                      )

    articles = driver.find_elements_by_xpath('//ul[contains(@class,"archive-list")]/li[@class="infinite-post"]')
    for article in articles:
        article_link = article.find_element_by_xpath('./a').get_attribute('href')

        # 2a
        article_title = article.find_element_by_xpath('./a/div/div/div/h2').text

        # 2b
        article_abstract = article.find_element_by_xpath('./a/div/div/div/p').text

        art_df.append({'link': article_link,
                       'category': article_category,
                       'title_outside': article_title,  # 2a
                       'abstract_outside': article_abstract,  # 2b
                       }
                      )
    print(len(art_df))
    return art_df


def download_articles(articles_df, time_border, csv_dir):
    for cat, df_grp in articles_df.groupby('category'):  # only one category at a time
        topic_list = []
        for i, row in df_grp.iterrows():

            link_dict = {}
            link = row['link']
            print(i, link)

            sleep_r('m')
            driver.get(link)
            sleep_r('s')

            link_dict['link'] = link

            link_dict['title'] = driver.find_element_by_xpath('//header/h1').text
            link_dict['author'] = driver.find_element_by_xpath('//span[@itemprop="name"]').text
            link_dict['date'] = driver.find_element_by_xpath('//time[@itemprop="datePublished"]').get_attribute(
                'datetime')

            # here time_border necessary, no date on the outside
            if pd.to_datetime(link_dict['date']) < time_border:
                continue

            # 4a
            article_p_list = []
            for p in driver.find_elements_by_xpath('//div[@id="content-main"]//p'):
                article_p_list.append(p.text)
            link_dict['text'] = '\n\n'.join(article_p_list)

            topic_list.append(link_dict)

        articles_df_inside = pd.DataFrame(topic_list)  # converting list of dicts to dataframe
        print(articles_df_inside.shape[0])

        # merging outside with inside
        if articles_df_inside.shape[0] != 0:  # it may happen that articles_df_inside is empty
            pd.merge(df_grp, articles_df_inside, on='link', how='right').to_csv(
                csv_dir + 'techforge_blockchain_' + cat + '.csv')


articles_df = []  # keep all articles in this list

## [:2] - default first two topics
## remember to pass a list in for i in topics[begin:end], otherwise it will not work
## you may freely change the parameters in two lines below
time_border = pd.to_datetime('now') - pd.Timedelta('190 days')  # 3
topics = list(set(topics_links()))
for i in topics:
    print(i)
    driver.get(i)
    stop = False

    while True:
        sleep_r('m')
        inf_more = driver.find_element_by_xpath('//a[@class="inf-more-but"]')
        if 'display: none' in inf_more.get_attribute('style'):
            break
        else:
            driver.execute_script('arguments[0].click();', inf_more)
            sleep_r('m')

    articles_df = article_links(art_df=articles_df, category=i)

articles_df = pd.DataFrame(articles_df)  # finally convert to dataframe

download_articles(articles_df, time_border, csv_dir_common())
