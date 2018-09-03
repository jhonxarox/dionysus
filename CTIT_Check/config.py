import pandas as pd
# from .function import connection_engine

# Connection to Database
# 'postgresql://username:password@host/database_name'
connection_to_database = 'postgresql://postgres:admin123@localhost/FraudTest_db'

# with connection_engine().connect() as cursor :
#     all_config_data = pd.read_sql(""" SELECT * FROM config """, cursor)
#     for index, row in all_config_data.iterrows():
#         if row['Config']=="CTIT Time":
#             minimal_time_check_CTIT = row.at['Value']
#             break
#         elif row['Config']=="Device Time":
#             minimal_time_check_device = row.at['Value']
#             break
#         elif row['Config']=="App Time":
#             minimal_time_check_app_version = row.at['Value']
#             break
#         else:
#             minimal_device = row.at['Value']

# Minimal device
# minimal_device = 10

# Minimal Time on Check CTIT (seconds)
# minimal_time_check_CTIT = 20

# Minimal Days for Device Check
# minimal_time_check_device = 60

# Minimal Days for App Version
# minimal_time_check_app_version = 7

