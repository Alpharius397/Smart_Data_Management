from django.forms import Form # type: ignore
from django import forms # type: ignore


class FeedBackForm(Form):
    status = forms.ChoiceField(
        required=False,
        help_text="Set the status of row",
        choices=[("true",'Verified'),("false",'Rejected'),("none",'Unchecked')],
        label="Row Status",
    )
    
    feedBack = forms.CharField(
        max_length=255,
        help_text='Any additional feedback (Optional)',
        widget=forms.Textarea,
        required=False,
        label="Row Feedback"    
    )
    
    locked = forms.ChoiceField(
        required=False,
        help_text="Set the Lock status of row",
        choices=[("true",'Lock'),("false",'Unlock')],
        label="Row Lock Status"    
    )

    issued = forms.ChoiceField(
        required=False,
        help_text="Set the issue status of row",
        choices=[("true",'Issued'),("false",'Cancel Issue')],
        label="Row Issue Status"    
    )
    
class FeedBackView(Form):
    status = forms.ChoiceField(
        required=False,
        help_text="Set the status of row",
        choices=[("true",'Verified'),("false",'Rejected'),("none",'Unchecked')],
        label="Row Status",
        widget=forms.Select(attrs={"readonly": "readonly", "disabled":"true"})
    )
    
    feedBack = forms.CharField(
        max_length=255,
        help_text='Any additional feedback (Optional)',
        widget=forms.Textarea(attrs={"readonly": "readonly", "disabled":"true"}),
        required=False,
        label="Row Feedback"    
    )
    
    locked = forms.ChoiceField(
        required=False,
        help_text="Set the Lock status of row",
        choices=[("true",'Lock'),("false",'Unlock')],
        label="Row Lock Status",
        widget=forms.Select(attrs={"readonly": "readonly", "disabled":"true"})
    )

    issued = forms.ChoiceField(
        required=False,
        help_text="Set the issue status of row",
        choices=[("true",'Issued'),("false",'Cancel Issue')],
        label="Row Issue Status",
        widget=forms.Select(attrs={"readonly": "readonly", "disabled":"true"})
    )