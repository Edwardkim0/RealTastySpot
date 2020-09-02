import requests
import pprint
import pandas as pd
import os


def postprocess_df(file_path, basis_name='mac_name'):
    df = pd.read_csv(file_path, sep='\t')
    for col in df.columns:
        if "Unnamed" in col:
            df = df.drop(col, axis=1)
    _dir = os.path.dirname(file_path)
    _path = file_path.split(os.path.sep)[-1]
    new_path = os.path.join(_dir, 'new_' + _path)

    print(df[df.duplicated([basis_name])])
    df = df.drop_duplicates([basis_name]).reset_index(drop=True)
    # df = df.drop_duplicates(['latitude', 'longitude']).reset_index(drop=True)
    df.to_csv(new_path, sep='\t')
    return new_path

if __name__ == '__main__':
    file_path = 'data/2020-06-24_16_53_맥드라이브.csv'
    postprocess_df(file_path)