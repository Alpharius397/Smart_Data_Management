from django.forms import Form
from django import forms

class ExcelForm(Form):
    username = forms.CharField(max_length=100, required=True,help_text='Enter the username')
    file = forms.FileField(required=True,help_text="Enter the Excel File",allow_empty_file=False)
    
    def clean_username(self):
        user = self.cleaned_data.get("username",None)
    
        if(user is None):
            raise forms.ValidationError(("Username cannot be empty"))
        
        return user
    

