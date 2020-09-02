from multiprocessing import freeze_support
from time import sleep

import selenium.webdriver as webdriver
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from itertools import cycle
import pandas as pd
from utils.address_convert import dataframe_loc_convert
from utils.csv_postprocess import postprocess_df
from utils.data_process import save_dataframe


def click_nolink_for_scrollDown(driver, scrollDown_num=100):
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
        sleep(0.1)
        body.send_keys(Keys.PAGE_DOWN)


def crawl_data():
    df_rows = []
    # search = input("검색어를 입력하세요 : ")
    search = "스타벅스dt"
    driver = webdriver.Chrome()
    base_url = 'https://m.naver.com/'
    driver.get(base_url)
    sleep(1.5)
    search_window = driver.find_element_by_xpath('//*[@id="MM_SEARCH_FAKE"]')
    search_window.click()
    sleep(1)
    real_search_window = driver.find_element_by_xpath('//*[@id="query"]')
    real_search_window.send_keys(search)
    real_search_window.send_keys(Keys.ENTER)
    sleep(1.5)
    search_more = driver.find_element_by_xpath('//*[@id="place-main-section-root"]/div/div[4]/div/a')
    search_more.send_keys(Keys.ENTER)
    sleep(1.5)
    SCROLL_TIME = 100
    click_nolink_for_scrollDown(driver, SCROLL_TIME)

    try:
        # loc_names = driver.find_elements_by_xpath(
        #     '//*[@id="_list_scroll_container"]/div/div/div[1]/ul/li/div[1]/a/div[1]/div/span')
        addresses = driver.find_elements_by_xpath(
            '//*[@id="_list_scroll_container"]/div/div/div[1]/ul/li/div[1]/a/div[2]/span[1]')
        num_reviews = driver.find_elements_by_xpath(
            '//*[@id="_list_scroll_container"]/div/div/div[1]/ul/li/div[1]/a/div[3]/span')
        links = driver.find_elements_by_xpath(
            '//*[@id="_list_scroll_container"]/div/div/div[1]/ul/li/div[1]/a')

        for loc, add, num, link in zip(addresses, num_reviews, links):
            try:
                row = {
                    # 'loc_name': loc.text,
                    'address': add.text,
                    'num_review': num.text,
                    'link': link.get_attribute('href')
                }
                df_rows.append(row)
                sleep(0.1)
            except Exception as e:
                print(e)
    except NoSuchElementException as e:
        print(f'{e}')
    except StaleElementReferenceException as e:
        print(f'{e}')

    dataframe = pd.DataFrame(data=df_rows)
    save_path = save_dataframe(search, dataframe)
    print("저장완료")
    return save_path

