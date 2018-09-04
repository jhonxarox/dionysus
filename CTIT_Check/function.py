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
import ast
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
def install_ctit_check(raw_data, con_engine):
    with con_engine.connect() as cursor:
        all_config_data = pd.read_sql(""" SELECT * FROM config """, cursor)

    for index, row in all_config_data.iterrows():
        if row['Config'] == "CTIT Time":
            minimal_time_check_CTIT = row.at['Value']
            ctit_status = row.at['Use']
            break

    raw_data['CTIT Status'] = False
    if ctit_status:
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
        all_config_data = pd.read_sql(""" SELECT * FROM config """, cursor)

    for index, row in all_config_data.iterrows():
        if row['Config'] == "Device Time":
            minimal_time_check_device = row.at['Value']
            device_status = row.at['Use']
        elif row['Config'] == "Minimal Device":
            minimal_device = row.at['Value']

    if device_status:
        white_list_device['Attributed Touch Time'] = pd.to_datetime(white_list_device['Attributed Touch Time'])
        white_list_device = white_list_device[
            white_list_device['Attributed Touch Time']
            > dt.datetime.now() - dt.timedelta(days=minimal_time_check_device)]

        if white_list_device.empty:
            white_list_device = raw_data[['Attributed Touch Time', 'Device Type']]

        white_list_device['Attributed Touch Time'] = pd.to_datetime(white_list_device['Attributed Touch Time'])
        white_list_device['Total Device'] = 0
        white_list_device = white_list_device.groupby('Device Type', as_index=False)['Total Device'].count()
        white_list_device = white_list_device[white_list_device['Total Device'] > minimal_device]

        raw_data = raw_data.merge(white_list_device, on=['Device Type'], indicator='Device Status', how='left')
        raw_data = raw_data.drop('Total Device', axis=1)
        raw_data['Device Status'] = np.where(raw_data['Device Status'] == 'both', False, True)
    else:
        raw_data['Device Status'] = False

    return raw_data


# App Version Check on raw data
def install_app_version_check(raw_data, con_engine, platform):
    with con_engine.connect() as cursor:
        appversion = pd.read_sql(""" SELECT * 
                             FROM appversion """, cursor)
        all_config_data = pd.read_sql(""" SELECT * FROM config """, cursor)

    for index, row in all_config_data.iterrows():
        if row['Config'] == "App Time":
            App_Time = row.at['Value']
            app_status = row.at['Use']

    if app_status:
        time = pd.to_datetime(raw_data['Install Time'])
        time = pd.to_datetime(time)
        time = time.sort_values()
        time = time.reset_index(drop=True)

        start = time.iloc[0].to_pydatetime()
        end = time.iloc[-1].to_pydatetime()

        appversion = appversion[appversion['Platform'] == platform]
        appversion['Date Release'] = pd.to_datetime(appversion['Date Release'])
        appversion = appversion.sort_values('Date Release')
        appversion = appversion.reset_index(drop=True)

        appversion_on_range = appversion[
            (appversion['Date Release'] <= end) &
            (appversion['Date Release'] >= start - dt.timedelta(days=App_Time))]

        if appversion_on_range.empty:
            appversion = appversion.tail(1)
        else:
            appversion = appversion_on_range

        raw_data = raw_data.merge(appversion, on=['App Version'], indicator='App Version Status', how='left')
        raw_data = raw_data.drop(['Platform_y', 'Date Release'], axis=1)
        raw_data = raw_data.rename(columns={'Platform_x': 'Platform'})
        raw_data['App Version Status'] = np.where(raw_data['App Version Status'] == 'both', False, True)
    else:
        raw_data['App Version Status'] = False
    return raw_data


# Get Fraud data
def install_fraud_check(raw_data):
    fraud_data = raw_data.loc[
        (raw_data['Device Status'] == True) |
        (raw_data['CTIT Status'] == True) |
        (raw_data['App Version Status'] == True)]
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
    fraud_data = fraud_data.drop_duplicates(keep='last', subset=['AppsFlyer ID'])
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
                         'Is Retargeting',
                         ]]

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
            while (ord(value[position]) >= 48) and (ord(value[position]) <= 57) and (position < len(value)):
                s += value[position]
                position += 1
                if (position == len(value) - 1) and (ord(value[position]) >= 48) and (ord(value[position]) <= 57):
                    s += value[position]
                    break
        s = int(s)
        raw_data.at[index, 'Checkout ID'] = s
    return raw_data


