from Main.forms import MainForm
from django import forms # type: ignore

class LoginForm(MainForm):
    username = forms.CharField(
        max_length=100, 
        required=True,
        help_text='Enter the username', 
        label="Username"
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(),
        help_text='Enter the password',
        required=True, 
        label="Password"
    )
