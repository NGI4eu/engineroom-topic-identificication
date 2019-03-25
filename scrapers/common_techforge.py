# todo
import pandas as pd
import re
from common_scraping import sleep_r, full_driver, csv_dir_common
from selenium.common.exceptions import NoSuchElementException


sites_previous = '''https://www.cloudcomputing-news.net/
https://www.developer-tech.com/
https://www.enterprise-cio.com/'''
sites = '''https://www.iottechnews.com/
https://www.marketingtechnews.net/'''
#http://virtualreality-news.net
#https://www.telecomstechnews.com/'''
sites = sites.split('\n')


def ornone(f):
    try:
        return f
    except NoSuchElementException:
        return ''


def tf_site(site):
    driver = full_driver()
    sleep_r('m')
    driver.get(site)

    # find links to categories (BIZ & IT, TECH etc.)
    while True:
        topics_a = driver.find_elements_by_xpath('//ul[@class="right"]/li[contains(@class,'
                                                 '"has-dropdown")]/ul[@class="dropdown"]/li/a')
        if len(topics_a) > 0:
            break
        else:
            print('no topics')
            sleep_r('m')
            driver.get(site)
            sleep_r('m')

    topics = []

    for i in topics_a:
        if '/categories/' in i.get_attribute('href'):
            # if 'cloudcomputing' in site and 'case-studies' in i.get_attribute(
            #         'href') or 'data-analytics' in i.get_attribute('href'):
            #     topics.append(i.get_attribute('href'))
            # if 'cloudcomputing' not in site:
            if 'developer' not in site:
                topics.append(i.get_attribute('href'))
            elif 'Gaming' not in i.get_attribute('href'):
                topics.append(i.get_attribute('href'))

    # topic numbers, if you want to choose only some
    for i, topic in enumerate(topics):
        print(site, i, topic)

    def article_links(time_border, art_df, category='//'):
        stop = False
        article_category = category.split('/')[-2]
        articles = driver.find_elements_by_xpath('//article')
        for article in articles:
            article_link = article.find_element_by_xpath('.//a').get_attribute('href')

            # 2a
            article_title = article.find_element_by_xpath('.//h2').text

            # 2b
            article_abstract = article.find_element_by_xpath('.//div[@class="summary"]').text

            # 2c
            article_author = article.find_element_by_xpath('./div[@class="meta_list"]/h4/a').text

            # 2d
            date = article.find_element_by_xpath('./div[@class="meta_list"]/h4').text

            date = re.search('[0-9]+\ (.+)\ [0-9]+,', date).group()[:-1]
            article_date = pd.to_datetime(date)

            # 2e
            article_number_of_comments = article.find_element_by_xpath('./div[@class="meta_list"]/h4').text.split(',')[
                -1]

            art_df.append({'link': article_link,
                           'category': article_category,
                           'title_outside': article_title,  # 2a
                           'abstract_outside': article_abstract,  # 2b
                           'author_outside': article_author,  # 2c
                           'date_outside': article_date,  # 2d
                           'comments_count_outside': article_number_of_comments}  # 2d
                          )

            if article_date < time_border:
                stop = True

        if not stop:
            sleep_r('m')
            next_page = driver.find_elements_by_xpath('//ul[@class="pagination"]/li[contains(@class, "arrow")]/a')[
                -1].get_attribute('href')

            curr_page = driver.current_url
            if curr_page == next_page:
                stop = True
                return art_df, stop
            driver.get(next_page)
            return article_links(time_border=time_border, art_df=art_df, category=category)

        return art_df, stop

    articles_df = []  # keep all articles in this list

    ## 30 days - default timelimit
    ## [:2] - default first two topics
    ## remember to pass a list in for i in topics[begin:end], otherwise it will not work
    ## you may freely change the parameters in two lines below
    timeborder = pd.to_datetime('now') - pd.Timedelta('190 days')  # 3
    print(topics)
    for i in topics:
        print(i)
        driver.get(i)
        stop = False

        while not stop:
            sleep_r('m')
            articles_df, stop = article_links(time_border=timeborder, art_df=articles_df, category=i)

    articles_df = pd.DataFrame(articles_df)  # finally convert to dataframe

    for cat, df_grp in articles_df.groupby('category'):  # only one category at a time
        print(cat, df_grp.shape)
        topic_list = []
        for i, row in df_grp.iterrows():

            link_dict = {}
            link = row['link']
            # print(i, link)

            # articles_df may contain too many articles
            # timeborder is checked only with regards to page
            # no reasonable change in speed, current solution avoids breaking a for loop
            if pd.to_datetime(row['date_outside']) < timeborder:
                continue

            sleep_r('s')
            while True:
                try:
                    driver.get(link)
                    break
                except:
                    sleep_r('l')
            sleep_r('s')

            link_dict['link'] = link

            link_dict['title'] = driver.find_element_by_xpath('//h2').text
            if len(driver.find_elements_by_xpath('//div[@class="meta"]')) > 0:
                link_dict['author'] = ornone(
                    driver.find_element_by_xpath('//div[@class="meta"]/h4/a[@rel="author"]').text)
                link_dict['date'] = ornone(driver.find_element_by_xpath('//div[@class="meta"]/h4').text.split('\n')[-2])
                # as above, but with date inside (double-check)
                # doesn't seem necessary, but doesn't make code slower
                # print(link_dict['date'], link_dict['date'].split(',')[0], pd.to_datetime(link_dict['date'].split(',')[0]))
                if pd.to_datetime(link_dict['date'].split(',')[0]) < timeborder:
                    continue
            link_dict['categories'] = ', '.join(
                [x.text for x in driver.find_elements_by_xpath('//div[@class="meta"]/a[@id="categories"]')])

            # 4a
            article_p_list = []
            for p in driver.find_elements_by_xpath('//div[@class="content"]//p'):
                article_p_list.append(p.text)
            link_dict['text'] = '\n\n'.join(article_p_list)

            topic_list.append(link_dict)

        articles_df_inside = pd.DataFrame(topic_list)  # converting list of dicts to dataframe
        print(articles_df_inside.shape[0])

        # merging outside with inside
        if articles_df_inside.shape[0] != 0:  # it may happen that articles_df_inside is empty
            pd.merge(df_grp, articles_df_inside, on='link', how='right').to_csv(csv_dir_common() +
                'techforge_' + site.split('.')[-2].replace('http://','') + '_' + cat + '.csv')


for single_site in sites:
    tf_site(site=single_site)