def orderplace_status_and_reason_fraud(raw_data, con_engine):
    with con_engine.connect() as cursor:
        all_fraud_data = pd.read_sql(""" SELECT * FROM fraud """, cursor)
        all_install_data = pd.read_sql(""" SELECT * FROM install """, cursor)

    raw_data = raw_data.merge(all_fraud_data, on=['AppsFlyer ID'], indicator='Fraud Status', how='left')
    raw_data['Fraud Status'] = np.where(raw_data['Fraud Status'] == 'both', True, False)

    all_install_data = all_install_data[['AppsFlyer ID',
                                         'CTIT Status',
                                         'Device Status',
                                         'App Version Status']]

    raw_data = raw_data.merge(all_install_data, on=['AppsFlyer ID'], how='left')
    raw_data[['CTIT Status']] = raw_data['CTIT Status'].fillna(False)
    raw_data[['Device Status']] = raw_data['Device Status'].fillna(False)
    raw_data[['App Version Status']] = raw_data['App Version Status'].fillna(False)

    raw_data['Fraud Reason'] = ""
    for index, row in raw_data.iterrows():
        s = ''
        if row['CTIT Status'] and s:
            s += "CTIT Problem"
        elif row['CTIT Status']:
            s += "CTIT Problem"

        if row['Device Status'] and s:
            s += ", Device Problem"
        elif row['Device Status']:
            s += "Device Problem"

        if row['App Version Status'] and s:
            s += ", App Version Problem"
        elif row['App Version Status']:
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


def orderplace_checkout_id(raw_data):
    checkout_id = raw_data['Checkout ID']
    return checkout_id


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
    raw_data['Checkout Status'] = np.where(
        raw_data['fe_status'] == 'Completed', "Valid", np.where(
            raw_data['fe_status'] == 'Cancelled', "Invalid", "Pending"))
    return raw_data


def bi_validation_buyer_status_check(raw_data):
    raw_data['Buyer Status'] = raw_data['OrderIDBefore'].isnull() | raw_data['PurchaseDateBefore'].isnull()
    raw_data['Buyer Status'] = np.where(raw_data['Buyer Status'], "New", "Repeat")
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


def take_new_buyer_base_on_date(con_engine, start, end):
    start = start.isoformat(' ')
    end = end.isoformat(' ')

    with con_engine.connect() as cursor:
        all_validation_data = pd.read_sql(""" SELECT * FROM validation """, cursor)
        all_orderplace_data = pd.read_sql(""" SELECT * FROM orderplace """, cursor)

    event_time = all_orderplace_data[['Checkout ID', 'Event Time', 'Fraud Status']]
    all_validation_data = event_time.join(all_validation_data, lsuffix='Checkout ID', rsuffix='Checkout_ID')
    all_validation_data = all_validation_data.drop(columns='Checkout_ID')

    all_validation_data[['Event Time']] = pd.to_datetime(all_validation_data['Event Time'])
    all_validation_data = all_validation_data[
        (all_validation_data['Event Time'] >= start) &
        (all_validation_data['Event Time'] <= end) &
        (all_validation_data['Buyer Status'] == "New")
        ]

    return all_validation_data


def check_new_buyer(con_engine, data):
    with con_engine.connect() as cursor:
        all_install_data = pd.read_sql(""" SELECT * FROM install """, cursor)
        all_orderplace_data = pd.read_sql(""" SELECT * FROM orderplace """, cursor)

    new_buyer = data[data['Buyer Status'] == "New"]
    not_fraud_orderplace = all_orderplace_data[all_orderplace_data['Fraud Status'] == False]
    not_fraud_orderplace = not_fraud_orderplace.merge(all_install_data, how='left')
    not_fraud_orderplace = not_fraud_orderplace[not_fraud_orderplace['Attributed Touch Time'].notnull() == True]

    new_buyer = new_buyer


