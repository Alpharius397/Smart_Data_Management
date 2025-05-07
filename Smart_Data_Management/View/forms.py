from django.forms import Form
from django import forms

class VerifyForm(Form):
    status = forms.ChoiceField(required=False,help_text="Set the status of excel",choices=[(True,'Verified'),(False,'Rejected'),(None,'Unchecked')])
    feed = forms.CharField(max_length=255,help_text='Any additional feedback (Optional)',widget=forms.Textarea,required=False)