def review_crawl(crawled_data, basis_column='loc_name', sep='\t'):
    linkdata = pd.read_csv(crawled_data, sep=sep)
    if 'Unnamed: 0' in linkdata.columns:
        df_rows = linkdata.drop_duplicates([basis_column], ignore_index=True)
        df_rows = df_rows.drop('Unnamed: 0', axis=1)
    else:
        df_rows = linkdata.drop_duplicates([basis_column], ignore_index=True)

    driver = webdriver.Chrome()
    search = crawled_data.split('_')[-1].split('.')[0]
    final_rows = []
    save_period = 10
    for idx, row in df_rows.iterrows():
        driver.get(row['link'])
        sleep(1)

        row['loc_name'] = driver.find_element_by_class_name('_3XamX').text
        print(row['loc_name'])
        sleep(1)
        while 'receipt' not in driver.current_url:
            try:
                receipt_review = driver.find_element_by_xpath(
                    '//*[@id="app-root"]/div/div[2]/div[3]/div/div/div/a[3]/span')
                receipt_review.click()
            except Exception as e:
                print(f'{e} ')
                driver.get(row['link'])
                sleep(1)
            sleep(1)
        try:
            row['receipt_num'] = int(driver.find_element_by_class_name('place_section_count').text)
            print(f'receipt_num : {row["receipt_num"]}')
        except Exception as e:
            print('receipt_num error', e)
        sleep(2)
        row['reviews'] = []
        row['scores'] = []
        row['dates'] = []
        try:
            more_receipt = driver.find_element_by_class_name('_3iTUo')
            while more_receipt.is_enabled():
                more_receipt.click()
                sleep(0.4)
        except StaleElementReferenceException as e:
            print(f'{e}, it`s ok .. go to next link')
        except NoSuchElementException as e:
            print(f'{e}, may be no review... it`s ok .. go to next link')

        try:
            review_elems = driver.find_elements_by_class_name('WoYOw')
            review_scores = driver.find_elements_by_class_name('_3qIdi')
            review_infos = driver.find_elements_by_class_name('_2wZjV')
            review_dates = [x for i, x in enumerate(review_infos) if i % 3 == 1]
            visit_nums = [x for i, x in enumerate(review_infos) if i % 3 == 2]
            print(f'receipt_elem_num : {len(review_elems)}, {len(review_scores)}, {len(review_dates)}')
            row['reviews'] = {i: elem.text for i, elem in enumerate(review_elems)}
            row['scores'] = {i: float(score.text) for i, score in enumerate(review_scores)}
            row['dates'] = {i: date.text for i, date in enumerate(review_dates)}
            row['visit_num'] = {i: num.text for i, num in enumerate(visit_nums)}
            print(f"{row['reviews']} \n {row['scores']}\n {row['dates']}\n {row['visit_num']}")
            sleep(0.5)
        except Exception as e:
            print(f'{e} ??')
        final_rows.append(row)

        if idx % save_period == 0:
            dataframe = pd.DataFrame(data=final_rows)
            save_path = save_dataframe(search + '_review', dataframe)
            print(f"{idx}... {save_path} 저장완료")

    dataframe = pd.DataFrame(data=final_rows)
    save_path = save_dataframe(search + '_review', dataframe)
    print(f"{save_path} 저장완료")
    return save_path

def get_link_from_placelist(place_csv_path='../data/pilot_lists2.csv'):
    place_df = pd.read_csv(place_csv_path, sep=',')
    place_list = place_df.name
    place_list = place_list.map(lambda x:x + " 여의도")

    driver = webdriver.Chrome()
    base_url = 'https://m.naver.com/'
    driver.get(base_url)
    sleep(1.5)
    place_df.link = ''

    for i, search in enumerate(place_list):
        search_window = driver.find_element_by_xpath('//*[@id="MM_SEARCH_FAKE"]')
        search_window.click()
        sleep(1)
        real_search_window = driver.find_element_by_xpath('//*[@id="query"]')
        real_search_window.send_keys(search)
        real_search_window.send_keys(Keys.ENTER)
        sleep(1)
        try:
            driver.find_element_by_class_name('_3XamX')
            '//*[@id="loc-main-section-root"]/div'
            '//*[@id="loc-main-section-root"]/div/div[5]/ul/li[1]/div[2]/div[1]/a'
            place_df.loc[i, 'link'] = driver.current_url
            driver.execute_script("window.history.go(-1)")
            sleep(1)
            continue
        except:
            pass

        try:
            place_df.loc[i, 'link'] = driver.find_element_by_xpath(
                '//*[@id="loc-main-section-root"]/div/div[5]/ul/li[1]/div[2]/div[1]/a').get_attribute('href')
            driver.execute_script("window.history.go(-1)")
            sleep(1)
            continue
        except:
            pass

        try:
            place_df.loc[i, 'link'] = driver.find_element_by_xpath('//*[@id="place-main-section-root"]/div/div[5]/ul/li[1]/div[1]/a').get_attribute('href')
            driver.execute_script("window.history.go(-1)")
            sleep(1)
            continue
        except:
            print(f'{search} failed.')
            pass

        try:
            place_df.loc[i, 'link'] = driver.find_element_by_class_name('_1hEhO').find_element_by_tag_name('a').get_attribute('href')
            driver.execute_script("window.history.go(-1)")
            sleep(1)
        except:
            print(f'{search} failed.')
            driver.execute_script("window.history.go(-1)")
            continue

    place_df.to_csv('../data/pilot_list2_with_link', index=False)

