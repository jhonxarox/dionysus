from django import forms


class CheckingFraudForm(forms.Form):
    media_sources = forms.SelectMultiple()
    start_date = forms.DateInput()
    end_date = forms.DateInput()
