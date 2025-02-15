from django.forms import Form
from django import forms

class DateForm(Form):
    query = forms.ChoiceField(choices=[("","----------"),("after","After"),("before","Before"),("on","On")],widget=forms.Select(),required=False)
    date = forms.DateField(widget=forms.DateInput(attrs={"type":"date"}),required=False,)
    

class LogQuery(Form):
    query = forms.ChoiceField(choices=[("","----------"),("fileName","File Name"),("index","Index"),("type","Type"),("username","Username"),("authLevel","Auth Level"),("timestamp","Time")],widget=forms.Select(),required=False)
    search = forms.CharField(max_length=225,required=False)
