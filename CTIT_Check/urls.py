from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('index/', views.index, name='index'),
    path('upload-install/', views.upload_install, name='upload_install'),
    path('upload-orderplace/', views.upload_orderplace, name='upload_orderplace'),
    path('upload-validation/', views.upload_bi_validation, name='upload_bi_validation'),
    path('alldata/', views.alldata, name='alldata'),
    path('download_all/', views.download_file_all, name='download'),
    path('config/', views.config, name='config'),
    path('add-update/', views.app_update, name='app_update')
]