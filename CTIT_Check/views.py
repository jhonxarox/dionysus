import csv
import io
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import render
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from .function import *
from .models import *
from .forms import *


def index(request):
    status = False
    if request.method == 'POST':
        form = CheckingFraudForm(request.POST)
        media_source = take_media_source(connection_engine())
        if form.is_valid():
            try:
                status = True
                media_sources = form.cleaned_data['media_sources']
                start_date = form.cleaned_data['start_date']
                end_date = form.cleaned_data['end_date']
                end_date = end_date + dt.timedelta(days=1)

                all_install_base_on_date = take_all_install_base_on_date(connection_engine(), start_date, end_date,
                                                                         media_sources)
                install_data = check_fraud_install(connection_engine(), all_install_base_on_date)
                install_total = len(install_data)
                install_fraud = len(install_data[install_data['Fraud Status'] == True])
                install_fraud_pecentage = (install_fraud / install_total) * 100
                install_fraud_pecentage = round(install_fraud_pecentage, 2)

                all_purchase_base_on_date = download_report(connection_engine(), start_date,
                                                            end_date, media_sources)
                purchase_total = len(all_purchase_base_on_date)
                purchase_fraud = len(all_purchase_base_on_date[all_purchase_base_on_date['Fraud Status'] == True])
                purchase_fraud_pecentage = (purchase_fraud / purchase_total) * 100
                purchase_fraud_pecentage = round(purchase_fraud_pecentage, 2)

                data = download_report(connection_engine(), start_date, end_date, media_sources)

                # -------------------------------------------SUSPECTED FRAUD-----------------------------------------

                suspected_fraud = data.loc[data['Fraud Status'] == True]

                suspec_valid = suspected_fraud.loc[suspected_fraud['Checkout Status'] == "Valid"]
                suspec_valid_new = len(suspec_valid.loc[suspec_valid['Buyer Status'] == "New"])
                suspec_valid_repeat = len(suspec_valid.loc[suspec_valid['Buyer Status'] == "Repeat"])

                suspec_invalid = suspected_fraud.loc[suspected_fraud['Checkout Status'] == "Invalid"]
                suspec_invalid_new = len(suspec_invalid.loc[suspec_invalid['Buyer Status'] == "New"])
                suspec_invalid_repeat = len(suspec_invalid.loc[suspec_invalid['Buyer Status'] == "Repeat"])

                suspec_pending = suspected_fraud.loc[suspected_fraud['Checkout Status'] == "Pending"]
                suspec_pending_new = len(suspec_pending.loc[suspec_pending['Buyer Status'] == "New"])
                suspec_pending_repeat = len(suspec_pending.loc[suspec_pending['Buyer Status'] == "Repeat"])

                # -------------------------------------------END SUSPECTED FRAUD----------------------------------------

                # -------------------------------------------TRUSTED INSTALL--------------------------------------------
                trusted_install = data.loc[data['Fraud Status'] == False]

                trust_valid = trusted_install.loc[trusted_install['Checkout Status'] == "Valid"]
                trust_valid_new = len(trust_valid.loc[trust_valid['Buyer Status'] == "New"])
                trust_valid_repeat = len(trust_valid.loc[trust_valid['Buyer Status'] == "Repeat"])

                trust_invalid = trusted_install.loc[trusted_install['Checkout Status'] == "Invalid"]
                trust_invalid_new = len(trust_invalid.loc[trust_invalid['Buyer Status'] == "New"])
                trust_invalid_repeat = len(trust_invalid.loc[trust_invalid['Buyer Status'] == "Repeat"])

                trust_pending = trusted_install.loc[trusted_install['Checkout Status'] == "Pending"]
                trust_pending_new = len(trust_pending.loc[trust_pending['Buyer Status'] == "New"])
                trust_pending_repeat = len(trust_pending.loc[trust_pending['Buyer Status'] == "Repeat"])

                # -------------------------------------------END TRUSTED INSTALL----------------------------------------

                start_date = start_date.strftime('%d-%m-%Y')
                end_date = end_date - dt.timedelta(days=1)
                end_date = end_date.strftime('%d-%m-%Y')
                return render(request, 'index.html', {'status': status,
                                                      'start_date': start_date,
                                                      'end_date': end_date,

                                                      'install_fraud': install_fraud,
                                                      'install_fraud_pecentage': install_fraud_pecentage,
                                                      'install_total': install_total,

                                                      'purchase_fraud': purchase_fraud,
                                                      'purchase_fraud_pecentage': purchase_fraud_pecentage,
                                                      'purchase_total': purchase_total,

                                                      'trust_valid_new': trust_valid_new,
                                                      'trust_valid_repeat': trust_valid_repeat,
                                                      'trust_invalid_new': trust_invalid_new,
                                                      'trust_invalid_repeat': trust_invalid_repeat,
                                                      'trust_pending_new': trust_pending_new,
                                                      'trust_pending_repeat': trust_pending_repeat,

                                                      'suspec_valid_new': suspec_valid_new,
                                                      'suspec_valid_repeat': suspec_valid_repeat,
                                                      'suspec_invalid_new': suspec_invalid_new,
                                                      'suspec_invalid_repeat': suspec_invalid_repeat,
                                                      'suspec_pending_new': suspec_pending_new,
                                                      'suspec_pending_repeat': suspec_pending_repeat,

                                                      'media_source': media_source,
                                                      'media_sources': media_sources,

                                                      'message': "valid true"})

            except Exception as e:
                return render(request, 'index.html', {'error': str(e),
                                                      'media_source': media_source,
                                                      'status': status,
                                                      'message': "valid false"})

        else:
            status = True
            media_source = take_media_source(connection_engine())
            return render(request, 'index.html', {'form': form,
                                                  'media_source': media_source,
                                                  'status': status,
                                                  'message': "nod valid"})
    else:
        status = False
        media_source = take_media_source(connection_engine())
        return render(request, 'index.html', {'status': status,
                                              'media_source': media_source})


