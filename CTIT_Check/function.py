# -*- coding: utf-8 -*-
"""
Created on Mon Jul  2 19:23:16 2018

@author: jhon.harry
"""

import pandas as pd
import numpy as np
import datetime as dt
import sqlalchemy as sa
from datetime import datetime
from .config import *


# Connection to Database
def connection_engine(connection_to_database):
    con_engine = sa.create_engine(connection_to_database)
    return con_engine


# Read CSV file
def read_csv(csv_filename):
    raw_data = pd.read_csv(csv_filename)
    return raw_data


# CTIT Check on raw data
def ctit_check(raw_data):
    raw_data['CTIT Status'] = False
    for index, row in raw_data.iterrows():
        attributeTouchTime = datetime.strptime(row['Attributed Touch Time'], '%Y-%m-%d %H:%M:%S')
        installTime = datetime.strptime(row['Install Time'], '%Y-%m-%d %H:%M:%S')
        time_reduce = installTime - attributeTouchTime
        if time_reduce.total_seconds() < 21:
            raw_data.at[index, 'CTIT Status'] = True
    return raw_data


# Device Check on raw data
def device_check(raw_data):
    white_list_device = raw_data[['Device Type']]
    white_list_device['Total Device'] = 0
    white_list_device = white_list_device.groupby('Device Type', as_index=False)['Total Device'].count()
    white_list_device = white_list_device[white_list_device['Total Device'] > minimal_device]
    raw_data = raw_data.merge(white_list_device, on=['Device Type'], indicator='Device Status', how='left')
    raw_data.drop('Total Device', axis=1)
    raw_data['Device Status'] = np.where(raw_data['Device Status'] == 'both', True, False)
    return raw_data


# Get Fraud data
def fraud_check(raw_data):
    fraud_data = raw_data.loc[(raw_data['Device Status'] == False) & (raw_data['CTIT Status'] == True)]
    fraud_data = fraud_data[['AppsFlyer ID']]
    return fraud_data


# Insert raw data to database
def insert_data_to_db(raw_data, con_engine):
    raw_data.to_sql(name='install', con=con_engine, if_exists='append', index=False)


# Insert fraud data to database
def insert_fraud_to_db(fraud_data, con_engine):
    fraud_data.to_sql(name='fraud', con=con_engine, if_exists='append', index=False)


# appversion_data.to_sql(name='appversion', con=con_engine, if_exists='replace', index=False)


# Get App Version from databaset

def select_app_version_from_db(platform, con_engine):
    with con_engine.connect() as cursor:
        device = pd.read_sql(""" SELECT * FROM appversion 
                                        WHERE "Platform" LIKE '%s'
                                           """ % platform, cursor)
    device['Date Release'] = pd.to_datetime(device['Date Release'])
    last_one_month = dt.datetime.now() - dt.timedelta(days=30)
    device = device[device['Date Release'] > last_one_month]
    return device
