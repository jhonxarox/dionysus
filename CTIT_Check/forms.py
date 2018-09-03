from django import forms
from .function import *


class CheckingFraudForm(forms.Form):
    options = take_media_source(connection_engine())
    option = ()
    for data in options:
        option = option + ((data, data),)
    media_sources = forms.MultipleChoiceField(choices=option, widget=forms.SelectMultiple)
    start_date = forms.DateTimeField()
    end_date = forms.DateTimeField()


class uploadOrderplace(forms.Form):
    download = forms.BooleanField(required=False)


class download(forms.Form):
    media_download = forms.Field(widget=forms.HiddenInput())
    start_date_download = forms.CharField(widget=forms.HiddenInput())
    end_date_download = forms.CharField(widget=forms.HiddenInput())


class updateConfig(forms.Form):
    ctit = forms.DecimalField()
    ctit_status = forms.BooleanField(required=False)

    device = forms.DecimalField()
    device_status = forms.BooleanField(required=False)
    device_number = forms.DecimalField()

    app = forms.DecimalField()
    app_status = forms.BooleanField(required=False)


class addAppVersion(forms.Form):
    options = take_app_platform(connection_engine())
    option = ()
    for data in options:
        option = option + ((data, data),)
    app_platform = forms.ChoiceField(choices=option)
    app_version = forms.CharField()
    release_date = forms.DateTimeField()