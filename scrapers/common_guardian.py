from common_scraping import sleep_r, full_driver, csv_dir_common
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import pickle

driver = full_driver()
driver.get('https://www.theguardian.com/technology?page=1')


def categories_links(time_border, art_links):
    temp_art_links = []
    articles = driver.find_elements_by_xpath('//div[@class="fc-item__container"]')
    next_page = driver.find_element_by_xpath('//a[contains(@aria-label, " next page")]').get_attribute('href')
    any_in = False

    for article in articles:
        article_link = article.find_element_by_xpath('.//a').get_attribute('href')
        article_title = article.find_element_by_xpath('.//*[contains(@class,"fc-item__title")]').text
        article_date = article.find_element_by_xpath('.//div[contains(@class, "fc-item__meta")]/time').get_attribute('datetime')

        try:
            article_author = article.find_element_by_xpath('.//div[@class="fc-item__byline"]').text
        except NoSuchElementException:
            article_author = ''

        try:
            article_comment_count = article.find_element_by_xpath('.//a[@data-link-name="Comment count"]').text
        except NoSuchElementException:
            article_comment_count = ''

        if pd.to_datetime(article_date) > time_border:
            any_in = True
            temp_art_links.append({'link': article_link,
                                   'title_outside': article_title,
                                   'date_outside': article_date,
                                   'author_outside': article_author,
                                   'comment_count_outside': article_comment_count,
                                   }
                                  )
    print(art_links)
    if not any_in:
        pickle.dump(art_links, open('guardian_links.pickle', 'wb'))  # in case something goes wrong with articles
        return art_links
    else:
        art_links += temp_art_links
        sleep_r('m')
        try:
            driver.get(next_page)
        except Exception as ex:
            print(ex)
            return art_links
        return categories_links(time_border=time_border, art_links=art_links)


def download_articles(all_articles, time_border, csv_dir):
    print(all_articles)
    for i_art, art in enumerate(all_articles):
        print(i_art, len(all_articles), art)
        link_dict = {}
        try:
            driver.get(art['link'])

            sleep_r('m')

            link_dict['link'] = art['link']
            try:
                link_dict['title'] = driver.find_element_by_xpath('//h1[@itemprop="headline"]').text
            except NoSuchElementException:
                try:
                    link_dict['title'] = driver.find_element_by_xpath('//h1[@articleprop="headline"]').text
                except NoSuchElementException:
                    print(art['link'], 'no title')
                    continue
            try:
                link_dict['author'] = driver.find_element_by_xpath('//span[@itemprop="name"]').text
            except NoSuchElementException:
                link_dict['author'] = ''

            try:
                link_dict['description'] = driver.find_element_by_xpath('//div[@class="gs-container"]//p').text
            except NoSuchElementException:
                link_dict['description'] = ''

            try:
                link_dict['date'] = driver.find_element_by_xpath(
                    '//div[contains(@class,"content__meta-container")]//time').get_attribute('datetime')  # 5a
            except NoSuchElementException:
                continue  # we don't need articles if we're not certain about date
            if pd.to_datetime(link_dict['date']) < time_border:
                continue

            article_p_list = []
            for p in [x.text for x in driver.find_elements_by_xpath('//div[(@itemprop="articleBody") or'
                      '(@itemprop="reviewBody")]/p')]:
                article_p_list.append(p)

            link_dict['text'] = '\n\n'.join(article_p_list)

            art.update(link_dict)
            all_articles[i_art] = art

        except TimeoutException:
            print('timeout', art['link'])
            all_articles.append(art)
            continue

    pd.DataFrame(all_articles).to_csv(csv_dir + 'guardian.csv')


csvs = csv_dir_common()
# you may freely change the parameter in line below
time_limit = pd.to_datetime('now') - pd.Timedelta('190 days')  # 3

sleep_r('m')
articles = categories_links(time_border=time_limit, art_links=[])

download_articles(articles, time_border=time_limit, csv_dir=csvs)