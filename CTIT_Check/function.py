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
import hashlib
from datetime import datetime
from .config import *


# Connection to Database
def connection_engine():
    con_engine = sa.create_engine(connection_to_database)
    return con_engine


# Check Data Platform
def install_check_platform(raw_data):
    raw_data_platform = raw_data[['Platform']]
    string = ""
    if 'android' in raw_data_platform.values:
        string += "android"
        return string
    else:
        string += "ios"
        return string

# Read CSV file
def install_read_csv(csv_filename):
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
def install_ctit_check(raw_data):
    raw_data['CTIT Status'] = False
    for index, row in raw_data.iterrows():
        if not isinstance(row['Attributed Touch Time'], str) and math.isnan(row['Attributed Touch Time']):
            installTime = datetime.strptime(row['Install Time'], '%Y-%m-%d %H:%M:%S')
            attributeTouchTime = installTime - dt.timedelta(seconds=minimal_time_check_CTIT)
        else:
            attributeTouchTime = datetime.strptime(row['Attributed Touch Time'], '%Y-%m-%d %H:%M:%S')
            installTime = datetime.strptime(row['Install Time'], '%Y-%m-%d %H:%M:%S')

        time_reduce = installTime - attributeTouchTime
        if time_reduce.total_seconds() < minimal_time_check_CTIT:
            raw_data.at[index, 'CTIT Status'] = True
    return raw_data


# Device Check on raw data
def install_device_check(raw_data, con_engine):
    with con_engine.connect() as cursor:
        white_list_device = pd.read_sql(""" SELECT "Attributed Touch Time", "Device Type" 
                                        FROM install
                                        """, cursor)

    white_list_device['Attributed Touch Time'] = pd.to_datetime(white_list_device['Attributed Touch Time'])
    white_list_device = white_list_device[
        white_list_device['Attributed Touch Time']
        > dt.datetime.now() - dt.timedelta(days=minimal_time_check_device)]

    if white_list_device.empty:
        white_list_device = raw_data[['Attributed Touch Time', 'Device Type']]
    else:
        white_list_device['Attributed Touch Time'] = pd.to_datetime(white_list_device['Attributed Touch Time'])
        white_list_device['Total Device'] = 0
        white_list_device = white_list_device.groupby('Device Type', as_index=False)['Total Device'].count()
        white_list_device = white_list_device[white_list_device['Total Device'] > minimal_device]

    raw_data = raw_data.merge(white_list_device, on=['Device Type'], indicator='Device Status', how='left')
    raw_data = raw_data.drop('Total Device', axis=1)
    raw_data['Device Status'] = np.where(raw_data['Device Status'] == 'both', True, False)

    return raw_data


# App Version Check on raw data
def install_app_version_check(raw_data, con_engine, platform):
    with con_engine.connect() as cursor:
        device = pd.read_sql(""" SELECT * 
                             FROM appversion """, cursor)

    device['Date Release'] = pd.to_datetime(device['Date Release'])
    time = dt.datetime.now() - dt.timedelta(days=minimal_time_check_app_version)

    appversion = device[device['Date Release'] > time]
    appversion = appversion[appversion['Platform'] == platform]
    raw_data = raw_data.merge(appversion, on=['App Version'], indicator='App Version Status', how='left')
    raw_data = raw_data.drop(['Platform_y', 'Date Release'], axis=1)
    raw_data = raw_data.rename(columns={'Platform_x': 'Platform'})
    raw_data['App Version Status'] = np.where(raw_data['App Version Status'] == 'both', True, False)
    return raw_data


# Get Fraud data
def install_fraud_check(raw_data):
    fraud_data = raw_data.loc[
        (raw_data['Device Status'] == False) |
        (raw_data['CTIT Status'] == True) |
        (raw_data['App Version Status'] == False)]
    fraud_data = fraud_data[['AppsFlyer ID']]
    return fraud_data


# Insert raw data to database
def install_insert_to_db(raw_data, con_engine):
    with con_engine.connect() as cursor:
        all_install_data = pd.read_sql(""" SELECT * FROM install """, cursor)
    raw_data = all_install_data.append(raw_data)
    raw_data = raw_data.drop_duplicates(keep='last')
    raw_data.to_sql(name='install', con=con_engine, if_exists='replace', index=False)


# Insert fraud data to database
def install_insert_fraud_to_db(fraud_data, con_engine):
    with con_engine.connect() as cursor:
        all_fraud_data = pd.read_sql(""" SELECT * FROM fraud """, cursor)
    fraud_data = all_fraud_data.append(fraud_data)
    fraud_data = fraud_data.drop_duplicates(keep='last')
    fraud_data.to_sql(name='fraud', con=con_engine, if_exists='replace', index=False)


def take_media_source(con_engine):
    with con_engine.connect() as cursor:
        media_source = pd.read_sql(""" SELECT "Media Source"
                                   FROM install
                                   """, cursor)

    media_source = media_source.drop_duplicates()
    media_source = media_source['Media Source'].astype(str)
    return media_source


