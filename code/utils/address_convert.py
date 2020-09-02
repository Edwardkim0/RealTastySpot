import requests
from utils.csv_postprocess import postprocess_df
import time


def find_lat_lng(location):
    # 요청 주소(구글맵)

    # Production(실제 서비스) 환경 - https 요청이 필수이고, API Key 발급(사용설정) 및 과금 설정이 반드시 필요합니다.
    URL = 'https://maps.googleapis.com/maps/api/geocode/json?key=AIzaSyBWgPcQF1nWKXIwGLPJVZA4-QYLw5GdVVM' \
          '&sensor=false&language=ko&address={}'.format(location)
    try:
        # URL로 보낸 Requst의 Response를 response 변수에 할당
        response = requests.get(URL)

        # JSON 파싱
        data = response.json()

        # lat, lon 추출
        lat = data['results'][0]['geometry']['location']['lat']
        lng = data['results'][0]['geometry']['location']['lng']
    except Exception as e:
        print(f'{e} : {location} failed to find coordinates')
        # time.sleep(1)
        # lat, lng = find_lat_lng(location)
        lat, lng = 0, 0
    return lat, lng

def dataframe_loc_convert(df, address_column):
    if isinstance(df, str):
        save_path = df
        import pandas as pd
        df = pd.read_csv(save_path, sep='\t')
    else:
        save_path = 'data/converted_result.csv'

    df['latitude'] = ""
    df['longitude'] = ""

    locs = []
    for i, loc in enumerate(df[address_column]):
        lat, lng = find_lat_lng(loc)
        df['latitude'].iloc[i] = lat
        df['longitude'].iloc[i] = lng
        print(f"{lat}'\t'{lng}")
        locs.append((lat, lng))

    if "Unnamed: 0" in df.columns:
        df = df.drop("Unnamed: 0", axis=1)
    df.to_csv(save_path, sep='\t')
    return save_path

if __name__ == '__main__':
    # file_path = 'data/2020-06-24_15_25_맥드라이브.csv'
    import os
    os.chdir('..')
    # file_path = 'data/starbucks/starbucks_review_groupby_200626.csv'
    # dataframe_loc_convert(file_path, 'address')
    # postprocess_df(file_path, basis_name='address')

    file_path = '/Users/dhkim/PycharmProjects/company_list/big_company_address_with_factory.csv'
    file_path = '/Users/dhkim/PycharmProjects/kakomap_crwal/data/2020-07-02_18_46_travel_crawl.csv'
    file_path = '../company_list/starbucks_btw_apt_info.csv'
    file_path = '/Users/dhkim/PycharmProjects/kakomap_crwal/data/2020-07-03_11_58_apt_review.csv'
    file_path = '../company_list/20200707_starbuck_apt_info_notyet.csv'
    file_path = '../samsung_location.xlsx'
    # file_path = './data/starbucks/new_starbucks_review_groupby_200626.csv'
    dataframe_loc_convert(file_path, '주소')
    # postprocess_df(file_path, basis_name='지점명')
    # print(find_lat_lng('충청남도 공주시 장기면 제천리 10'))
    print(find_lat_lng('세종특별자치시 한누리대로 321'))