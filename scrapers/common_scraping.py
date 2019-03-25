from selenium import webdriver
from time import sleep
from numpy.random import uniform


def sleep_r(length):
    if length == "s":
        return sleep(uniform(0.25, 0.5))
    elif length == "m":
        return sleep(uniform(1, 2))
    elif length == "l":
        return sleep(uniform(4, 6))
    else:
        print("error")


def full_driver():
    chrome_options = webdriver.ChromeOptions()

    # load ublock
    # It should throw an error if path is wrong (and it is surely wrong unless you change it)
    path_to_ublock = '/home/username/.config/chromium/Default/Extensions/cjpalhdlnbpafiamejdnhcphjbkeiagm/1.15.24_0'
    chrome_options.add_argument('--load-extension=' + path_to_ublock)

    # if you feel like it and are really time-constrained, you may try --headless argument as well
    # like this: chrome_options.add_argument('--headless')

    # smaller window size may cause problems, because some websites are responsive
    chrome_options.add_argument('--window-size=1360,700')
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.set_page_load_timeout(180)
    return driver


def csv_dir_common():
    return './csv_final/'
