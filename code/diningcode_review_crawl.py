from multiprocessing import freeze_support
from time import sleep
import selenium.webdriver as webdriver
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import pandas as pd
from itertools import cycle, islice
from utils.data_process import save_dataframe
from utils.csv_postprocess import postprocess_df
import numpy as np


def click_nolink_for_scrollDown(driver, scrollDown_num=100):
    print('scroll down for seeing more review')
    url = driver.current_url
    while True:
        try:
            body = driver.find_element_by_css_selector('body')
        except:
            driver.refresh()
            sleep(1)
        body.click()
        sleep(0.1)
        if url == driver.current_url:
            break
        else:
            driver.execute_script("window.history.go(-1)")
    sleep(0.1)
    for i in range(scrollDown_num):
        sleep(0.3)
        body.send_keys(Keys.PAGE_DOWN)


def crawl_diningcode():
    df_rows = []
    # search = input("검색어를 입력하세요 : ")
    place_list = pd.read_csv('/Users/dhkim/PycharmProjects/RealTastySpot/data/pilot_lists2.csv')
    print(place_list.head())
    search_list = place_list.name.values
    driver = webdriver.Chrome()
    base_url = 'https://www.diningcode.com/'
    driver.get(base_url)
    sleep(1)

    for idx, search in enumerate(search_list):
        if idx < 35:
            continue
        search_window = driver.find_element_by_xpath('//*[@id="txt_keyword"]')
        search_window.send_keys(search + " 영등포")
        sleep(1)
        search_window.send_keys(Keys.RETURN)

        sleep(3)
        try:
            clikc_link = driver.find_element_by_xpath('//*[@id="div_rn"]/ul/li/a')
            clikc_link.send_keys(Keys.ENTER)
        except:
            print(f'there is no place {search}')
            continue
        sleep(2)
        driver.close()
        sleep(1)
        driver.switch_to.window(driver.window_handles[0])
        while True:
            try:
                more_review = driver.find_element_by_id('div_more_review')
                more_review.click()
                sleep(0.5)
                click_nolink_for_scrollDown(driver, 3)
                sleep(0.2)
            except:
                break

        # scores = driver.find_elements_by_class_name('point-detail')
        dates = driver.find_elements_by_class_name('star-date')
        reviews = driver.find_elements_by_class_name('review_contents')
        scores = [float(
            x.find_element_by_class_name('star').find_element_by_tag_name('i').get_attribute('style').split(' ')[
                1].replace('%;', '')) / 100 * 5 for x in dates]
        for score, data, review in zip(scores, dates, reviews):
            try:
                row = {
                    'name': search,
                    'review': review.text,
                    'date': data.text,
                    'score': score
                }
                df_rows.append(row)
                sleep(0.1)
            except Exception as e:
                print(e)

        dataframe = pd.DataFrame(df_rows)
        save_path = save_dataframe('crawl_diningcode' + '_review', dataframe)
        print(f"{save_path} 저장완료")
    return save_path


def crawl_diningcode_favor():
    df_rows = []
    # search = input("검색어를 입력하세요 : ")
    place_list = pd.read_csv('/Users/dhkim/PycharmProjects/RealTastySpot/data/pilot_lists2.csv')
    print(place_list.head())
    search_list = place_list.name.values
    driver = webdriver.Chrome()
    base_url = 'https://www.diningcode.com/'
    driver.get(base_url)
    sleep(1)

    for idx, search in enumerate(search_list):
        if idx < 15:
            continue
        search_window = driver.find_element_by_xpath('//*[@id="txt_keyword"]')
        search_window.send_keys(search + " 영등포")
        sleep(1)
        search_window.send_keys(Keys.RETURN)

        sleep(3)
        try:
            clikc_link = driver.find_element_by_xpath('//*[@id="div_rn"]/ul/li/a')
            clikc_link.send_keys(Keys.ENTER)
        except:
            print(f'there is no place {search}')
            continue
        sleep(2)
        driver.close()
        sleep(1)
        driver.switch_to.window(driver.window_handles[0])

        try:
            driver.find_element_by_id('div_profile').find_elements_by_class_name('s-list')[
                1].find_element_by_class_name('favor').find_element_by_tag_name('a').click()
            sleep(1)
            counts = driver.find_element_by_id('lbl_favorites_count').text
            sleep(0.1)
            body = driver.find_element_by_css_selector('body')
            body.click()
            for i in range(np.clip(int(counts)//3, 1, int(counts)//2)):
                sleep(0.3)
                body.send_keys(Keys.PAGE_DOWN)
            favor_str = driver.find_element_by_id('ul_favorites_list').text
            favor_list = favor_str.split('\n')
            people = islice(favor_list, 0, len(favor_list)-1, 2)
            dates = islice(favor_list, 1, len(favor_list)-1, 2)
            for person, date in zip(people, dates):
                if not '년' in date:
                    date = '2020년 ' + date
                rows = {
                    'name': search,
                    'person': person,
                    'like_date': date
                }
                df_rows.append(rows)

        except Exception as e:
            driver.get(base_url)
            sleep(1)
            print(e)
        dataframe = pd.DataFrame(df_rows)
        save_path = save_dataframe('crawl_diningcode_favor' + '_review', dataframe)
        print(f"{save_path} 저장완료")
    return save_path


if __name__ == '__main__':
    freeze_support()

    pd_df = crawl_diningcode_favor()
    print(pd_df)