def upload_install(request):
    con_engine = connection_engine()
    all_config_data = get_config(con_engine)
    for index, row in all_config_data.iterrows():
        if row['Config'] == "CTIT Time":
            CTIT_Time = row.at['Value']
            CTIT_status = row.at['Use']
        elif row['Config'] == "Device Time":
            Device_Time = row.at['Value']
            device_status = row.at['Use']
        elif row['Config'] == "App Time":
            App_Time = row.at['Value']
            app_status = row.at['Use']
        elif row['Config'] == "Minimal Device":
            Minimal_Device = row.at['Value']

    if "GET" == request.method:
        status = False
        return render(request, 'upload-install.html', {'status': status,
                                                       'CTIT_Time': CTIT_Time,
                                                       'CTIT_status': CTIT_status,
                                                       'Device_Time': Device_Time,
                                                       'device_status': device_status,
                                                       'App_Time': App_Time,
                                                       'app_status': app_status,
                                                       'Minimal_Device': Minimal_Device,})

    csv_file = request.FILES['csv_file']

    if not (csv_file.name.endswith('.csv')):
        return render(request, 'upload-install.html', {'CTIT_Time': CTIT_Time,
                                                       'CTIT_status': CTIT_status,
                                                       'Device_Time': Device_Time,
                                                       'device_status': device_status,
                                                       'App_Time': App_Time,
                                                       'app_status': app_status,
                                                       'Minimal_Device': Minimal_Device,
                                                       'message': "Please Upload CSV file!"})

    raw_data = install_read_csv(csv_file)
    platform = install_check_platform(raw_data)
    ctit_result = install_ctit_check(raw_data, con_engine)
    device_result = install_device_check(ctit_result, con_engine)
    data = install_app_version_check(device_result, con_engine, platform)
    fraud_data = install_fraud_check(data)
    install_insert_to_db(data, con_engine)
    install_insert_fraud_to_db(fraud_data, con_engine)
    update_if_install_uploaded(con_engine)
    status = True
    return render(request, 'upload-install.html', {'status': status,
                                                   'CTIT_Time': CTIT_Time,
                                                   'CTIT_status': CTIT_status,
                                                   'Device_Time': Device_Time,
                                                   'device_status': device_status,
                                                   'App_Time': App_Time,
                                                   'app_status': app_status,
                                                   'Minimal_Device': Minimal_Device,
                                                   'message': "Upload Success"})


