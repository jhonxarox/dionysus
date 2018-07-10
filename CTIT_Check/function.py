# -*- coding: utf-8 -*-
"""
Created on Mon Jul  2 19:23:16 2018

@author: jhon.harry
"""

import pandas as pd
import numpy as np
import time
import datetime as dt
import sqlalchemy as sa
from datetime import datetime

start = time.time()
# Connection to Database
con_engine = sa.create_engine('postgresql://postgres:admin123@localhost/FraudTest_db')

# Read CSV file
raw_data = pd.read_csv("com.shopee.id_installs_2018-07-03_2018-07-03_UHIFP_Asia_Singapore.csv")
appversion_data = pd.read_csv("appversion.csv")

raw_data['CTIT Status'] = False

for index, row in raw_data.iterrows() :
    attributeTouchTime =  datetime.strptime(row['Attributed Touch Time'], '%Y-%m-%d %H:%M:%S')
    installTime = datetime.strptime(row['Install Time'], '%Y-%m-%d %H:%M:%S')
    time_reduce = installTime - attributeTouchTime
    if time_reduce.total_seconds() < 21 :
        raw_data.at[index, 'CTIT Status'] = True

white_list_device = raw_data[['Device Type']]
white_list_device['Total Device'] = 0
white_list_device = white_list_device.groupby('Device Type', as_index = False)['Total Device'].count()
white_list_device = white_list_device[white_list_device['Total Device'] > 10]

raw_data = raw_data.merge(white_list_device, on = ['Device Type'], indicator = 'Device Status' , how = 'left')
raw_data.drop('Total Device', axis=1)
raw_data['Device Status'] = np.where(raw_data['Device Status'] == 'both', True, False)

fraud_data = raw_data.loc[(raw_data['Device Status'] == False) & (raw_data['CTIT Status'] == True)]
fraud_data = fraud_data[['AppsFlyer ID']]

print("Insert to Database")
raw_data.to_sql(name = 'install', con = con_engine, if_exists = 'replace', index = False)
fraud_data.to_sql(name = 'fraud', con = con_engine, if_exists = 'replace', index = False)
appversion_data.to_sql(name = 'appversion', con = con_engine, if_exists = 'replace', index = False)

platform='android'

with con_engine.connect() as cursor :
    device = pd.read_sql(""" SELECT * FROM appversion 
                                        WHERE "Platform" LIKE '%s'
                                        """ %platform , cursor)

device['Date Release'] = pd.to_datetime(device['Date Release'])
last_one_month = dt.datetime.now() - dt.timedelta(days = 30)

device = device[device['Date Release'] > last_one_month]

stop = time.time()

str(dt.timedelta(seconds=stop-start))