def review_crawl(crawled_data, basis_column='loc_name', sep='\t'):
    linkdata = pd.read_csv(crawled_data, sep=sep)
    if 'Unnamed: 0' in linkdata.columns:
        df_rows = linkdata.drop_duplicates([basis_column], ignore_index=True)
        df_rows = df_rows.drop('Unnamed: 0', axis=1)
    else:
        df_rows = linkdata.drop_duplicates([basis_column], ignore_index=True)

    driver = webdriver.Chrome()
    search = crawled_data.split('_')[-1].split('.')[0]
    final_rows = []
    save_period = 10
    for idx, row in df_rows.iterrows():
        driver.get(row['link'])
        sleep(1)

        row['loc_name'] = driver.find_element_by_class_name('_3XamX').text
        print(row['loc_name'])
        sleep(1)
        while 'visitor' not in driver.current_url:
            try:
                receipt_review = driver.find_element_by_xpath(
                    '//*[@id="app-root"]/div/div[2]/div[3]/div/div/div/a[3]/span')
                receipt_review.click()
            except Exception as e:
                print(f'{e} ')
                driver.get(row['link'])
                sleep(1)
            sleep(1)
        try:
            row['visitor_num'] = int(driver.find_element_by_class_name('place_section_count').text)
            print(f'visitor_num : {row["visitor_num"]}')
        except Exception as e:
            print('visitor_num error', e)
        sleep(2)
        row['reviews'] = []
        row['scores'] = []
        row['dates'] = []
        try:
            more_receipt = driver.find_element_by_class_name('_3iTUo')
            while more_receipt.is_enabled():
                more_receipt.click()
                sleep(0.4)
        except StaleElementReferenceException as e:
            print(f'{e}, it`s ok .. go to next link')
        except NoSuchElementException as e:
            print(f'{e}, may be no review... it`s ok .. go to next link')

        try:
            review_elems = driver.find_elements_by_class_name('WoYOw')
            review_scores = driver.find_elements_by_class_name('_2tObC')
            review_infos = driver.find_elements_by_class_name('ql4ZC')
            print(f'visitor_elem_num : {len(review_elems)}, {len(review_scores)}, {len(review_infos)}')
            row['reviews'] = {i: elem.text for i, elem in enumerate(review_elems)}
            row['scores'] = {i: float(score.text) for i, score in enumerate(review_scores)}
            row['dates'] = {i: date.text[:10] for i, date in enumerate(review_infos)}
            row['visit_num'] = {i: num.text[10:] for i, num in enumerate(review_infos)}
            print(f"{row['reviews']} \n {row['scores']}\n {row['dates']}\n {row['visit_num']}")
            sleep(0.5)
        except Exception as e:
            print(f'{e} ??')
        final_rows.append(row)

        if idx % save_period == 0:
            dataframe = pd.DataFrame(data=final_rows)
            save_path = save_dataframe(search + '_review', dataframe)
            print(f"{idx}... {save_path} 저장완료")

    dataframe = pd.DataFrame(data=final_rows)
    save_path = save_dataframe(search + '_review', dataframe)
    print(f"{save_path} 저장완료")
    return save_path


if __name__ == '__main__':
    # s = pd.read_csv('naver_3place.csv', index_col=0)
    # print(s.head())
    # freeze_support()
    # save_path = crawl_data()
    # save_path = dataframe_loc_convert(save_path, 'address')

    # save_path = 'data/2020-06-25_16_23_스타벅스dt.csv'
    # save_path = 'recrwal_select_data.csv'
    # save_path = postprocess_df(save_path, basis_name='address')
    # get_link_from_placelist()
    save_path = '../data/pilot_list2_with_link.csv'
    review_crawl(save_path, basis_column='name', sep=',')
