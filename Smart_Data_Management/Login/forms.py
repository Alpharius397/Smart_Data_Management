from django.forms import Form
from django import forms

class LoginForm(Form):
    username = forms.CharField(max_length=100, required=True,help_text='Enter the username')
    password = forms.CharField(widget=forms.PasswordInput(),help_text='Enter the password')
    
    def clean_password(self):
        password = self.cleaned_data.get("password",None)
        
        if(password is None):
            raise forms.ValidationError(("Password cannot be empty"))
        
        return password
        
    def clean_username(self):
        username = self.cleaned_data.get("username",None)
        
        if(username is None):
            raise forms.ValidationError(("Username cannot be empty"))
        
        return username