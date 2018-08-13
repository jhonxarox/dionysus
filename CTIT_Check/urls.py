from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('index/', views.index, name='index'),
    path('elements/', views.elements, name='elements'),
    # path('charts/', views.upload, name='charts'),
    # path('panels/', views.upload, name='panels'),
    path('upload-install/', views.upload_install, name='upload_install'),
    path('upload-orderplace/', views.upload_orderplace, name='upload_orderplace'),
    path('upload-validation/', views.upload_bi_validation, name='upload_bi_validation'),
    # path('pages/', views.upload, name='pages'),
    # path('page-lockscreen/', views.upload, name='page-lockscreen'),
    # path('page-login/', views.upload, name='page-login'),
    # path('table/', views.upload, name='table'),
    # path('typography/', views.upload, name='typography'),
    # path('icons/', views.upload, name='icons'),
    path('alldata/', views.alldata, name='alldata'),
]