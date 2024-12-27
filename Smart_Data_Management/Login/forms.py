from django.forms import Form
from django import forms

class LoginForm(Form):
    username = forms.CharField(max_length=100, required=True,help_text='Enter the username')
    level = forms.ChoiceField(help_text='Enter the role',required=True,choices=[('Uploader','Uploader'),('Manager','Manager')])
    password = forms.CharField(widget=forms.PasswordInput(),help_text='Enter the password',required=True)
    
    def clean_level(self):
        level = self.cleaned_data.get("level",None)
        
        if(level is None):
            raise forms.ValidationError(("Level cannot be empty"))
        
        if(level not in ['Manager','Uploader']):
            raise forms.ValidationError(("Unknown level detected"))
            
        return level