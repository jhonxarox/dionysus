from django.http import HttpResponse
from django.shortcuts import render
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from .function import *
from .models import *
from .forms import *


def index(request):
    if request.method == 'POST':
        form = CheckingFraudForm(request.POST)
        if form.is_valid():
            status = True
            media_sources = form.cleaned_data['media_sources']
            # fraud_data = media_source[(
            #         media_source['CTIT Status'] |
            #         media_source['App Version Status'] |
            #         media_source['Device Status'])]

            # start_date = form.cleaned_data['start_date']
            # end_date = form.cleaned_data['end_date']

            data = Install.objects.filter(media_source=media_sources)
            fraud_data = data[(data['CTIT Status'] |
                               data['App Version Status'] |
                               data['Device Status'])]
            bad_percentage = ((len(data.index) - len(fraud_data.index)) / len(data.index)) * 100
            good_percentage = 100 - bad_percentage
            return render(request, 'index.html', {'status': status,
                                                  'good_percentage': good_percentage,
                                                  'bad_percentage': bad_percentage})
        else:
            status = True
            media_source = take_media_source(connection_engine())
            return render(request, 'index.html', {'form': form,
                                                  'media_source': media_source,
                                                  'status': status})
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


def upload(request):
    if "GET" == request.method:
        status = False
        return render(request, 'upload.html', {'status': status})

    csv_file = request.FILES['csv_file']

    if not (csv_file.name.endswith('.csv')):
        return render(request, 'upload.html', {'message': "Please Upload CSV file!"})

    con_engine = connection_engine()
    raw_data = read_csv(csv_file)
    ctit_result = ctit_check(raw_data)
    device_result = device_check(ctit_result, con_engine)
    data = app_version_check(device_result, con_engine)
    fraud_data = fraud_check(data)
    insert_data_to_db(data, con_engine)
    insert_fraud_to_db(fraud_data, con_engine)
    status = True
    return render(request, 'upload.html', {'status': status, 'message': "Upload Success"})


def page_lockscreen(request):
    return render(request, 'pages.html', {})


def alldata(request):
    data = Install.objects.all()
    paginator = Paginator(data, 100)
    page = request.GET.get('page')
    contacts = paginator.get_page(page)
    # head = pd.DataFrame(list(output.values()))
    # body = pd.DataFrame(list())
    return render(request, 'alldata.html', {'data': contacts})