def take_all_install_base_on_date(con_engine, start, end, media):
    start = start.isoformat(' ')
    end = end.isoformat(' ')
    media = pd.DataFrame({'Media Source': media})
    # print(media)
    with con_engine.connect() as cursor:
        all_install_data = pd.read_sql(""" SELECT * FROM install """, cursor)

    all_install_data = all_install_data[
        (all_install_data['Install Time'] >= start) &
        (all_install_data['Install Time'] <= end)
        ]

    all_install_data = all_install_data.merge(media, on=['Media Source'], indicator='Check', how='left')
    all_install_data['Check'] = np.where(all_install_data['Check'] == 'both', True, False)
    all_install_data = all_install_data[all_install_data['Check'] == True]
    all_install_data = all_install_data.drop('Check', axis=1)

    return all_install_data


def check_fraud_install(con_engine, data):
    with con_engine.connect() as cursor:
        all_fraud_data = pd.read_sql(""" SELECT * FROM fraud """, cursor)

    data = data.merge(all_fraud_data, indicator='Fraud Status', how='left')
    data['Fraud Status'] = np.where(data['Fraud Status'] == 'both', True, False)
    return data


# def take_all_purchase_base_on_date(con_engine, start, end):
#     start = start.isoformat(' ')
#     end = end.isoformat(' ')
#
#     with con_engine.connect() as cursor:
#         all_orderplace_data = pd.read_sql(""" SELECT * FROM orderplace """, cursor)
#
#     all_orderplace_data = all_orderplace_data[
#         (all_orderplace_data['Event Time'] >= start) &
#         (all_orderplace_data['Event Time'] <= end)
#         ]
#
#     return all_orderplace_data


def download_report(con_engine, start, end, media):
    if isinstance(start, str) and isinstance(end, str) and isinstance(media, str):
        start = datetime.strptime(start, '%d-%m-%Y')
        end = datetime.strptime(end, '%d-%m-%Y')
        media = ast.literal_eval(media)
        media = pd.DataFrame({'Media Source': media})
        # print(start)
        # print(end)
        # print(media)
        # media = pd.Series(media)
    else:
        start = start.isoformat(' ')
        end = end.isoformat(' ')
        media = pd.DataFrame({'Media Source': media})

    with con_engine.connect() as cursor:
        all_install_data = pd.read_sql(""" SELECT * FROM install """, cursor)
        all_orderplace_data = pd.read_sql(""" SELECT * FROM orderplace """, cursor)
        all_validation_data = pd.read_sql(""" SELECT * FROM validation """, cursor)

    table = all_orderplace_data.join(all_validation_data)
    table = table.drop(columns='Checkout_ID')

    install_data = all_install_data.drop(columns='Is Retargeting')
    table = table.merge(install_data, how='left', on='AppsFlyer ID')
    table = table[['AppsFlyer ID',
                   'Attributed Touch Time',
                   'Install Time',
                   'Event Time',
                   'Event Value',
                   'Media Source',
                   'Platform',
                   'Device Type',
                   'App Version',
                   'Checkout ID',
                   'Buyer Status',
                   'Checkout Status',
                   'OrderIDBefore',
                   'Order_SN',
                   'PurchaseDateBefore',
                   'fe_status',
                   'Campaign',
                   'Campaign ID',
                   'Site ID',
                   'Original URL',
                   'Fraud Status',
                   'Fraud Reason']]
    # print(table)
    table = table.drop_duplicates(subset=['AppsFlyer ID', 'Checkout ID', 'Order_SN'])
    print(table)
    table['Event Time'] = pd.to_datetime(table['Event Time'])
    # print(table)
    table = table[
        (table['Event Time'] >= start) &
        (table['Event Time'] <= end)
        ]
    # print(table)
    table = table.merge(media, on=['Media Source'], indicator='Check', how='left')
    # print(table)
    table['Check'] = np.where(table['Check'] == 'both', True, False)
    # print(table)
    table = table[table['Check'] == True]
    table = table.drop('Check', axis=1)
    # print(table)
    # writer = pd.ExcelWriter('report.xlsx')
    # table.to_excel(writer, 'Data', index=False)

    return table


