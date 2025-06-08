from django.forms import Form # type: ignore
from django import forms # type: ignore

class TaskCreateForm(Form):
    
    username = forms.CharField(
        max_length=100,
        required=True,
        help_text="Enter the username",
        widget=forms.TextInput(attrs={"readonly": "readonly"}),
        label="User"
    )
    
    fileName = forms.CharField(
        max_length=100,
        help_text="Enter the file name",
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Enter the Task name", "title": "Enter the name of the task"}),
        label="Task Name"
    )
    
    semesterLimit = forms.IntegerField(
        max_value=100,
        min_value=1,
        required=True,
        widget=forms.NumberInput(attrs={"title": "Enter the max number of semesters under this task", "placeholder": "No. of semesters"}),
        label="Semester Count"
    )

class TaskUpdateForm(Form):
    
    taskID = forms.CharField(
        max_length=100,
        required=True,
        help_text="Task ID",
        widget=forms.TextInput(attrs={"readonly": "readonly"},),
        label="Task ID"
    )
    
    fileName = forms.CharField(
        max_length=100,
        help_text="Enter the file name",
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Enter the Task name", "title": "Enter the name of the task"}),
        label="Task Name"
    )
    
    semesterLimit = forms.IntegerField(
        max_value=100,
        min_value=1,
        required=True,
        widget=forms.NumberInput(attrs={"title": "Enter the max number of semesters under this task", "placeholder": "No. of semesters"}),
        label="Semester Count"
    )
    
class TaskDeleteForm(Form):
    
    taskID = forms.CharField(
        max_length=100,
        required=True,
        help_text="Task ID",
        widget=forms.TextInput(attrs={"readonly": "readonly"},),
        label="Task ID"
    )
    fileName = forms.CharField(
        max_length=100,
        help_text="Enter the file name",
        required=True,
        widget=forms.TextInput(attrs={"readonly": "readonly"}),
        label="Task Name"
    )
    
    semesterLimit = forms.IntegerField(
        max_value=100,
        min_value=1,
        required=True,
        widget=forms.NumberInput(attrs={"title": "Enter the max number of semesters under this task","readonly": "readonly"}),
        label="Semester Count"
    )
    
class SemesterCreateForm(Form):
    taskID = forms.CharField(
        max_length=100,
        required=True,
        help_text="Task ID",
        widget=forms.TextInput(attrs={"readonly": "readonly"},),
        label="Task ID"
    )
    
    semester = forms.ChoiceField(required=True, label="Semester")
    
    file = forms.FileField(
        required=True, 
        allow_empty_file=False, 
        widget=forms.FileInput(attrs={"title": "Upload an excel file"}),
        label="Upload File"
    )
    
    def setChoice(self, choices: list[tuple[str, str]]):
        self.fields["semester"].choices = choices
        
class SemesterEditForm(Form):
    taskID = forms.CharField(
        max_length=100,
        required=True,
        help_text="Task ID",
        widget=forms.TextInput(attrs={"readonly": "readonly"},),
        label="Task ID"
    )
    
    semester = forms.IntegerField(        
        required=True,
        help_text="Semester",
        widget=forms.TextInput(attrs={"readonly": "readonly"},),
        label="Semester"
    )
    
    file = forms.FileField(
        required=True, 
        allow_empty_file=False, 
        widget=forms.FileInput(attrs={"title": "Upload an excel file"}),
        label="Upload File"
    )
