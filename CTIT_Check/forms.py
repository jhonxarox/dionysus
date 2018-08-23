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