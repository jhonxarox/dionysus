from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    return render(request, 'index.html', {})

def elements(request):
    return render(request, 'elements.html', {})

def upload(request):
    return render(request, 'upload.html', {})