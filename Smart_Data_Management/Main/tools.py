from django.forms import Form
from datetime import date,time

def get_var(form:Form, key:str) -> str | int | float | date | time | None:
    return form.cleaned_data.get(key,None)