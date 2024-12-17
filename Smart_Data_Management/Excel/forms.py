from django.forms import Form
from django import forms

class ExcelForm(Form):
    username = forms.CharField(max_length=100, required=True,help_text='Enter the username',widget = forms.TextInput(attrs={'readonly':'readonly'}))
    file_name = forms.CharField(max_length=100,help_text='Enter the file name')
    file = forms.FileField(help_text="Enter the Excel File")
    
    def clean_username(self):
        user = self.cleaned_data.get("username",None)
    
        if(user is None):
            raise forms.ValidationError(("Username cannot be empty"))
        
        return user
    
    def clean_file_name(self):
        file = self.cleaned_data.get("file_name",None)
        if(file is None):
            raise forms.ValidationError(("Filename cannot be empty"))
        
        return file
    
    def clean_file(self):
        file = self.cleaned_data.get("file",None)
        if(file is None):
            raise forms.ValidationError(("File cannot be empty"))
        
        return file
    
class SearchQuery(Form):
    
    def __init__(self):
        super().__init__()
        
    # def add_field(self, name, type) -> None:
        
        
    def get_field_type(self, type):
        
        match(type):
            case 'char': return forms.CharField()
            case 'int': return forms.IntegerField()
            case 'date': return forms.CharField()
    
    
        

