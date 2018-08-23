import csv

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
                # fraud_data = media_source[(
                #         media_source['CTIT Status'] |
                #         media_source['App Version Status'] |
                #         media_source['Device Status'])]
                start_date = form.cleaned_data['start_date']
                end_date = form.cleaned_data['end_date']

                all_data = take_all_install_data_base_on_date(connection_engine(), start_date, end_date)
                # data = Install.objects.filter(media_source=media_sources)
                # fraud_data = data[(data['CTIT Status'] | data['App Version Status'] | data['Device Status'])]
                # bad_percentage = ((len(data.index) - len(fraud_data.index)) / ((len(data.index)) * 100))
                # good_percentage = 100 - bad_percentage
                return render(request, 'index.html', {'status': status,
                                                      # 'good_percentage': good_percentage,
                                                      # 'bad_percentage': bad_percentage,
                                                      'start_date': start_date,
                                                      'end_date': end_date,
                                                      'all_data': all_data,
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
    respone = HttpResponse(download_file.to_csv(index=False), content_type='text/csv')
    respone['Content-Disposition'] = 'attachment; filename=checkout_id_%s.csv' % csv_file
    status = True

    if download:
        return respone
    else:
        return render(request, 'upload-orderplace.html',
                      {'status': status, 'message': "Upload Success", 'respone': respone})


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
