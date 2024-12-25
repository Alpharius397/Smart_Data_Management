from django.forms import Form
from django import forms

class ExcelForm(Form):
    username = forms.CharField(max_length=100, required=True,help_text='Enter the username',widget = forms.TextInput(attrs={'readonly':'readonly'}))
    file_name = forms.CharField(max_length=100,help_text='Enter the file name',required=True)
    file = forms.FileField(help_text="Enter the Excel File",required=True)

class VerifyForm(Form):
    status = forms.ChoiceField(required=True,help_text="Set the status of excel",choices=[(True,'Verified'),(False,'Rejected'),(None,'Unchecked')])
    feedback = forms.CharField(max_length=255,help_text='Any additional feedback (Optional)',widget=forms.Textarea,required=False)

