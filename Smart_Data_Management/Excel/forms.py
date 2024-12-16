from django.forms import Form
from django import forms

class RegisterForm(Form):
    username = forms.CharField(max_length=100, required=True,help_text='Enter the username')
    email = forms.EmailField(max_length=255,required=True,help_text='Enter the email')
    password = forms.CharField(widget=forms.PasswordInput(),help_text='Enter the password')
    confirm_password = forms.CharField(widget=forms.PasswordInput(),help_text='Re-enter the password')
    
    def clean_password(self):
        password_1 = self.cleaned_data.get("password",None)
        
        if((password_1 is None)):
            raise forms.ValidationError(("Password cannot be empty"))
        
        return password_1
    
    
    def clean_confirm_password(self):
        password_1 = self.cleaned_data.get("password",None)
        password_2 = self.cleaned_data.get("confirm_password",None)
        
        if((password_2 is None)):
            raise forms.ValidationError(("Password cannot be empty"))
        
        if(password_1!=password_2):
            raise forms.ValidationError(("Password cannot be different"))
            
        return password_2
    
    def clean_email(self):
        email = self.cleaned_data.get("email",None)
        
        if(email is None):
            raise forms.ValidationError(("Email cannot be empty"))
        
        return email
        
    def clean_username(self):
        username = self.cleaned_data.get("username",None)
        
        if(username is None):
            raise forms.ValidationError(("Username cannot be empty"))
        
        return username