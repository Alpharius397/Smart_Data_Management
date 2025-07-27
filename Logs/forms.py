from django.forms import Form
from django import forms

from Main.forms import MainForm

class DateForm(MainForm):
    query = forms.ChoiceField(choices=[("","----------"),("after","After"),("before","Before"),("on","On")],widget=forms.Select(),required=False)
    date = forms.DateField(widget=forms.DateInput(attrs={"type":"date"}),required=False,)