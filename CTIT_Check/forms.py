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
    ctit = forms.NumberInput()
    device = forms.NumberInput()
    app = forms.NumberInput()


# class addAppVersion(forms.Form):
#     options =