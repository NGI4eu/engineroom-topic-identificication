from common_scraping import sleep_r, full_driver, csv_dir_common
import pandas as pd
from selenium.common.exceptions import NoSuchElementException

start=1
link = 'https://www.reuters.com/news/archive/technologyNews?view=page&page=' + str(start) + '&pageSize=10'
driver = full_driver()
driver.get(link)

def article_links(arts, time_border, start):
    any_in = False
    articles_all=driver.find_elements_by_xpath('//div[contains(@class, "column1")]//article')
    for article in articles_all:
        article_link = article.find_element_by_xpath('./div[@class="story-content"]/a').get_attribute('href')
        print(article_link)
        article_title=article.find_element_by_xpath('./div[@class="story-content"]/a/h3').text
        try:
            article_date=article.find_element_by_xpath('./div[@class="story-content"]/time').text
            article_date=pd.to_datetime(article_date)
        except:
            article_date='NaN'
        article_abstract = article.find_element_by_xpath('./div[@class="story-content"]/p').text
        print(article_date)
        if article_date=='NaN' or article_date > time_border:
                any_in = True
                arts.append({'link': article_link,
                                'title_outside': article_title,
                                'abstract_outside': article_abstract,
                                'date_outside': article_date,
                              })
    if not any_in:
        return arts
    else:
        start=start+1
        next_page = 'https://www.reuters.com/news/archive/technologyNews?view=page&page=' + str(start) + '&pageSize=10'
        print(next_page)
        driver.get(next_page)
        sleep_r
        return article_links(arts=arts, time_border=time_border, start=start)


def download_articles(all_articles, csv_dir):
    topic_list=[]
    for i_art, art in enumerate(all_articles):
        print(i_art, len(all_articles), art['link'])
        link_dict = {}
        sleep_r('s')
        link=art['link']
        driver.get(link)
        sleep_r('m')

        link_dict['link'] = link
        link_dict['title'] = driver.find_element_by_xpath('//h1[contains(@class, "headline")]').text
        link_dict['author'] = driver.find_element_by_xpath('//div[contains(@class, "first-container")]/div/div').text
        if 'MIN READ' in link_dict['author']:
            try:
                link_dict['author'] = driver.find_element_by_xpath('//div[contains(@class, "first-container")]/div/p').text
            except NoSuchElementException:
                try:
                    link_dict['author'] = driver.find_element_by_xpath('//p[@class="Attribution_content"]').text
                except NoSuchElementException:
                    link_dict['author'] = 'NaN'
        try:
            link_dict['date'] = driver.find_element_by_xpath('//div[contains(@class, "date")]').text.split('/')[0]
            link_dict['date']=pd.to_datetime(link_dict['date'])
        except:
            link_dict['date']='NaN'

        article_p_list = []
        for p in driver.find_elements_by_xpath('//div[contains(@class, "body")]/p'):
            try:
                article_p_list.append(p.text)
            except:
                pass
        link_dict['text'] = '\n\n'.join(article_p_list)

        topic_list.append(link_dict)

    articles_df_inside = pd.DataFrame(topic_list)
    print(articles_df_inside.shape[0])
    df=pd.DataFrame(all_articles)

    df_all=pd.merge(df, articles_df_inside, on='link', how='right')
    pd.merge(df, articles_df_inside, on='link', how='right').to_csv(csv_dir + 'reuters' + '.csv')


time_border=pd.to_datetime('now') - pd.Timedelta('190 days')
arts=[]
csvs = csv_dir_common()

article_links(arts, time_border, start=1)
download_articles(all_articles=arts, csv_dir=csvs)