# -*- coding: utf-8 -*-
"""
Created on Mon Jul  2 19:23:16 2018

@author: jhon.harry
"""

import pandas as pd
import numpy as np
import datetime as dt
import sqlalchemy as sa
import math
from datetime import datetime
from .config import *


# Connection to Database
def connection_engine(connection_to_database):
    con_engine = sa.create_engine(connection_to_database)
    return con_engine


# Read CSV file
def read_csv(csv_filename):
    raw_data = pd.read_csv(csv_filename)
    raw_data = raw_data[['Attributed Touch Time',
                         'Install Time',
                         'Media Source',
                         'Campaign',
                         'Campaign ID',
                         'Site ID',
                         'AppsFlyer ID',
                         'Platform',
                         'Device Type',
                         'App Version',
                         'Is Retargeting',
                         'Original URL',
                         ]]
    return raw_data


# CTIT Check on raw data
def ctit_check(raw_data):
    raw_data['CTIT Status'] = False
    for index, row in raw_data.iterrows():
        if not isinstance(row['Attributed Touch Time'], str) and math.isnan(row['Attributed Touch Time']):
            installTime = datetime.strptime(row['Install Time'], '%Y-%m-%d %H:%M:%S')
            attributeTouchTime = installTime - dt.timedelta(seconds=minimal_time)
        else:
            attributeTouchTime = datetime.strptime(row['Attributed Touch Time'], '%Y-%m-%d %H:%M:%S')
            installTime = datetime.strptime(row['Install Time'], '%Y-%m-%d %H:%M:%S')

        time_reduce = installTime - attributeTouchTime
        if time_reduce.total_seconds() < minimal_time:
            raw_data.at[index, 'CTIT Status'] = True
    return raw_data


# Device Check on raw data
def device_check(raw_data, con_engine):
    with con_engine.connect() as cursor:
        white_list_device = pd.read_sql(""" SELECT "Attributed Touch Time", "Device Type" 
                                        FROM install
                                        """, cursor)
    white_list_device['Attributed Touch Time'] = pd.to_datetime(white_list_device['Attributed Touch Time'])
    white_list_device = white_list_device[
        white_list_device['Attributed Touch Time']
        > dt.datetime.now() - dt.timedelta(days=30)]
    white_list_device['Total Device'] = 0
    white_list_device = white_list_device.groupby('Device Type', as_index=False)['Total Device'].count()
    white_list_device = white_list_device[white_list_device['Total Device'] > minimal_device]
    raw_data = raw_data.merge(white_list_device, on=['Device Type'], indicator='Device Status', how='left')
    raw_data.drop('Total Device', axis=1)
    raw_data['Device Status'] = np.where(raw_data['Device Status'] == 'both', True, False)
    return raw_data


# App Version Check on raw data
def app_version_check(raw_data, con_engine):
    with con_engine.connect() as cursor:
        device = pd.read_sql(""" SELECT * 
                             FROM appversion """, cursor)

    device['Date Release'] = pd.to_datetime(device['Date Release'])
    last_one_month = dt.datetime.now() - dt.timedelta(days=30)

    device = device[device['Date Release'] > last_one_month]

    raw_data = raw_data.merge(device, on=['App Version'], indicator='App Version Status', how='left')
    raw_data = raw_data.drop(['Platform_y', 'Date Release'], axis=1)
    raw_data = raw_data.rename(columns={'Platform_x': 'Platform'})
    raw_data['App Version Status'] = np.where(raw_data['App Version Status'] == 'both', True, False)


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

