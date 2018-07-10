from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name = 'index'),
    path('index.html', views.index, name = 'index'),
    path('elements.html', views.elements, name = 'elements'),
    path('upload.html', views.upload, name = 'upload'),
]