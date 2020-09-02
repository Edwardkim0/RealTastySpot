import os
from datetime import datetime
import pandas as pd


def save_dataframe(search_name, df):
    now = datetime.now()
    save_dir = 'data'
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, now.strftime("%Y-%m-%d_%H_%M_") + search_name + '.csv')
    df.to_csv(save_path, sep='\t')
    return save_path

def read_csv(data_path):
    dataframe = pd.read_csv(data_path, sep='\t')
    if 'Unnamed: 0' in dataframe.columns:
        dataframe = dataframe.drop('Unnamed: 0', axis=1)
    return dataframe