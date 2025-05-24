from django.forms import Form, CharField, Widget, ModelForm
from .models import ColorRegex

class ColorPick(Widget):
    input_type = "color"
    template_name = "django/forms/widgets/input.html"
    
    def __init__(self, attrs=None):
        if attrs is not None:
            attrs = attrs.copy()
            self.input_type = attrs.pop("type", self.input_type)
        super().__init__(attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["type"] = self.input_type
        return context

class ColorPickerForm(ModelForm):
    main_color = CharField(validators=[ColorRegex], max_length=7,min_length=7,widget=ColorPick())
    sec_color = CharField(validators=[ColorRegex], max_length=7,min_length=7,widget=ColorPick())