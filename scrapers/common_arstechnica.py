from common_scraping import sleep_r, full_driver, csv_dir_common
import pandas as pd

driver = full_driver()
driver.get('https://arstechnica.com/')


def topics_links():
    # find links to categories (BIZ & IT, TECH etc.)
    topics_a = driver.find_elements_by_xpath('//nav[@id="header-nav-primary"]//a')
    topics_href = []

    for i in topics_a:
        if i.text not in ['GAMING & CULTURE', 'FORUMS'] and i.text != 'TECH':
            # specification says these categories are unnecessary
            # FORUMS would also break the code

            topics_href.append(i.get_attribute('href'))
            # append already clean links

    return topics_href


def categories_links(time_border, arts, category):
    stop_categories = False
    article_category = category.split('/')[-2]
    articles_all = driver.find_elements_by_xpath('//li[contains(@class, "article")]')
    for article in articles_all:
        article_link = article.find_element_by_xpath('.//a').get_attribute('href')
        article_title = article.find_element_by_xpath('.//header/h2').text  # 2a
        article_abstract = article.find_element_by_xpath('.//header/p[@class="excerpt"]').text  # 2b
        article_author = article.find_element_by_xpath('.//p[@class="byline"]//span[@itemprop="name"]').text  # 2c
        date = article.find_element_by_xpath('.//time')
        article_date = pd.to_datetime(date.get_attribute('datetime'))  # 2d
        article_number_of_comments = article.find_element_by_xpath(
            './/footer//span[@class="comment-count-number"]').text  # 2e

        arts.append({'link': article_link,
                     'category': article_category,
                     'title_outside': article_title,  # 2a
                     'abstract_outside': article_abstract,  # 2b
                     'author_outside': article_author,  # 2c
                     'date_outside': article_date,  # 2d
                     'comments_count_outside': article_number_of_comments}  # 2e
                    )
        print(article_date, time_border)
        if article_date < time_border:
            stop_categories = True

    if not stop_categories:
        sleep_r('m')
        next_page_div = driver.find_elements_by_xpath('//div[contains(@class, "prev-next-links")]/a')
        if len(next_page_div) == 1:  # only load more stories available on the first page
            next_page = next_page_div[0].get_attribute('href')
        elif len(next_page_div) > 1:  # older stories / newer stories
            next_page = next_page_div[0].find_element_by_xpath('./../a[@rel="prev"]').get_attribute('href')
        else:
            return arts
        driver.get(next_page)
        return categories_links(time_border=time_border, arts=arts, category=category)

    return arts


def download_articles(all_articles, time_border, csv_dir):
    for cat, df_grp in all_articles.groupby('category'):  # only one category at a time
        topic_list = []
        for i, row in df_grp.iterrows():
            link_dict = {}
            link = row['link']
            print(i, link)

            sleep_r('m')
            driver.get(link)
            sleep_r('s')

            link_dict['link'] = link

            link_dict['title'] = driver.find_element_by_xpath('//h1[@itemprop="headline"]').text  # 4a
            link_dict['description'] = driver.find_element_by_xpath('//h2[@itemprop="description"]').text  # 2b/4a
            link_dict['author'] = driver.find_element_by_xpath('//span[@itemprop="name"]').text  # 2c
            link_dict['date'] = driver.find_element_by_xpath(
                '//section[contains(@class, "post-meta")]//time').get_attribute('datetime')

            # all_articles may contain too many articles
            # time_border is checked only with regards to page
            if pd.to_datetime(link_dict['date']) < time_border or pd.to_datetime(row['date_outside']) < time_border:
                continue

            article_p_list = []
            for p in driver.find_elements_by_xpath('//div[@itemprop="articleBody"]/p'):
                article_p_list.append(p.text)
            link_dict['text'] = '\n\n'.join(article_p_list)  # 4a

            topic_list.append(link_dict)

        articles_df_inside = pd.DataFrame(topic_list)  # converting list of dicts to DataFrame
        print(articles_df_inside.shape[0])

        # merging outside with inside
        pd.merge(df_grp, articles_df_inside, on='link', how='right').to_csv(csv_dir + 'arstechnica_' + cat + '.csv')


csvs = csv_dir_common()
topics = topics_links()
print(topics)
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