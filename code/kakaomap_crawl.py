from multiprocessing import freeze_support
from time import sleep

import selenium.webdriver as webdriver
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from itertools import cycle
import pandas as pd
from utils.address_convert import dataframe_loc_convert
from utils.csv_postprocess import postprocess_df
from utils.data_process import save_dataframe


def crawl_data():
    df_rows = []
    search = input("검색어를 입력하세요 : ")
    driver = webdriver.Chrome()
    base_url = 'https://map.kakao.com'
    driver.get(base_url)
    sleep(1)
    search_window = driver.find_element_by_xpath('//*[@id="search.keyword.query"]')
    search_window.send_keys(search)
    sleep(1)
    search_window.send_keys(Keys.RETURN)

    sleep(1.5)
    search_more = driver.find_element_by_xpath('//*[@id="info.search.place.more"]')
    search_more.send_keys(Keys.ENTER)
    sleep(1)
    driver.find_element_by_xpath(f'//*[@id="info.search.page.no1"]').send_keys(Keys.ENTER)
    sleep(1)
    total_row_nums = int(driver.find_element_by_xpath('//*[@id="info.search.place.cnt"]').text)
    for page in cycle(['no2', 'no3', 'no4', 'no5', 'next']):
        try:
            mac_names = driver.find_elements_by_xpath(
                f'//*[@id="info.search.place.list"]/li/div[3]/strong/a[2]')
            addresses = driver.find_elements_by_xpath(
                f'//*[@id="info.search.place.list"]/li/div[5]/div[2]/p[1]')
            addresses2 = driver.find_elements_by_xpath(
                f'//*[@id="info.search.place.list"]/li/div[5]/div[2]/p[2]')
            scores = driver.find_elements_by_xpath(
                f'//*[@id="info.search.place.list"]/li/div[4]/span[1]/em')
            for m, a1, a2, s in zip(mac_names, addresses, addresses2, scores):
                try:
                    row = {
                        'mac_name': m.text,
                        'address': a1.text,
                        'address2': a2.text,
                        'score': s.text
                    }
                    df_rows.append(row)
                    sleep(0.1)
                except Exception as e:
                    print(e)
        except NoSuchElementException as e:
            print(f'{e}')
            continue
        except StaleElementReferenceException as e:
            print(f'{e}')
            continue
        try:
            next_page = driver.find_element_by_xpath(f'//*[@id="info.search.page.{page}"]')
            if total_row_nums <= len(df_rows):
                break
            elif next_page.is_enabled():
                next_page.send_keys(Keys.ENTER)
                sleep(1)
            else:
                break
        except Exception as e:
            print('next page error, break out!')
            break

    dataframe = pd.DataFrame(data=df_rows)
    save_path = save_dataframe(search, dataframe)
    print("저장완료")
    return save_path


if __name__ == '__main__':
    freeze_support()
    save_path = crawl_data()
    save_path = dataframe_loc_convert(save_path, 'address')
    postprocess_df(save_path)
