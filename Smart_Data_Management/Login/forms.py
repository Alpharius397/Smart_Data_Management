from django.forms import Form
from django import forms

class LoginForm(Form):
    username = forms.CharField(max_length=100, required=True,help_text='Enter the username')
    password = forms.CharField(widget=forms.PasswordInput(),help_text='Enter the password',required=True)