def update_if_install_uploaded(con_engine):
    with con_engine.connect() as cursor:
        all_fraud_data = pd.read_sql(""" SELECT * FROM fraud """, cursor)
        all_install_data = pd.read_sql(""" SELECT * FROM install """, cursor)
        all_orderplace_data = pd.read_sql(""" SELECT * FROM orderplace """, cursor)

    all_orderplace_data = all_orderplace_data.drop(columns=['Fraud Status', 'Fraud Reason'])
    all_orderplace_data = all_orderplace_data.merge(all_fraud_data, on=['AppsFlyer ID'], indicator='Fraud Status',
                                                    how='left')
    all_orderplace_data['Fraud Status'] = np.where(all_orderplace_data['Fraud Status'] == 'both', True, False)

    all_install_data = all_install_data[['AppsFlyer ID',
                                         'CTIT Status',
                                         'Device Status',
                                         'App Version Status']]

    all_orderplace_data = all_orderplace_data.merge(all_install_data, on=['AppsFlyer ID'], how='left')
    all_orderplace_data[['CTIT Status']] = all_orderplace_data['CTIT Status'].fillna(False)
    all_orderplace_data[['Device Status']] = all_orderplace_data['Device Status'].fillna(False)
    all_orderplace_data[['App Version Status']] = all_orderplace_data['App Version Status'].fillna(False)

    all_orderplace_data['Fraud Reason'] = ""
    for index, row in all_orderplace_data.iterrows():
        s = ''
        if row['CTIT Status'] and s:
            s += "CTIT Problem"
        elif row['CTIT Status']:
            s += "CTIT Problem"

        if row['Device Status'] and s:
            s += ", Device Problem"
        elif row['Device Status']:
            s += "Device Problem"

        if row['App Version Status'] and s:
            s += ", App Version Problem"
        elif row['App Version Status']:
            s += "App Version Problem"

        all_orderplace_data.at[index, 'Fraud Reason'] = s

    all_orderplace_data = all_orderplace_data.drop(columns=['CTIT Status', 'Device Status', 'App Version Status'])
    # all_orderplace_data = all_orderplace_data.append(all_orderplace_data)
    all_orderplace_data = all_orderplace_data.drop_duplicates(keep='last')
    all_orderplace_data.to_sql(name='orderplace', con=con_engine, if_exists='replace', index=False)


def get_config(con_engine):
    with con_engine.connect() as cursor:
        all_config_data = pd.read_sql(""" SELECT * FROM config """, cursor)
    return all_config_data


def update_config(con_engine, new_all_config_data):
    with con_engine.connect() as cursor:
        all_config_data = pd.read_sql(""" SELECT * FROM config """, cursor)
    new_all_config_data = all_config_data.append(new_all_config_data)
    new_all_config_data = new_all_config_data.drop_duplicates(subset='Config', keep='last')
    new_all_config_data.to_sql(name='config', con=con_engine, if_exists='replace', index=False)


def take_app_platform(con_engine):
    with con_engine.connect() as cursor:
        appversion = pd.read_sql(""" SELECT * 
                                     FROM appversion """, cursor)
    appversion = appversion.drop(columns=['App Version', 'Date Release']).drop_duplicates(
        subset='Platform').reset_index(drop=True)
    appversion = appversion['Platform'].astype(str)
    return appversion


def add_new_app_version(con_engine, platform, version, date):
    date = date.replace(tzinfo=None)
    new = {'Platform': platform, 'App Version': version, 'Date Release': date}
    with con_engine.connect() as cursor:
        appversion = pd.read_sql(""" SELECT * 
                                        FROM appversion """, cursor)
    appversion = appversion.append(new, ignore_index=True)
    appversion = appversion.drop_duplicates(keep='last', subset=['Platform', 'App Version'])
    appversion.to_sql(name='appversion', con=con_engine, if_exists='replace', index=False)
