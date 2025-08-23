from Main.forms import MainForm
from django import forms # type: ignore
from django.urls import reverse_lazy # type: ignore
from University.models import University
from User.models import RoleType

class RegisterForm(MainForm):
    username = forms.CharField(
        max_length=100, 
        required=True,
        help_text='Enter the username', label="Username"
    )
    
    email = forms.EmailField(
        max_length=255,
        required=True,
        help_text='Enter the email', label="Email"
    )
    
    level = forms.ChoiceField(
        help_text='Choose the role',
        required=True,
        choices=[(RoleType.MANAGER.value,RoleType.MANAGER.value),(RoleType.ADMIN.value,RoleType.ADMIN.value)], label="Level"
    )
    
    university = forms.ModelChoiceField(
        help_text='Choose the University',
        required=True,
        queryset=University.objects.all(),
        widget=forms.Select(attrs={
                'hx-get':reverse_lazy("Register:htmxInstitute"),
                'hx-target':'#id_institute',
                'hx-swap':'innerHTML',
                'hx-trigger':'load,click'
                })
        , label="University"
        )
    
    institute = forms.CharField(
        help_text='Choose the Institute',
        required=True,
        widget=forms.Select(attrs={
                'hx-get':reverse_lazy("Register:htmxBranch"),
                'hx-target':'#id_branch',
                'hx-swap':'innerHTML',
                'hx-trigger':'load,click'})
        , label="Institute"
        
    )
    
    branch = forms.CharField(
        help_text='Choose the Branch',
        required=True,
        widget=forms.Select()
        , label="Branch"
        
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(),
        help_text='Enter the password',
        required=True
        , label="Password"
        
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(),
        help_text='Re-enter the password',
        required=True
        , label="Confirm Password"
        
    )
    
    def clean_confirm_password(self):
        password_1 = self.cleaned_data.get("password",None)
        password_2 = self.cleaned_data.get("confirm_password",None)
        
        if((password_2 is None)):
            raise forms.ValidationError(("Password cannot be empty"))
        
        if(password_1!=password_2):
            raise forms.ValidationError(("Password cannot be different"))
            
        return password_2