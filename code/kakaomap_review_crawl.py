from multiprocessing import freeze_support
from time import sleep
import selenium.webdriver as webdriver
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import pandas as pd
from itertools import cycle
from utils.data_process import save_dataframe
from utils.csv_postprocess import postprocess_df


def crawl_review_data():
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
            links = driver.find_elements_by_xpath(
                f'//*[@id="info.search.place.list"]/li/div[4]/a')
            for m, a1, a2, s, l in zip(mac_names, addresses, addresses2, scores, links):
                try:
                    row = {
                        'mac_name': m.text,
                        'address': a1.text,
                        'address2': a2.text,
                        'score': s.text,
                        'link': l.get_attribute('href')
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
    print(f"{save_path} 저장완료")

    for row in df_rows:
        row['num_review'] = 0
        row['reviews'] = []
        row['scores'] = []
        row['dates'] = []
        driver.get(row['link'])
        sleep(1)
        try:
            num_reviews = driver.find_element_by_xpath('//*[@id="mArticle"]/div[5]/div[2]/a/span[1]').text
            row['num_review'] = num_reviews
        except:
            print('num_reviews error... maybe no review yet')
            continue
        num_pages, num_last = divmod(int(num_reviews), 5)
        if (num_last == 0) and (num_pages > 0): num_pages -= 1
        num_pages += 1
        for idx, page in enumerate(cycle([2, 3, 4, 5])):
            try:
                review_elems = driver.find_elements_by_xpath('//*[@id="mArticle"]/div[5]/div[4]/ul/li/div[2]/p/span')
                review_scores = driver.find_elements_by_xpath('//*[@id="mArticle"]/div[5]/div[4]/ul/li/div[1]/div/em')
                review_dates = driver.find_elements_by_xpath(
                    '//*[@id="mArticle"]/div[5]/div[4]/ul/li/div[2]/div/span[3]')
                for elem, score, date in zip(review_elems, review_scores, review_dates):
                    row['reviews'].append(elem.text)
                    row['scores'].append(score.text)
                    row['dates'].append(date.text)
                sleep(0.5)
                if page > num_pages:
                    break
            except Exception as e:
                print(e, 'review appending failed...')
                continue
            try:
                next_page = driver.find_element_by_xpath(f'//*[@id="mArticle"]/div[5]/div[4]/div/a[{page - 1}]')
                next_page.send_keys(Keys.RETURN)
                sleep(0.5)
            except Exception as e:
                print(e, 'next page failed.')
                continue
            if idx + 2 > num_pages:
                break

    dataframe = pd.DataFrame(data=df_rows)
    save_path = save_dataframe(search + '_review', dataframe)
    print(f"{save_path} 저장완료")
    return save_path


def get_link_from_placelist(place_csv_path='../data/pilot_lists2.csv'):
    place_df = pd.read_csv(place_csv_path, sep=',')
    place_list = place_df.name
    place_list = place_list.map(lambda x: x + " 여의도")

    driver = webdriver.Chrome()
    base_url = 'https://map.kakao.com/'
    driver.get(base_url)
    sleep(1.5)

    place_df.link = ''

    for i, search in enumerate(place_list):
        search_window = driver.find_element_by_xpath('//*[@id="search.keyword.query"]')
        search_window.send_keys(search)
        sleep(1)
        search_window.send_keys(Keys.RETURN)
        sleep(1)

        try:
            place_df.loc[i, 'link'] = driver.find_element_by_class_name('moreview').get_attribute('href')
            search_window.clear()
            sleep(0.5)
            continue
        except:
            search_window.clear()
            sleep(0.5)
            continue

    place_df.to_csv('../data/여의도 맛집 list/pilot_list2_with_kakao_link.csv', index=False)


def crawl_review_data_from_list(crawled_data, basis_column='loc_name', sep='\t'):
    linkdata = pd.read_csv(crawled_data, sep=sep)
    if 'Unnamed: 0' in linkdata.columns:
        df_rows = linkdata.drop_duplicates([basis_column], ignore_index=True)
        df_rows = df_rows.drop('Unnamed: 0', axis=1)
    else:
        df_rows = linkdata.drop_duplicates([basis_column], ignore_index=True)

    driver = webdriver.Chrome()
    search = crawled_data.split('_')[-1].split('.')[0]
    final_rows = []
    save_period = 2
    for idx, row in df_rows.iterrows():
        if idx < 41:
            continue
        driver.get(row['link'])
        sleep(1)
        try:
            loc_info = driver.find_element_by_class_name('inner_place').text.split('\n')
            row['loc_name'] = loc_info[0]
            print(row['loc_name'])
        except:
            row['loc_name'] = search
            print(row['loc_name'])

        sleep(1)
        row['reviews'] = {}
        row['scores'] = {}
        row['dates'] = {}
        count = 0
        try:
            num_reviews = int(driver.find_element_by_class_name('evaluation_sorting').text.split('전체')[1])
            row['num_review'] = num_reviews
        except:
            print('num_reviews error... maybe no review yet')
            continue
        end_flag = False
        while not end_flag:
            try:
                num_linkpages = max(len(driver.find_elements_by_class_name('link_page')), 1)
            except:
                break

            for i in range(num_linkpages):
                try:
                    linkpages = driver.find_elements_by_class_name('link_page')
                except Exception as e:
                    print(e, f'{search} review appending failed...')
                    pass

                reviews = driver.find_elements_by_class_name('txt_comment')
                sleep(0.1)
                scores = driver.find_elements_by_class_name('star_info')
                sleep(0.1)
                dates = driver.find_elements_by_class_name('time_write')
                sleep(0.1)
                for review, score, date in zip(reviews, scores, dates):
                    try:
                        row['reviews'][count] = review.text
                    except Exception as e:
                        print(f'{search} {e} review error')
                        row['reviews'][count] = ''
                    try:
                        row['scores'][count] = score.text
                    except Exception as e:
                        print(f'{search} {e} score error')
                        row['scores'][count] = ''
                    try:
                        row['dates'][count] = date.text[:-1]
                    except Exception as e:
                        print(f'{search} {e} date error')
                        row['dates'][count] = ''
                    count += 1
                    sleep(0.3)
                sleep(0.1)

                if (len(linkpages) < 5 and (i == len(linkpages) - 1)) or len(linkpages) == 0:
                    end_flag = True
                    break
                try:
                    linkpages[i + 1].send_keys(Keys.ENTER)
                    sleep(1)
                except:
                    pass
                if i == 4:
                    try:
                        driver.find_element_by_class_name('btn_next').click()
                        end_flag = False
                        sleep(1)
                        break
                    except:
                        end_flag = True
                        break
        print(
            f'{search} crwal complete, reviews : {len(row["reviews"])}, scores : {len(row["scores"])}, dates : {len(row["dates"])}')
        final_rows.append(row)

        if idx % save_period == 0:
            dataframe = pd.DataFrame(data=final_rows)
            save_path = save_dataframe(search + 'kakao_review', dataframe)
            print(f"{idx}... {save_path} 저장완료")

    dataframe = pd.DataFrame(data=final_rows)
    save_path = save_dataframe(search + 'kakao_review', dataframe)
    print(f"{save_path} 저장완료")
    return save_path


if __name__ == '__main__':
    freeze_support()
    # get_link_from_placelist()
    crawl_review_data_from_list('../data/여의도 맛집 list/pilot_list2_with_kakao_link.csv', 'name', sep=',')
    # save_path = crawl_review_data()
    # postprocess_df(save_path)
