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

                all_install_base_on_date = take_all_install_base_on_date(connection_engine(), start_date, end_date)
                install_data = check_fraud_install(connection_engine(), all_install_base_on_date)
                install_total = len(install_data)
                install_fraud = len(install_data[install_data['Fraud Status'] == True])
                install_fraud_pecentage = (install_fraud / install_total) * 100
                install_fraud_pecentage = round(install_fraud_pecentage, 2)

                all_orderplace_base_on_date = take_all_orderplace_base_on_date(connection_engine(), start_date,
                                                                               end_date)
                orderplace_total = len(all_orderplace_base_on_date)
                orderplace_fraud = len(all_orderplace_base_on_date[all_orderplace_base_on_date['Fraud Status'] == True])
                orderplace_fraud_pecentage = (orderplace_fraud / orderplace_total) * 100
                orderplace_fraud_pecentage = round(orderplace_fraud_pecentage, 2)

                all_new_buyer_base_on_date = take_new_buyer_base_on_date(connection_engine(), start_date, end_date)
                new_buyer_total = len(all_new_buyer_base_on_date)

                new_buyer_valid_total = len(
                    all_new_buyer_base_on_date[all_new_buyer_base_on_date['Checkout Status'] == "Valid"])
                new_buyer_valid_total_percentage = (new_buyer_valid_total / new_buyer_total) * 100
                new_buyer_valid_total_percentage = round(new_buyer_valid_total_percentage, 2)

                new_buyer_invalid_total = len(
                    all_new_buyer_base_on_date[all_new_buyer_base_on_date['Checkout Status'] == "Invalid"])
                new_buyer_invalid_percentage = (new_buyer_invalid_total / new_buyer_total) * 100
                new_buyer_invalid_percentage = round(new_buyer_invalid_percentage, 2)

                start_date = start_date.strftime('%d-%m-%Y')
                end_date = end_date.strftime('%d-%m-%Y')
                return render(request, 'index.html', {'status': status,
                                                      'start_date': start_date,
                                                      'end_date': end_date,

                                                      'install_fraud': install_fraud,
                                                      'install_fraud_pecentage': install_fraud_pecentage,
                                                      'install_total': install_total,

                                                      'orderplace_fraud': orderplace_fraud,
                                                      'orderplace_fraud_pecentage': orderplace_fraud_pecentage,
                                                      'orderplace_total': orderplace_total,

                                                      'new_buyer_total': new_buyer_total,
                                                      'new_buyer_valid_total': new_buyer_valid_total,
                                                      'new_buyer_valid_total_percentage': new_buyer_valid_total_percentage,
                                                      'new_buyer_invalid_total': new_buyer_invalid_total,
                                                      'new_buyer_invalid_percentage': new_buyer_invalid_percentage,

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


def elements(request):
    return render(request, 'elements.html', {})


def charts(request):
    return render(request, 'charts.html', {})


def panels(request):
    return render(request, 'panels.html', {})


def upload_install(request):
    if "GET" == request.method:
        status = False
        return render(request, 'upload-install.html', {'status': status})

    csv_file = request.FILES['csv_file']

    if not (csv_file.name.endswith('.csv')):
        return render(request, 'upload-install.html', {'message': "Please Upload CSV file!"})

    con_engine = connection_engine()
    raw_data = install_read_csv(csv_file)
    platform = install_check_platform(raw_data)
    ctit_result = install_ctit_check(raw_data)
    device_result = install_device_check(ctit_result, con_engine)
    data = install_app_version_check(device_result, con_engine, platform)
    fraud_data = install_fraud_check(data)
    install_insert_to_db(data, con_engine)
    install_insert_fraud_to_db(fraud_data, con_engine)
    status = True
    return render(request, 'upload-install.html', {'status': status, 'message': "Upload Success"})


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
            output = io.BytesIO()
            media = form.cleaned_data['media_download']
            start_date = form.cleaned_data['start_date_download']
            end_date = form.cleaned_data['end_date_download']
            download_file = download_report(connection_engine(), start_date, end_date)
            response = HttpResponse(download_file.to_csv(index=False), content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=report.csv'
            return response
