from common_scraping import sleep_r, full_driver, csv_dir_common
import pandas as pd

link = 'https://www.fastcompany.com/category/technology/1'
driver = full_driver()
driver.get(link)


def article_links(arts):
    sleep_r('m')
    articles_all = driver.find_element_by_class_name('all-feed').find_elements_by_tag_name('article')
    if not articles_all:
        driver.refresh()
        sleep_r('l')
        articles_all = driver.find_element_by_class_name('all-feed').find_elements_by_tag_name('article')
    for article in articles_all:
        article_link = article.find_element_by_tag_name('a').get_attribute('href')
        article_title = article.find_element_by_tag_name('a').get_attribute('title')
        try:
            article_abstract = article.find_element_by_tag_name('h3').text
        except:
            article_abstract = "Nan"
        if 'the-only-hawaiian-shirt-you-should-wear-this-summer' in article_link:
            continue
        arts.append({'link': article_link,
                     'title_outside': article_title,
                     'abstract_outside': article_abstract}
                    )
    return arts


def download_articles(all_articles, time_border, df_all, i, csv_dir):
    stop_categories = False
    topic_list = []
    for i_art, art in enumerate(all_articles):
        print(i_art, len(all_articles), art['link'])
        link_dict = {}
        sleep_r('m')
        driver.get(art['link'])
        sleep_r('s')
        link_dict['link'] = art['link']
        link_dict['title'] = driver.find_element_by_class_name('post__title').find_element_by_tag_name('a').text
        try:
            link_dict['author'] = driver.find_element_by_class_name('post__by').text
        except:
            link_dict['author'] = "NaN"
        try:
            link_dict['date'] = driver.find_element_by_class_name('eyebrow__item').find_element_by_tag_name(
                'time').get_attribute('datetime')
            article_date = pd.to_datetime(link_dict['date'])
        except:
            article_date = pd.to_datetime('2050-01-01')

        article_p_list = []
        retry_count = 0
        while retry_count < 5:
            try:
                for p in driver.find_element_by_class_name('post__article ').find_elements_by_tag_name('p'):
                    article_p_list.append(p.text)
                    link_dict['text'] = '\n\n'.join(article_p_list)
                break
            except:
                retry_count += 1
                driver.refresh()
                sleep_r('m')

        topic_list.append(link_dict)

        if article_date < time_border:
            stop_categories = True

    articles_df_inside = pd.DataFrame(topic_list)
    df = pd.DataFrame(all_articles)
    df_temp = pd.merge(df, articles_df_inside, on='link', how='right')
    df_all.append(df_temp)

    if not stop_categories:
        i = i + 1
        next_page = 'https://www.fastcompany.com/category/technology/' + str(i)
        driver.get(next_page)
        print(next_page)
        arts = []
        article_links(arts)

        return download_articles(all_articles=arts, time_border=time_border, df_all=df_all, i=i, csv_dir=csv_dir)

    pd.DataFrame(pd.concat(df_all)).to_csv(csv_dir + 'fastcompany' + '.csv')

    return df_all

df_all = []
time_border=pd.to_datetime('now') - pd.Timedelta('190 days')
arts = []
article_links(arts)
download_articles(all_articles=arts, time_border=time_border, df_all=df_all, i=1, csv_dir=csv_dir_common())
