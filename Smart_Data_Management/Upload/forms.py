from django.forms import Form
from django import forms

class ExcelForm(Form):
    username = forms.CharField(max_length=100, required=True,help_text='Enter the username',widget = forms.TextInput(attrs={'readonly':'readonly'}))
    file_name = forms.CharField(max_length=100,help_text='Enter the file name',required=True)
    file = forms.FileField(help_text="Enter the Excel File",required=True)
