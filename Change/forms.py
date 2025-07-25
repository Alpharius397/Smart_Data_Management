from Main.forms import MainForm
from django import forms # type: ignore
from django.core.validators import RegexValidator, validate_email # type: ignore

OTP_VALID = RegexValidator(r'^[0-9]{6}$')

class ForgotEmail(MainForm):
    Email = forms.CharField(
        max_length=100, 
        required=True,
        help_text='Enter the email', 
        validators=[validate_email],
        label="Email"
    )

class UsernameChange(MainForm):
    OTP = forms.CharField(
        min_length=6,
        max_length=6,
        validators=[OTP_VALID],
        required=True,
        help_text='Enter the OTP', 
        label="OTP"
    )
    
    Username = forms.CharField(
        max_length=100, 
        required=True,
        help_text='Enter the new username', 
        label="Username"
    )

class EmailChange(MainForm):
    OTP = forms.CharField(
        min_length=6,
        max_length=6,
        validators=[validate_email],
        required=True,
        help_text='Enter the OTP', 
        label="OTP"
    )
    
    Email = forms.CharField(
        max_length=100, 
        required=True,
        help_text='Enter the new email', 
        validators=[validate_email],
        label="Email"
    )
    
        
class PasswordChange(MainForm):
    OTP = forms.CharField(
        min_length=6,
        max_length=6,
        validators=[OTP_VALID],
        required=True,
        help_text='Enter the OTP', 
        label="OTP"
    )
    
    Password = forms.CharField(
        widget=forms.PasswordInput(),
        min_length=10,
        max_length=100, 
        required=True,
        help_text='Enter the password', 
        label="Password"
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(),
        min_length=10,
        max_length=100, 
        required=True,
        help_text='Re-enter the password', 
        label="Confirm password"
    )
    
    def clean_Password(self):
        data = self.cleaned_data
        
        val_1 = data.get("Password", None)
        val_2 = data.get("confirm_password", None)

        if(not (val_1 or val_2)):
            raise forms.ValidationError("Both cannot be empty")
        
        if( val_1 != val_2):
            raise forms.ValidationError("Both cannot be different")