from Main.forms import MainForm
from django import forms  # type: ignore


class HeadingForm(MainForm):
    university = forms.IntegerField(
        help_text="Choose the University",
        label="University",
        required=True,
    )
    institute = forms.IntegerField(
        help_text="Choose the Institute",
        label="Institute",
        required=True,
    )

    branch = forms.IntegerField(
        label="Branch",
        help_text="Choose the Branch", 
        required=True
    )