def upload_orderplace(request):
    if "GET" == request.method:
        status = False
        return render(request, 'upload-orderplace.html', {'status': status})

    csv_file = request.FILES['csv_file']
    # status = request.POST.getlist['status']
    form = uploadOrderplace(request.POST)
    if not (csv_file.name.endswith('.csv')):
        return render(request, 'upload-orderplace.html', {'message': "Please Upload CSV file!"})

    if not form.is_valid():
        status = False
        return render(request, 'upload-orderplace.html', {'status': status})

    download = form.cleaned_data['download']
    con_engine = connection_engine()
    raw_data = orderplace_read_csv(csv_file)
    checkout = orderplace_find_checkout_id(raw_data)
    status_reason = orderplace_status_and_reason_fraud(checkout, con_engine)
    orderplace_insert_to_db(status_reason, con_engine)
    download_file = orderplace_checkout_id(checkout)
    response = HttpResponse(download_file.to_csv(index=False), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=checkout_id_%s.csv' % csv_file
    status = True

    if download:
        return response
    else:
        return render(request, 'upload-orderplace.html',
                      {'status': status, 'message': "Upload Success", 'respone': response})


def upload_bi_validation(request):
    if "GET" == request.method:
        status = False
        return render(request, 'upload-validation.html', {'status': status})

    csv_file = request.FILES['csv_file']

    if not (csv_file.name.endswith('.csv')):
        return render(request, 'upload-validation.html', {'message': "Please Upload CSV file!"})

    con_engine = connection_engine()
    raw_data = bi_validation_read_csv(csv_file)
    order_status = bi_validation_order_status_check(raw_data)
    buyer_status = bi_validation_buyer_status_check(order_status)
    hash_username = bi_validation_hash_username(buyer_status)
    bi_validation_insert_to_db(hash_username, con_engine)
    status = True
    return render(request, 'upload-validation.html', {'status': status, 'message': "Upload Success"})


def alldata(request):
    data = Install.objects.all()
    paginator = Paginator(data, 100)
    page = request.GET.get('page')
    contacts = paginator.get_page(page)
    # head = pd.DataFrame(list(output.values()))
    # body = pd.DataFrame(list())
    return render(request, 'alldata.html', {'data': contacts})


def download_file_all(request):
    if request.method == 'POST':
        form = download(request.POST)
        if form.is_valid():
            media = form.cleaned_data['media_download']
            start_date = form.cleaned_data['start_date_download']
            end_date = form.cleaned_data['end_date_download']
            download_file = download_report(connection_engine(), start_date, end_date, media)
            response = HttpResponse(download_file.to_csv(index=False), content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=report.csv'
            return response


def config(request):
    con_engine = connection_engine()
    all_config_data = get_config(con_engine)
    app_platform = take_app_platform(con_engine)
    if "GET" == request.method:
        status = False
        for index, row in all_config_data.iterrows():
            if row['Config'] == "CTIT Time":
                CTIT_Time = row.at['Value']
                CTIT_status = row.at['Use']
            elif row['Config'] == "Device Time":
                Device_Time = row.at['Value']
                device_status = row.at['Use']
            elif row['Config'] == "App Time":
                App_Time = row.at['Value']
                app_status = row.at['Use']
            elif row['Config'] == "Minimal Device":
                Minimal_Device = row.at['Value']
        return render(request, 'config.html', {'CTIT_Time': CTIT_Time,
                                               'CTIT_status': CTIT_status,
                                               'Device_Time': Device_Time,
                                               'device_status': device_status,
                                               'App_Time': App_Time,
                                               'app_status': app_status,
                                               'Minimal_Device': Minimal_Device,
                                               'app_platform': app_platform,
                                               'status': status})
    elif "POST" == request.method:
        status = True
        form = updateConfig(request.POST)
        if form.is_valid():
            CTIT_Time = form.cleaned_data['ctit']
            CTIT_status = form.cleaned_data['ctit_status']
            Device_Time = form.cleaned_data['device']
            device_status = form.cleaned_data['device_status']
            App_Time = form.cleaned_data['app']
            app_status = form.cleaned_data['app_status']
            Minimal_Device = form.cleaned_data['device_number']
            for index, row in all_config_data.iterrows():
                if row['Config'] == "CTIT Time":
                    all_config_data.at[index, 'Value'] = CTIT_Time
                    all_config_data.at[index, 'Use'] = CTIT_status

                elif row['Config'] == "Device Time":
                    all_config_data.at[index, 'Value'] = Device_Time
                    all_config_data.at[index, 'Use'] = device_status

                elif row['Config'] == "App Time":
                    all_config_data.at[index, 'Value'] = App_Time
                    all_config_data.at[index, 'Use'] = app_status

                elif row['Config'] == "Minimal Device":
                    all_config_data.at[index, 'Value'] = Minimal_Device

            update_config(con_engine, all_config_data)
            return render(request, 'config.html', {'CTIT_Time': CTIT_Time,
                                                   'CTIT_status': CTIT_status,
                                                   'Device_Time': Device_Time,
                                                   'device_status': device_status,
                                                   'App_Time': App_Time,
                                                   'app_status': app_status,
                                                   'Minimal_Device': Minimal_Device,
                                                   'app_platform': app_platform,
                                                   'status': True})
        else:
            for index, row in all_config_data.iterrows():
                if row['Config'] == "CTIT Time":
                    CTIT_Time = row.at['Value']
                    CTIT_status = row.at['Use']
                elif row['Config'] == "Device Time":
                    Device_Time = row.at['Value']
                    device_status = row.at['Use']
                elif row['Config'] == "App Time":
                    App_Time = row.at['Value']
                    app_status = row.at['Use']
                elif row['Config'] == "Minimal Device":
                    Minimal_Device = row.at['Value']
            return render(request, 'config.html', {'CTIT_Time': CTIT_Time,
                                                   'CTIT_status': CTIT_status,
                                                   'Device_Time': Device_Time,
                                                   'device_status': device_status,
                                                   'App_Time': App_Time,
                                                   'app_status': app_status,
                                                   'Minimal_Device': Minimal_Device,
                                                   'app_platform': app_platform,
                                                   'status': status})
    else:
        return render(request, 'config.html', {})

def app_update(request):
    con_engine = connection_engine()
    all_config_data = get_config(con_engine)
    app_platform = take_app_platform(con_engine)
    for index, row in all_config_data.iterrows():
        if row['Config'] == "CTIT Time":
            CTIT_Time = row.at['Value']
            CTIT_status = row.at['Use']
        elif row['Config'] == "Device Time":
            Device_Time = row.at['Value']
            device_status = row.at['Use']
        elif row['Config'] == "App Time":
            App_Time = row.at['Value']
            app_status = row.at['Use']
        elif row['Config'] == "Minimal Device":
            Minimal_Device = row.at['Value']
    if "POST" == request.method:
        form = addAppVersion(request.POST)
        if form.is_valid():
            platform = form.cleaned_data['app_platform']
            version = form.cleaned_data['app_version']
            date = form.cleaned_data['release_date']
            add_new_app_version(con_engine, platform, version, date)

            return render(request, 'config.html', {'CTIT_Time': CTIT_Time,
                                               'CTIT_status': CTIT_status,
                                               'Device_Time': Device_Time,
                                               'device_status': device_status,
                                               'App_Time': App_Time,
                                               'app_status': app_status,
                                               'Minimal_Device': Minimal_Device,
                                               'app_platform': app_platform})

        return render(request, 'config.html', {'CTIT_Time': CTIT_Time,
                                               'CTIT_status': CTIT_status,
                                               'Device_Time': Device_Time,
                                               'device_status': device_status,
                                               'App_Time': App_Time,
                                               'app_status': app_status,
                                               'Minimal_Device': Minimal_Device,
                                               'app_platform': app_platform})

    return render(request, 'config.html', {'CTIT_Time': CTIT_Time,
                                               'CTIT_status': CTIT_status,
                                               'Device_Time': Device_Time,
                                               'device_status': device_status,
                                               'App_Time': App_Time,
                                               'app_status': app_status,
                                               'Minimal_Device': Minimal_Device,
                                               'app_platform': app_platform})