from django.forms import Form
from django import forms

class RegisterForm(Form):
    username = forms.CharField(max_length=100, required=True,help_text='Enter the username')
    level = forms.ChoiceField(help_text='Enter the role',required=True,choices=[('Uploader','Uploader'),('Manager','Manager')])
    email = forms.EmailField(max_length=255,required=True,help_text='Enter the email')
    password = forms.CharField(widget=forms.PasswordInput(),help_text='Enter the password')
    confirm_password = forms.CharField(widget=forms.PasswordInput(),help_text='Re-enter the password')
    
    def clean_confirm_password(self):
        password_1 = self.cleaned_data.get("password",None)
        password_2 = self.cleaned_data.get("confirm_password",None)
        
        if((password_2 is None)):
            raise forms.ValidationError(("Password cannot be empty"))
        
        if(password_1!=password_2):
            raise forms.ValidationError(("Password cannot be different"))
            
        return password_2
    
    def clean_level(self):
        level = self.cleaned_data.get("level",None)
        
        if(level is None):
            raise forms.ValidationError(("Level cannot be empty"))
        
        if(level not in ['Manager','Uploader']):
            raise forms.ValidationError(("Unknown level detected"))
        
        return level