def orderplace_read_csv(csv_filename):
    raw_data = pd.read_csv(csv_filename)
    raw_data = raw_data[['AppsFlyer ID',
                         'Event Time',
                         'Event Value',
                         'Is Retargeting']]

    raw_data[['Event Value']] = raw_data[['Event Value']].astype(str)
    return raw_data


def orderplace_find_checkout_id(raw_data):
    raw_data['Checkout ID'] = ""
    for index, value in raw_data['Event Value'].iteritems():
        position = value.find(""""af_receipt_id":""")
        s = ""
        if position < 0:
            s += '0'
        else:
            position += 16
            while (ord(value[position]) >= 48) and (ord(value[position]) <= 57) and position < len(value):
                s += value[position]
                position += 1
                if position == len(value) - 1 and (ord(value[position]) >= 48) and (ord(value[position]) <= 57):
                    s += value[position]
                    break
        s = int(s)
        raw_data.at[index, 'Checkout ID'] = s
    return raw_data


def orderplace_status_and_reason_fraud(raw_data, con_engine):
    with con_engine.connect() as cursor:
        all_fraud_data = pd.read_sql(""" SELECT * FROM fraud """, cursor)
        all_install_data = pd.read_sql(""" SELECT * FROM install """, cursor)

    all_fraud_data = all_fraud_data.drop_duplicates()
    all_install_data = all_install_data.drop_duplicates()
    raw_data = raw_data.merge(all_fraud_data, on=['AppsFlyer ID'], indicator='Fraud Status', how='left')
    raw_data['Fraud Status'] = np.where(raw_data['Fraud Status'] == 'both', True, False)

    all_install_data = all_install_data[['AppsFlyer ID',
                                         'CTIT Status',
                                         'Device Status',
                                         'App Version Status']]

    raw_data = raw_data.merge(all_install_data, on=['AppsFlyer ID'], how='left')
    raw_data['CTIT Status'] = np.where(raw_data['CTIT Status'] == True, True, False)
    raw_data['Device Status'] = np.where(raw_data['Device Status'] == True, True, False)
    raw_data['App Version Status'] = np.where(raw_data['App Version Status'] == True, True, False)

    raw_data['Fraud Reason'] = ""
    for index, row in raw_data.iterrows():
        s = ''
        if row['CTIT Status']:
            s += "CTIT Problem"
        if not row['Device Status'] and s:
            s += ", Device Problem"
        elif not row['Device Status']:
            s += "Device Problem"
        if not row['App Version Status'] and s:
            s += ", App Version Problem"
        elif not row['App Version Status']:
            s += "App Version Problem"
        raw_data.at[index, 'Fraud Reason'] = s

    raw_data = raw_data.drop(columns=['CTIT Status', 'Device Status', 'App Version Status'])
    return raw_data


def orderplace_insert_to_db(raw_data, con_engine):
    with con_engine.connect() as cursor:
        all_orderplace_data = pd.read_sql(""" SELECT * FROM orderplace """, cursor)
    raw_data = all_orderplace_data.append(raw_data)
    raw_data = raw_data.drop_duplicates(keep='last')
    raw_data.to_sql(name='orderplace', con=con_engine, if_exists='replace', index=False)


def bi_validation_read_csv(csv_filename):
    raw_data = pd.read_csv(csv_filename)
    raw_data = raw_data[['Checkout_ID',
                         'Order_SN',
                         'Username',
                         'fe_status',
                         'OrderIDBefore',
                         'PurchaseDateBefore']]
    raw_data[['Username']] = raw_data[['Username']].astype(str)
    raw_data[['OrderIDBefore']] = raw_data[['OrderIDBefore']].astype(str)
    raw_data[['OrderIDBefore']] = raw_data['OrderIDBefore'].str.replace('.0', '', regex=False)
    raw_data[['OrderIDBefore']] = raw_data['OrderIDBefore'].str.replace('nan', '', regex=False)
    return raw_data


def bi_validation_order_status_check(raw_data):
    raw_data['Order Status'] = np.where(
        raw_data['fe_status'] == 'Completed', "Valid", np.where(
            raw_data['fe_status'] == 'Cancelled', "Invalid", "Pending"))
    return raw_data


def bi_validation_buyer_status_check(raw_data):
    raw_data['Buyer Status'] = raw_data['OrderIDBefore'].isnull()
    raw_data['Buyer Status'] = np.where(raw_data['Buyer Status'] == True, "New", "Repeat")
    return raw_data


def bi_validation_hash_username(raw_data):
    raw_data['Hash Username'] = ""
    for index, value in raw_data['Username'].iteritems():
        hash_username = value.encode(encoding='UTF-8')
        raw_data.at[index, 'Hash Username'] = hashlib.md5(hash_username).hexdigest()
    return raw_data


def bi_validation_insert_to_db(raw_data, con_engine):
    with con_engine.connect() as cursor:
        all_bi_validation_data = pd.read_sql(""" SELECT * FROM validation """, cursor)
    raw_data = all_bi_validation_data.append(raw_data)
    raw_data = raw_data.drop_duplicates(keep='last', subset=['Checkout_ID', 'Order_SN'])
    raw_data.to_sql(name='validation', con=con_engine, if_exists='replace', index=False)
