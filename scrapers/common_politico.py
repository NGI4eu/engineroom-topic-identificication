from common_scraping import sleep_r, full_driver, csv_dir_common
import pandas as pd

driver = full_driver()

def get_page(category, page):
    link = f"https://www.politico.eu/section/{category}/page/{page}"
    driver.get(link)
    
def get_links():
    articles = driver.find_elements_by_xpath("//section[@class='content-groupset pos-alpha']//div[@class='summary']/header//a")
    articles = [art.get_attribute('href') for art in articles]
    return articles
    
def get_info(link):
    driver.get(link)
    try:
        art_title = driver.find_element_by_xpath("//div/header/h1").text
    except NoSuchElementException:
        print('no title', link)
        return None
    try:
        art_author = driver.find_element_by_xpath("//a[@rel='author']").text
    except NoSuchElementException:
        print('no author', link)
        art_author = ''
    try:
        art_abstract = driver.find_element_by_xpath("//p[@class='subhead']").text
    except NoSuchElementException:
        print('no abstract', link)
        art_abstract = ''
    try:
        art_date = driver.find_element_by_xpath("//div/footer[@class='meta']/p[@class='timestamp']/time").get_attribute('datetime')
    except NoSuchElementException:
        print('no time', link)
        return None
#     art_datex = art_date.get_attribute('datetime')
    art_texts = driver.find_elements_by_xpath("//div[@class = 'story-text has-sidebar']/p")
    art_text_para = '\n\n'.join([para.text for para in art_texts])
    return {'link': link, 'title': art_title, 'author': art_author, 'abstract': art_abstract, 'date': art_date, 'text': art_text_para}

categories = ['data-and-digitization', 'technology', 'sustainability']
csvdir = csv_dir_common()
time_limit = pd.to_datetime('now') - pd.Timedelta('1170 days')

for cat in categories:
    print(cat)
    art_dicts = []
    time_limit_reached = False
    i=1
    driver.get(f"https://www.politico.eu/section/{cat}/")
    get_page(cat, 1)
    count_pages = int(driver.find_element_by_xpath("//a[@class='page-numbers']").text)
    while i<=count_pages and not time_limit_reached:
        get_page(cat, i)
        links = get_links()
        for link in links:
            info = get_info(link)
            if info is None:
                continue
<<<<<<< HEAD
=======
#             print(info['date'])
>>>>>>> 0cd159f401e3f5c0fe800013dd578d725f38fc98
            if pd.to_datetime(info['date']) < time_limit:
                time_limit_reached = True
                break
            art_dicts.append(info)
<<<<<<< HEAD
=======
#             print(info)
#             time.sleep(random.uniform(0.75, 2.5))
>>>>>>> 0cd159f401e3f5c0fe800013dd578d725f38fc98
        i=i+1
        links.clear()
        print(len(art_dicts))
        
    if len(art_dicts) > 0:
        df_politico = pd.DataFrame(art_dicts)
        df_politico.drop_duplicates(subset=['link'], inplace=True)
        df_politico.to_csv(csvdir + 'politico_' + cat + '.csv')