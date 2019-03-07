from common_scraping import sleep_r, full_driver, csv_dir_common
import pandas as pd
from selenium import webdriver
import pickle

link = 'https://theconversation.com/uk/technology/articles'
driver = full_driver()
driver.get(link)


def article_links(arts):
    articles = driver.find_elements_by_xpath('//section[contains(@class, "content-list")]/article')
    for article in articles:
        article_link = article.find_element_by_xpath('./header/div/h2/a').get_attribute('href')

        article_title = article.find_element_by_xpath('./header/div/h2').text

        article_abstract = article.find_element_by_xpath('./div[@class="content"]/span').text

        try:
            article_author = ', '.join(
                [x.text for x in article.find_elements_by_xpath('./header/div/p[@class="byline"]/span/a')])
        except NoSuchElementException:
            article_author = article.find_element_by_xpath('./header/div/p[@class="byline"]').text

        arts.append({'link': article_link,
                     'title_outside': article_title,  # 2a
                     'abstract_outside': article_abstract,  # 2b
                     'author_outside': article_author,  # 2c
                     }
                    )

    return arts


def download_articles(all_articles, time_border, df_all, csv_dir, i):
    any_in = False
    topic_list = []
    for i_art, art in enumerate(all_articles):
        print(i_art, len(all_articles), art['link'])

        link_dict = {}

        driver.get(art['link'])
        sleep_r('m')
        print(link)
        link_dict['link'] = art['link']
        link_dict['title'] = driver.find_element_by_xpath('//h1[@itemprop="name"]').text
        link_dict['author'] = driver.find_element_by_xpath('//li[@itemprop="author"]').text
        try:
            link_dict['date'] = driver.find_element_by_xpath('//time[@itemprop="datePublished"]').get_attribute(
                'datetime')
            link_dict['date'] = pd.to_datetime(link_dict['date'])
        except:
            link_dict['date'] = 'NaN'
        article_p_list = []
        for p in driver.find_elements_by_xpath('//div[@itemprop="articleBody"]//p'):
            article_p_list.append(p.text)
        link_dict['text'] = '\n\n'.join(article_p_list)

        print(link_dict['date'], time_border)
        topic_list.append(link_dict)
        if link_dict['date'] > time_border:
            any_in = True

    articles_df_inside = pd.DataFrame(topic_list)
    df = pd.DataFrame(all_articles)
    df_temp = pd.merge(df, articles_df_inside, on='link', how='right')
    df_all = df_all.append(df_temp)

    if not any_in:
        df_all.to_csv(csv_dir + 'conversation' + '.csv')

    else:

        i = i + 1
        next_page = 'https://theconversation.com/uk/technology/articles' + '?page=' + str(i)
        driver.get(next_page)
        print(next_page)
        arts = []
        article_links(arts)

        return download_articles(all_articles=arts, time_border=time_border, df_all=df_all, csv_dir=csv_dir, i=i)

        df_all.to_csv(csv_dir + 'conversation' + '.csv')

    return df_all


d = {'link': [], 'title_outside': [], 'abstract_outside': [], 'author': [], 'date': [], 'text': []}
df_all = pd.DataFrame(data=d)

time_border=pd.to_datetime('now') - pd.Timedelta('190 days')
arts = []
article_links(arts)
download_articles(all_articles=arts, time_border=time_border, df_all=df_all, csv_dir=csv_dir_common(), i=1)
