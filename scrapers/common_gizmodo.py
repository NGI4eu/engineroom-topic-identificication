from common_scraping import sleep_r, full_driver, csv_dir_common
import pandas as pd
from selenium import webdriver
import pickle

link = 'https://gizmodo.com'
driver = full_driver()
driver.get(link)


def article_links(time_border, arts):
    any_in = False
    articles = driver.find_elements_by_xpath('//section[@class="main"]//div[contains(@class, "post-wrapper")]')
    for article in articles:
        article_link = article.find_element_by_xpath('.//h1[contains(@class, "headline")]/a').get_attribute('href')
        if ('gizmodo' not in article_link) or ('io9.gizmodo' in article_link):
            continue

        article_title = article.find_element_by_xpath(
            './/h1[(contains(@class, "headline")) or (contains(@class, "title"))]').text
        try:
            article_date = article.find_element_by_xpath(
                './/div[contains(@class, "meta__container")]/time').get_attribute('datetime')
            article_date = pd.to_datetime(article_date)
        except:
            article_date = 'NaN'
        try:
            article_author = article.find_element_by_xpath('.//div[contains(@class, "author")]').text
        except:
            article_author = 'NaN'

        if article_date == 'NaN' or article_date > time_border:
            print(article_date)
            any_in = True
            arts.append({'link': article_link,
                         'title_outside': article_title,
                         'date_outside': article_date,
                         'author_outside': article_author,
                         }
                        )
        #else:
        #    return arts

    if not any_in:
        return arts

    else:
        sleep_r('m')
        next_page = driver.find_element_by_xpath('//div[@class="load-more__button"]/a').get_attribute('href')
        driver.get(next_page)
        return article_links(time_border=time_border, arts=arts)

    return arts


def download_articles(all_articles, csv_dir):
    topic_list = []
    for i_art, art in enumerate(all_articles):
        print(i_art, len(all_articles), art['link'])
        link_dict = {}
        sleep_r('s')
        link = art['link']
        driver.get(link)
        sleep_r('l')

        try:
            link_dict['link'] = link

            link_dict['title'] = driver.find_element_by_xpath('//h1').text
            try:
                link_dict['author'] = driver.find_element_by_xpath('//div[contains(@class, "author")]').text
            except:
                link_dict['author'] = 'NaN'

            link_dict['date'] = driver.find_element_by_xpath(
                '//div[contains(@class,"meta__container")]/time').get_attribute('datetime')

            article_p_list = []
            for p in [x.text for x in driver.find_elements_by_xpath('//div[contains(@class, "entry-content")]//p')]:
                article_p_list.append(p)

            link_dict['text'] = '\n\n'.join(article_p_list)
            topic_list.append(link_dict)
            # print(topic_list)
        except:
            print('problem', link)

    articles_df_inside = pd.DataFrame(topic_list)
    df = pd.DataFrame(all_articles)

    # df_all=pd.merge(df, articles_df_inside, on='link', how='right')
    pd.merge(df, articles_df_inside, on='link', how='right').to_csv(csv_dir + 'gizmodo_' + '.csv')


time_border = pd.to_datetime('now') - pd.Timedelta('190 days')
arts = []

article_links(time_border=time_border, arts=arts)
download_articles(arts, csv_dir_common())

